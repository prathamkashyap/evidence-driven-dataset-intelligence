"""Family-aware bounded greedy diversity selection for M7."""

from __future__ import annotations

from typing import Any

from dataset_intelligence.exploration.family import detect_family_redundancy
from .scoring import score_candidate_r3
from .signals import CandidateSignals, compute_attribute_distance


def compute_set_diversity(selected_records: list[Any]) -> float:
    """Compute mean pairwise attribute distance across the selected dataset records."""
    n = len(selected_records)
    if n <= 1:
        return 0.0

    total_dist = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_dist += compute_attribute_distance(selected_records[i], selected_records[j])
            pairs += 1

    return round(total_dist / pairs, 4) if pairs > 0 else 0.0


def select_diversified_set(
    candidates: list[Any],
    signals_by_id: dict[str, CandidateSignals],
    target_k: int = 3,
    lambda_div: float = 0.20,
    config: dict[str, Any] | None = None,
) -> list[tuple[Any, float, float]]:
    """Select a diversified recommendation set S* of size <= target_k.

    Uses Family-Aware Bounded Greedy Diversity Selection, strictly excluding
    same-family mirrors pairwise against all accepted datasets via detect_family_redundancy.

    Returns:
        List of tuples: (selected_record, raw_candidate_score, marginal_diversity_gain)
    """
    selected: list[tuple[Any, float, float]] = []
    selected_records: list[Any] = []
    selected_ids: set[str] = set()

    k = max(1, target_k)

    while len(selected) < k:
        best_candidate: Any = None
        best_cand_score: float = -1.0
        best_marginal_div: float = 0.0
        best_marginal_gain: float = float("-inf")

        for cand in candidates:
            did = getattr(cand, "internal_id", "")
            if did in selected_ids:
                continue

            # 1. Pairwise family redundancy check against ALL accepted records in S*
            is_redundant, _, _ = detect_family_redundancy(cand, selected_records)
            if is_redundant:
                continue

            # 2. Candidate intrinsic score
            sig = signals_by_id.get(did)
            if not sig:
                continue
            cand_score = score_candidate_r3(sig)

            # 3. Set-relative marginal diversity
            if not selected_records:
                marginal_div = 1.0
            else:
                marginal_div = min(compute_attribute_distance(cand, s) for s in selected_records)

            marginal_gain = cand_score + (lambda_div * marginal_div)

            # Deterministic tie-breaking: marginal_gain, cand_score, did
            cand_key = (round(marginal_gain, 6), round(cand_score, 6), did)
            best_key = (
                round(best_marginal_gain, 6),
                round(best_cand_score, 6),
                getattr(best_candidate, "internal_id", "") if best_candidate else "",
            )

            if best_candidate is None or cand_key > best_key:
                best_candidate = cand
                best_cand_score = cand_score
                best_marginal_div = marginal_div
                best_marginal_gain = marginal_gain

        if best_candidate is None:
            # No eligible non-redundant candidates remaining
            break

        best_id = getattr(best_candidate, "internal_id", "")
        selected_ids.add(best_id)
        selected_records.append(best_candidate)
        selected.append((best_candidate, best_cand_score, round(best_marginal_div, 4)))

    return selected
