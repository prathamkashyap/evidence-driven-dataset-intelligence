"""Pure, offline metrics used by the M8 evaluator.

These functions deliberately return ``None`` for an unavailable denominator rather
than manufacturing a score or removing a case from an aggregate.
"""

from __future__ import annotations

from math import sqrt
from typing import Iterable, Sequence


M7_SCORE_MIN = -0.15
M7_SCORE_MAX = 1.00


def mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return round(sum(items) / len(items), 6) if items else None


def set_jaccard(left: Sequence[str], right: Sequence[str]) -> float | None:
    union = set(left) | set(right)
    return round(len(set(left) & set(right)) / len(union), 6) if union else None


def kendall_tau(left: Sequence[str], right: Sequence[str]) -> float | None:
    """Kendall tau-a on IDs shared by two deterministic rankings.

    The M8 ranked lists use deterministic dataset-ID tie breaking, so no tie
    adjustment is required. A singleton ranking has no comparable pair and is N/A.
    """
    common = [item for item in left if item in set(right)]
    if len(common) < 2:
        return None
    right_pos = {item: index for index, item in enumerate(right)}
    concordant = discordant = 0
    for index, first in enumerate(common):
        for second in common[index + 1 :]:
            if right_pos[first] < right_pos[second]:
                concordant += 1
            else:
                discordant += 1
    pairs = concordant + discordant
    return round((concordant - discordant) / pairs, 6) if pairs else None


def map_m7_score_to_unit_interval(score: float) -> float:
    """Apply the preregistered linear mapping, without clipping."""
    if not M7_SCORE_MIN <= score <= M7_SCORE_MAX:
        raise ValueError(f"M7 score outside frozen range [{M7_SCORE_MIN}, {M7_SCORE_MAX}]: {score}")
    return round((score + 0.15) / 1.15, 8)


def brier_score(probabilities: Sequence[float], labels: Sequence[int]) -> float | None:
    if len(probabilities) != len(labels):
        raise ValueError("Brier inputs must have equal lengths.")
    if not probabilities:
        return None
    if any(not 0.0 <= value <= 1.0 for value in probabilities) or any(label not in {0, 1} for label in labels):
        raise ValueError("Brier inputs must be unit probabilities and binary labels.")
    return round(sum((probability - label) ** 2 for probability, label in zip(probabilities, labels)) / len(labels), 6)


def descriptive_ece(probabilities: Sequence[float], labels: Sequence[int], bins: int = 5) -> float | None:
    """Five-bin ECE retained only as the Option C descriptive diagnostic."""
    if len(probabilities) != len(labels):
        raise ValueError("ECE inputs must have equal lengths.")
    if not probabilities:
        return None
    if bins < 1:
        raise ValueError("ECE needs at least one bin.")
    total = len(probabilities)
    result = 0.0
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        members = [item for item, probability in enumerate(probabilities) if lower <= probability < upper or (index == bins - 1 and probability == 1.0)]
        if not members:
            continue
        accuracy = sum(labels[item] for item in members) / len(members)
        confidence = sum(probabilities[item] for item in members) / len(members)
        result += (len(members) / total) * abs(accuracy - confidence)
    return round(result, 6)


def pearson_correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right):
        raise ValueError("Correlation inputs must have equal lengths.")
    if len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((x - mean_left) * (y - mean_right) for x, y in zip(left, right))
    left_scale = sqrt(sum((x - mean_left) ** 2 for x in left))
    right_scale = sqrt(sum((y - mean_right) ** 2 for y in right))
    if left_scale == 0.0 or right_scale == 0.0:
        return None
    return round(numerator / (left_scale * right_scale), 6)


def rank_values(values: Sequence[float]) -> list[float]:
    """Average tied ranks, ascending, with no dependency on a statistics package."""
    sorted_indices = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(sorted_indices):
        end = start
        while end + 1 < len(sorted_indices) and values[sorted_indices[end + 1]] == values[sorted_indices[start]]:
            end += 1
        rank = (start + end + 2) / 2.0
        for offset in range(start, end + 1):
            ranks[sorted_indices[offset]] = rank
        start = end + 1
    return ranks


def partial_spearman(popularity: Sequence[float], rank: Sequence[float], suitability: Sequence[float]) -> float | None:
    """Partial rank correlation of popularity and rank while holding suitability.

    It is N/A if the frozen data do not supply at least three measured values or
    a non-degenerate residual. This is an audit only; popularity never feeds M7.
    """
    if not (len(popularity) == len(rank) == len(suitability)):
        raise ValueError("Partial correlation inputs must have equal lengths.")
    if len(popularity) < 3:
        return None
    x, y, z = rank_values(popularity), rank_values(rank), rank_values(suitability)
    r_xy = pearson_correlation(x, y)
    r_xz = pearson_correlation(x, z)
    r_yz = pearson_correlation(y, z)
    if r_xy is None or r_xz is None or r_yz is None:
        return None
    denominator = sqrt((1 - r_xz**2) * (1 - r_yz**2))
    return round((r_xy - r_xz * r_yz) / denominator, 6) if denominator else None
