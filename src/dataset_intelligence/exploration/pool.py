"""Under-exposed candidate exploration pool builder and hidden-gem predicate for M6."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from .family import detect_family_redundancy
from .popularity import DatasetPopularityProfile

DEFAULT_EXPLORATION_CONFIG = {
    "min_exploration_utility": 0.50,
    "min_hidden_gem_utility": 0.70,
    "min_access_score": 0.80,
    "min_quality_score": 0.70,
    "max_exploration_additions": 5,
    "retrieval_top_k": 3,
}


def check_hidden_gem(
    profile: DatasetPopularityProfile,
    utility_estimate: Any,
    is_family_variant: bool = False,
    config: dict[str, Any] | None = None,
) -> tuple[bool, str, str]:
    """Evaluate hidden-gem predicate and under-observed high-utility designation.

    Returns:
        (is_hidden_gem, designation, explanation)
    """
    cfg = config or DEFAULT_EXPLORATION_CONFIG
    min_gem_u = cfg.get("min_hidden_gem_utility", 0.70)
    min_acc = cfg.get("min_access_score", 0.80)
    min_qual = cfg.get("min_quality_score", 0.70)

    u_score = getattr(utility_estimate, "composite_utility", 0.0)
    hard_gated = getattr(utility_estimate, "hard_gated", False)
    components = getattr(utility_estimate, "components", {})

    acc_comp = components.get("access_feasibility")
    acc_score = getattr(acc_comp, "score", 0.0) if acc_comp else 0.0
    qual_comp = components.get("quality_compatibility")
    qual_score = getattr(qual_comp, "score", 0.0) if qual_comp else 0.0

    if hard_gated:
        return False, "hard_gated", "Candidate violates hard task constraints."

    # Check Under-Observed High-Utility Candidate
    if profile.popularity_measurement_state == "under_observed":
        if u_score >= min_gem_u and acc_score >= min_acc:
            return (
                False,
                "under_observed_high_utility",
                f"Candidate has high task utility ({u_score:.3f}) and usable access, but community popularity was not measured; cannot be designated a hidden gem without popularity verification.",
            )
        else:
            return (
                False,
                "under_observed_standard",
                f"Popularity unmeasured; task utility ({u_score:.3f}) below high-utility threshold ({min_gem_u}).",
            )

    # Check Measured Hidden Gem
    if profile.popularity_stratum not in {"low", "very_low"}:
        return (
            False,
            "not_low_popularity",
            f"Candidate belongs to {profile.popularity_stratum} popularity stratum; not eligible for hidden gem.",
        )

    if is_family_variant:
        return (
            False,
            "redundant_family_variant",
            "Candidate is a family variant/mirror of a dataset already present in the main retrieval pool.",
        )

    if u_score < min_gem_u:
        return (
            False,
            "insufficient_utility",
            f"Candidate utility ({u_score:.3f}) is below hidden-gem threshold ({min_gem_u}).",
        )

    if acc_score < min_acc:
        return (
            False,
            "insufficient_access",
            f"Operational access score ({acc_score:.2f}) below threshold ({min_acc}).",
        )

    # If M4 quality is present and evaluated (score > 0.5 default), check quality
    if qual_comp and getattr(qual_comp, "epistemic_state", "") in {"known_favorable", "known_unfavorable"}:
        if qual_score < min_qual:
            return (
                False,
                "insufficient_quality",
                f"Quality score ({qual_score:.2f}) below threshold ({min_qual}).",
            )

    return (
        True,
        "hidden_gem",
        f"Verified hidden gem: measured {profile.popularity_stratum} popularity, high task utility ({u_score:.3f}), verified access ({acc_score:.2f}), and non-redundant lineage.",
    )


def check_exploration_eligibility(
    profile: DatasetPopularityProfile,
    utility_estimate: Any,
    is_under_exposed: bool,
    config: dict[str, Any] | None = None,
) -> tuple[bool, str, str]:
    """Evaluate whether an under-exposed candidate is eligible for long-tail exploration."""
    cfg = config or DEFAULT_EXPLORATION_CONFIG
    min_exp_u = cfg.get("min_exploration_utility", 0.50)

    if not is_under_exposed:
        return False, "already_exposed", "Candidate is already exposed in main retrieval top-k."

    hard_gated = getattr(utility_estimate, "hard_gated", False)
    if hard_gated:
        return False, "hard_gated", "Candidate violates hard task constraints."

    u_score = getattr(utility_estimate, "composite_utility", 0.0)
    if u_score < min_exp_u:
        return False, "insufficient_utility", f"Utility ({u_score:.3f}) below exploration threshold ({min_exp_u})."

    components = getattr(utility_estimate, "components", {})
    acc_comp = components.get("access_feasibility")
    if acc_comp and getattr(acc_comp, "epistemic_state", "") == "failed":
        return False, "operational_failure", "Operational access failed (e.g. HTTP 502)."

    # Check popularity state
    if profile.popularity_measurement_state == "under_observed":
        return (
            True,
            "under_observed_exploration",
            f"Eligible for under-observed exploration: utility {u_score:.3f}, access usable, popularity unmeasured.",
        )

    if profile.popularity_stratum in {"medium", "low", "very_low"}:
        return (
            True,
            "long_tail_exploration",
            f"Eligible for long-tail exploration: measured {profile.popularity_stratum} popularity, utility {u_score:.3f}.",
        )

    return False, "high_popularity_under_exposed", f"Candidate has {profile.popularity_stratum} popularity; not a long-tail candidate."


@dataclass(frozen=True)
class ExplorationCandidateSet:
    """Exploration audit and candidate set output for a specific task and query."""

    set_id: str
    task_id: str
    query_id: str
    main_pool_dataset_ids: tuple[str, ...]
    under_exposed_dataset_ids: tuple[str, ...]
    eligible_exploration_dataset_ids: tuple[str, ...]
    selected_exploration_dataset_ids: tuple[str, ...]
    hidden_gem_dataset_ids: tuple[str, ...]
    under_observed_high_utility_dataset_ids: tuple[str, ...]
    redundant_family_variants: dict[str, str]
    provenance: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExplorationPoolBuilder:
    """Constructs bounded exploration candidate sets from M2 retrieval, M5 utility, and popularity profiles."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or dict(DEFAULT_EXPLORATION_CONFIG)

    def build_exploration_set(
        self,
        task_id: str,
        query_id: str,
        retrieved_dataset_ids: list[str],
        corpus_records: list[Any],
        popularity_profiles: dict[str, DatasetPopularityProfile],
        utility_estimates: dict[str, Any],
    ) -> ExplorationCandidateSet:
        top_k = self.config.get("retrieval_top_k", 3)
        max_add = self.config.get("max_exploration_additions", 5)

        main_pool_ids = tuple(retrieved_dataset_ids[:top_k])
        records_by_id = {
            r.internal_id if hasattr(r, "internal_id") else "": r
            for r in corpus_records
        }
        main_records = [records_by_id[did] for did in main_pool_ids if did in records_by_id]

        under_exposed_ids: list[str] = []
        eligible_ids: list[str] = []
        hidden_gems: list[str] = []
        under_obs_high_u: list[str] = []
        redundant_variants: dict[str, str] = {}

        # Evaluate all corpus candidates not in main pool
        for rec in corpus_records:
            did = rec.internal_id if hasattr(rec, "internal_id") else ""
            if did in main_pool_ids:
                continue

            u_est = utility_estimates.get(did)
            prof = popularity_profiles.get(did)
            if not u_est or not prof:
                continue

            is_under_exp = getattr(u_est, "composite_utility", 0.0) > 0.0 and not getattr(u_est, "hard_gated", False)
            if is_under_exp:
                under_exposed_ids.append(did)

            # Check family redundancy against main pool
            is_redundant, red_reason, red_match_id = detect_family_redundancy(rec, main_records)
            if is_redundant and red_reason:
                redundant_variants[did] = red_reason

            # Check exploration eligibility
            is_elig, elig_cat, _ = check_exploration_eligibility(prof, u_est, is_under_exposed=True, config=self.config)
            if is_elig:
                eligible_ids.append(did)

            # Check hidden gem predicate
            is_gem, designation, _ = check_hidden_gem(prof, u_est, is_family_variant=is_redundant, config=self.config)
            if is_gem:
                hidden_gems.append(did)
            elif designation == "under_observed_high_utility":
                under_obs_high_u.append(did)

        # Select top exploration additions (prioritize non-redundant, highest utility)
        candidate_tuples: list[tuple[str, float, bool]] = []
        for did in eligible_ids:
            u_score = getattr(utility_estimates[did], "composite_utility", 0.0)
            is_red = did in redundant_variants
            candidate_tuples.append((did, u_score, is_red))

        # Sort: non-redundant first, then by utility descending, then by did ascending
        candidate_tuples.sort(key=lambda x: (not x[2], x[1], x[0]), reverse=True)
        selected_additions = tuple(t[0] for t in candidate_tuples[:max_add])

        payload = {
            "task_id": task_id,
            "query_id": query_id,
            "main_pool_dataset_ids": main_pool_ids,
            "selected_exploration_dataset_ids": selected_additions,
        }
        set_id = "exp_" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]

        provenance = {
            "retrieval_top_k": top_k,
            "max_exploration_additions": max_add,
            "min_exploration_utility": self.config.get("min_exploration_utility", 0.50),
            "min_hidden_gem_utility": self.config.get("min_hidden_gem_utility", 0.70),
        }

        return ExplorationCandidateSet(
            set_id=set_id,
            task_id=task_id,
            query_id=query_id,
            main_pool_dataset_ids=main_pool_ids,
            under_exposed_dataset_ids=tuple(under_exposed_ids),
            eligible_exploration_dataset_ids=tuple(eligible_ids),
            selected_exploration_dataset_ids=selected_additions,
            hidden_gem_dataset_ids=tuple(hidden_gems),
            under_observed_high_utility_dataset_ids=tuple(under_obs_high_u),
            redundant_family_variants=redundant_variants,
            provenance=provenance,
        )
