"""Guarded exposure audit metrics and exposure disparity calculation for M6."""

from __future__ import annotations

from typing import Any

from .popularity import POPULARITY_STRATA


def compute_stratum_exposure_share(strata_list: list[str], target_stratum: str) -> float:
    """Compute fraction of exposed items belonging to target_stratum."""
    if not strata_list:
        return 0.0
    count = sum(1 for s in strata_list if s == target_stratum)
    return round(count / len(strata_list), 4)


def compute_exposure_disparity_ratio(
    exposed_strata: list[str],
    corpus_strata: list[str],
    target_stratum: str,
) -> float | str:
    """Compute Exposure Disparity Ratio with guarded zero-denominator handling."""
    if not corpus_strata:
        return "not_estimable (zero corpus size)"
    corpus_count = sum(1 for s in corpus_strata if s == target_stratum)
    if corpus_count == 0:
        return "not_estimable (zero corpus share)"
    if not exposed_strata:
        return "not_estimable (zero exposed size)"

    corpus_share = corpus_count / len(corpus_strata)
    exposed_share = sum(1 for s in exposed_strata if s == target_stratum) / len(exposed_strata)
    return round(exposed_share / corpus_share, 4)


def compute_utility_weighted_exposure(
    exposed_items: list[tuple[str, float]],
    target_stratum: str,
) -> float | str:
    """Compute utility-weighted exposure share with guarded zero-utility handling."""
    total_u = sum(u for _, u in exposed_items)
    if total_u <= 0.0:
        return "not_estimable (zero exposed utility)"

    stratum_u = sum(u for s, u in exposed_items if s == target_stratum)
    return round(stratum_u / total_u, 4)


def compute_mean_utility_by_stratum(
    items: list[tuple[str, float]],
) -> dict[str, float | str]:
    """Compute mean task utility for each popularity stratum."""
    grouped: dict[str, list[float]] = {s: [] for s in sorted(POPULARITY_STRATA)}
    for s, u in items:
        if s in grouped:
            grouped[s].append(u)

    result: dict[str, float | str] = {}
    for s, vals in grouped.items():
        if not vals:
            result[s] = "not_estimable (no candidates in stratum)"
        else:
            result[s] = round(sum(vals) / len(vals), 4)
    return result


class ExposureAuditor:
    """Auditor analyzing popularity-stratum exposure in M2 retrieval against M5 utility."""

    def __init__(self, profiles: dict[str, Any]) -> None:
        self.profiles = profiles

    def audit_retrieval_run(
        self,
        query_id: str,
        retrieved_dataset_ids: list[str],
        corpus_dataset_ids: list[str],
        utility_estimates: dict[str, Any],
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Audit popularity exposure for a specific retrieval run."""
        exposed_ids = retrieved_dataset_ids[:top_k]
        exposed_strata = [
            self.profiles.get(did).popularity_stratum if did in self.profiles else "unknown"
            for did in exposed_ids
        ]
        corpus_strata = [
            self.profiles.get(did).popularity_stratum if did in self.profiles else "unknown"
            for did in corpus_dataset_ids
        ]

        exposed_items = [
            (
                self.profiles.get(did).popularity_stratum if did in self.profiles else "unknown",
                utility_estimates.get(did).composite_utility if did in utility_estimates else 0.0,
            )
            for did in exposed_ids
        ]

        corpus_items = [
            (
                self.profiles.get(did).popularity_stratum if did in self.profiles else "unknown",
                utility_estimates.get(did).composite_utility if did in utility_estimates else 0.0,
            )
            for did in corpus_dataset_ids
        ]

        stratum_exposure_shares: dict[str, float] = {}
        exposure_disparity_ratios: dict[str, float | str] = {}
        utility_weighted_shares: dict[str, float | str] = {}

        for s in sorted(POPULARITY_STRATA):
            stratum_exposure_shares[s] = compute_stratum_exposure_share(exposed_strata, s)
            exposure_disparity_ratios[s] = compute_exposure_disparity_ratio(exposed_strata, corpus_strata, s)
            utility_weighted_shares[s] = compute_utility_weighted_exposure(exposed_items, s)

        mean_utility_exposed = compute_mean_utility_by_stratum(exposed_items)
        mean_utility_corpus = compute_mean_utility_by_stratum(corpus_items)

        return {
            "query_id": query_id,
            "top_k": top_k,
            "exposed_datasets_count": len(exposed_ids),
            "corpus_datasets_count": len(corpus_dataset_ids),
            "stratum_exposure_share": stratum_exposure_shares,
            "exposure_disparity_ratio": exposure_disparity_ratios,
            "utility_weighted_exposure": utility_weighted_shares,
            "mean_utility_by_stratum_exposed": mean_utility_exposed,
            "mean_utility_by_stratum_corpus": mean_utility_corpus,
        }
