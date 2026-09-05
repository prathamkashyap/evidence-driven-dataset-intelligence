"""Deterministic post-selection recommendation role assignment for M7."""

from __future__ import annotations

from typing import Any

from dataset_intelligence.exploration.pool import check_hidden_gem
from .signals import CandidateSignals, compute_attribute_distance


def assign_recommendation_roles(
    selected_tuples: list[tuple[Any, float, float]],
    signals_by_id: dict[str, CandidateSignals],
    utility_estimates_by_id: dict[str, Any],
    popularity_profiles_by_id: dict[str, Any],
    fingerprints_by_id: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, str | None]:
    """Assign mutually exclusive recommendation roles to candidates in S*.

    Roles:
      - 'best_overall': Highest candidate intrinsic score in S*
      - 'best_quality': Highest M4 quality score (>= 0.70) without sample anomalies
      - 'best_efficient_option': Grounded access feasibility with lowest comparable operational overhead
      - 'hidden_gem': Inherits strict M6 measured hidden-gem predicate
      - 'best_alternative': Maximum attribute distance from best_overall (>= 0.30)

    Returns:
        Dict mapping dataset_id -> role_name (or None if unassigned)
    """
    assigned_roles: dict[str, str | None] = {}
    if not selected_tuples:
        return assigned_roles

    fp_dict = fingerprints_by_id or {}
    selected_records = [t[0] for t in selected_tuples]
    for rec in selected_records:
        did = getattr(rec, "internal_id", "")
        assigned_roles[did] = None

    # 1. Best Overall: Top candidate in S* (highest candidate score)
    best_overall_rec = selected_tuples[0][0]
    best_overall_id = getattr(best_overall_rec, "internal_id", "")
    assigned_roles[best_overall_id] = "best_overall"

    claimed_ids: set[str] = {best_overall_id}

    # 2. Hidden Gem: Must satisfy strict M6 hidden-gem predicate
    for rec in selected_records:
        did = getattr(rec, "internal_id", "")
        if did in claimed_ids:
            continue
        prof = popularity_profiles_by_id.get(did)
        u_est = utility_estimates_by_id.get(did)
        if prof and u_est:
            is_gem, _, _ = check_hidden_gem(prof, u_est, is_family_variant=False)
            if is_gem:
                assigned_roles[did] = "hidden_gem"
                claimed_ids.add(did)
                break

    # 3. Best Data-Quality Profile: Highest quality score >= 0.70 with clean sample diagnostics
    best_qual_rec: Any = None
    best_qual_score: float = -1.0

    for rec in selected_records:
        did = getattr(rec, "internal_id", "")
        if did in claimed_ids:
            continue
        fp = fp_dict.get(did)
        u_est = utility_estimates_by_id.get(did)
        qual_comp = getattr(u_est, "components", {}).get("quality_compatibility") if u_est else None
        q_score = getattr(qual_comp, "score", 0.0) if qual_comp else 0.0

        if q_score >= 0.70:
            missing_ratio = 0.0
            if fp:
                scope = getattr(fp, "sample_scope", {})
                if isinstance(scope, dict):
                    missing_ratio = scope.get("missing_cell_ratio", 0.0) or 0.0
            adjusted_q = q_score * (1.0 - missing_ratio)
            if adjusted_q > best_qual_score:
                best_qual_score = adjusted_q
                best_qual_rec = rec

    if best_qual_rec is not None:
        best_qual_id = getattr(best_qual_rec, "internal_id", "")
        assigned_roles[best_qual_id] = "best_quality"
        claimed_ids.add(best_qual_id)

    # 4. Best Efficient Option: Grounded access criteria + lowest comparable operational overhead
    # Contract: "Among eligible candidates, select the candidate with the lowest measured
    # operational overhead using only operational measurements that are actually present
    # and comparable across the candidates being compared."
    eligible_efficient: list[tuple[Any, float | None, float]] = []  # (rec, duration_ms, utility)

    for rec in selected_records:
        did = getattr(rec, "internal_id", "")
        if did in claimed_ids:
            continue
        u_est = utility_estimates_by_id.get(did)
        if not u_est:
            continue
        acc_comp = getattr(u_est, "components", {}).get("access_feasibility")
        acc_score = getattr(acc_comp, "score", 0.0) if acc_comp else 0.0
        acc_state = getattr(acc_comp, "epistemic_state", "") if acc_comp else ""
        u_score = getattr(u_est, "composite_utility", 0.0)

        # Grounded feasibility check
        if acc_score >= 0.80 and acc_state == "known_favorable" and u_score >= 0.50:
            fp = fp_dict.get(did)
            duration_ms: float | None = None
            if fp:
                scope = getattr(fp, "sample_scope", {})
                if isinstance(scope, dict) and "duration_ms" in scope and scope["duration_ms"] is not None:
                    try:
                        duration_ms = float(scope["duration_ms"])
                    except (ValueError, TypeError):
                        duration_ms = None
            eligible_efficient.append((rec, duration_ms, u_score))

    if eligible_efficient:
        # Check if duration_ms is present and comparable across ALL candidates being compared
        has_comparable_duration = all(t[1] is not None for t in eligible_efficient)
        if has_comparable_duration:
            # Sort by lowest measured duration_ms ascending, then highest utility descending
            eligible_efficient.sort(key=lambda x: (x[1] if x[1] is not None else float("inf"), -x[2], getattr(x[0], "internal_id", "")))
        else:
            # Fall back to sorting by highest utility descending among access-verified candidates
            eligible_efficient.sort(key=lambda x: (-x[2], getattr(x[0], "internal_id", "")))

        eff_rec = eligible_efficient[0][0]
        eff_id = getattr(eff_rec, "internal_id", "")
        assigned_roles[eff_id] = "best_efficient_option"
        claimed_ids.add(eff_id)

    # 5. Best Alternative: Maximum attribute distance from best_overall (>= 0.30)
    best_alt_rec: Any = None
    best_alt_dist: float = -1.0

    for rec in selected_records:
        did = getattr(rec, "internal_id", "")
        if did in claimed_ids:
            continue
        dist = compute_attribute_distance(rec, best_overall_rec)
        if dist >= 0.30 and dist > best_alt_dist:
            best_alt_dist = dist
            best_alt_rec = rec

    if best_alt_rec is not None:
        best_alt_id = getattr(best_alt_rec, "internal_id", "")
        assigned_roles[best_alt_id] = "best_alternative"
        claimed_ids.add(best_alt_id)

    return assigned_roles
