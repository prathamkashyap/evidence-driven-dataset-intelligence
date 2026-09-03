"""Popularity profiling and source-relative quantile stratification for M6."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

PROFILE_VERSION = "1.0"
MEASUREMENT_STATES = frozenset({"measured", "under_observed"})
POPULARITY_STRATA = frozenset({"very_high", "high", "medium", "low", "very_low", "unknown"})

DEFAULT_STRATA_CUTOFFS = {
    "very_high": 0.80,
    "high": 0.60,
    "medium": 0.40,
    "low": 0.20,
}


def compute_profile_id(
    profile_version: str,
    dataset_id: str,
    source_name: str,
    raw_signals: dict[str, Any],
    primary_metric_name: str | None,
    primary_metric_value: float | None,
    popularity_measurement_state: str,
    popularity_stratum: str,
) -> str:
    """Derive deterministic content-addressed identity from stable popularity fields."""
    payload = {
        "profile_version": profile_version,
        "dataset_id": dataset_id,
        "source_name": source_name,
        "raw_signals": raw_signals,
        "primary_metric_name": primary_metric_name,
        "primary_metric_value": primary_metric_value,
        "popularity_measurement_state": popularity_measurement_state,
        "popularity_stratum": popularity_stratum,
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "pop_" + hashlib.sha256(canonical_bytes).hexdigest()[:24]


@dataclass(frozen=True)
class DatasetPopularityProfile:
    """Source-aware popularity profile preserving raw metrics and normalized strata."""

    profile_id: str
    profile_version: str
    dataset_id: str
    source_name: str
    raw_signals: dict[str, Any]
    primary_metric_name: str | None
    primary_metric_value: float | None
    popularity_measurement_state: str
    source_relative_percentile: float | None
    popularity_stratum: str
    observed_at: str
    provenance: dict[str, Any]

    def validate(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id cannot be blank.")
        if self.profile_version != PROFILE_VERSION:
            raise ValueError(f"Unsupported profile version: {self.profile_version}")
        if self.popularity_measurement_state not in MEASUREMENT_STATES:
            raise ValueError(f"Invalid measurement state: {self.popularity_measurement_state}")
        if self.popularity_stratum not in POPULARITY_STRATA:
            raise ValueError(f"Invalid popularity stratum: {self.popularity_stratum}")
        if self.popularity_measurement_state == "under_observed" and self.popularity_stratum != "unknown":
            raise ValueError("under_observed popularity profile must have popularity_stratum=='unknown'")
        if self.popularity_measurement_state == "measured" and self.popularity_stratum == "unknown":
            raise ValueError("measured popularity profile cannot have popularity_stratum=='unknown'")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def extract_raw_popularity(record: Any) -> tuple[dict[str, Any], str | None, float | None, str]:
    """Extract raw community metrics and primary metric for a canonical dataset record."""
    source_name = record.identity.get("source_name", "unknown") if hasattr(record, "identity") else "unknown"
    community = record.community_context if hasattr(record, "community_context") else {}
    observed_at = "unknown"
    if hasattr(record, "provenance") and record.provenance:
        observed_at = record.provenance[0].get("observed_at", "unknown")

    raw_signals = dict(community) if isinstance(community, dict) else {}

    primary_name: str | None = None
    primary_val: float | None = None

    if source_name in {"huggingface", "kaggle"}:
        downloads = raw_signals.get("downloads")
        stars = raw_signals.get("stars")
        if downloads is not None and isinstance(downloads, (int, float)):
            primary_name = "downloads"
            primary_val = float(downloads)
        elif stars is not None and isinstance(stars, (int, float)):
            primary_name = "stars"
            primary_val = float(stars)

    state = "measured" if primary_val is not None else "under_observed"
    return raw_signals, primary_name, primary_val, state, observed_at


def build_popularity_profiles(
    records: list[Any],
    config: dict[str, Any] | None = None,
) -> dict[str, DatasetPopularityProfile]:
    """Build deterministic, source-relative popularity profiles across all input records."""
    cutoffs = (config or {}).get("strata_cutoffs", DEFAULT_STRATA_CUTOFFS)

    # 1. Group records by source and extract raw metrics
    records_by_source: dict[str, list[tuple[Any, dict[str, Any], str | None, float | None, str, str]]] = {}
    for rec in records:
        raw_sig, p_name, p_val, state, obs_at = extract_raw_popularity(rec)
        src = rec.identity.get("source_name", "unknown") if hasattr(rec, "identity") else "unknown"
        records_by_source.setdefault(src, []).append((rec, raw_sig, p_name, p_val, state, obs_at))

    profiles: dict[str, DatasetPopularityProfile] = {}

    for src, items in records_by_source.items():
        # Separate measured from under_observed
        measured_items = [it for it in items if it[4] == "measured" and it[3] is not None]
        under_obs_items = [it for it in items if it[4] == "under_observed"]

        # Sort measured items descending by primary_val, tie-breaking by internal_id
        measured_items.sort(
            key=lambda x: (
                x[3] if x[3] is not None else -1.0,
                x[0].internal_id if hasattr(x[0], "internal_id") else "",
            ),
            reverse=True,
        )

        n_measured = len(measured_items)

        for rank_idx, (rec, raw_sig, p_name, p_val, state, obs_at) in enumerate(measured_items):
            did = rec.internal_id if hasattr(rec, "internal_id") else ""
            if n_measured > 1:
                # Percentile rank: 1.0 for top dataset, 0.0 for lowest dataset
                percentile = round((n_measured - 1 - rank_idx) / (n_measured - 1), 4)
            else:
                percentile = 1.0

            # Determine stratum
            if percentile >= cutoffs.get("very_high", 0.80):
                stratum = "very_high"
            elif percentile >= cutoffs.get("high", 0.60):
                stratum = "high"
            elif percentile >= cutoffs.get("medium", 0.40):
                stratum = "medium"
            elif percentile >= cutoffs.get("low", 0.20):
                stratum = "low"
            else:
                stratum = "very_low"

            pid = compute_profile_id(
                profile_version=PROFILE_VERSION,
                dataset_id=did,
                source_name=src,
                raw_signals=raw_sig,
                primary_metric_name=p_name,
                primary_metric_value=p_val,
                popularity_measurement_state="measured",
                popularity_stratum=stratum,
            )

            provenance = {
                "normalization_method": "source_relative_quantile",
                "source_population_measured": n_measured,
                "source_total_records": len(items),
                "rank_within_source": rank_idx + 1,
            }

            profile = DatasetPopularityProfile(
                profile_id=pid,
                profile_version=PROFILE_VERSION,
                dataset_id=did,
                source_name=src,
                raw_signals=raw_sig,
                primary_metric_name=p_name,
                primary_metric_value=p_val,
                popularity_measurement_state="measured",
                source_relative_percentile=percentile,
                popularity_stratum=stratum,
                observed_at=obs_at,
                provenance=provenance,
            )
            profile.validate()
            profiles[did] = profile

        for rec, raw_sig, p_name, p_val, state, obs_at in under_obs_items:
            did = rec.internal_id if hasattr(rec, "internal_id") else ""
            pid = compute_profile_id(
                profile_version=PROFILE_VERSION,
                dataset_id=did,
                source_name=src,
                raw_signals=raw_sig,
                primary_metric_name=None,
                primary_metric_value=None,
                popularity_measurement_state="under_observed",
                popularity_stratum="unknown",
            )
            provenance = {
                "normalization_method": "under_observed_unnormalized",
                "source_population_measured": n_measured,
                "source_total_records": len(items),
                "reason": f"Source {src} does not provide native popularity counters in current corpus snapshot.",
            }
            profile = DatasetPopularityProfile(
                profile_id=pid,
                profile_version=PROFILE_VERSION,
                dataset_id=did,
                source_name=src,
                raw_signals=raw_sig,
                primary_metric_name=None,
                primary_metric_value=None,
                popularity_measurement_state="under_observed",
                source_relative_percentile=None,
                popularity_stratum="unknown",
                observed_at=obs_at,
                provenance=provenance,
            )
            profile.validate()
            profiles[did] = profile

    return profiles
