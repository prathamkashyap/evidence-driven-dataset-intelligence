"""Candidate scoring functions for Baselines R1, R2, and Proposed R3."""

from __future__ import annotations

from typing import Any

from .signals import CandidateSignals

DEFAULT_SCORING_WEIGHTS = {
    "w_fit": 0.35,
    "w_util": 0.35,
    "w_evid": 0.15,
    "w_cov": 0.15,
    "w_risk": 0.15,
}


def score_candidate_r1(signals: CandidateSignals) -> float:
    """Baseline R1: Utility-only candidate score in raw range [0.0, 1.0]."""
    return round(signals.utility_score, 4)


def score_candidate_r2(
    signals: CandidateSignals,
    weights: dict[str, float] | None = None,
) -> float:
    """Baseline R2: Linear multi-objective candidate score in raw range [-0.15, 1.00]."""
    w = weights or DEFAULT_SCORING_WEIGHTS
    score = (
        w.get("w_fit", 0.35) * signals.fit_score
        + w.get("w_util", 0.35) * signals.utility_score
        + w.get("w_evid", 0.15) * signals.evidence_support_score
        + w.get("w_cov", 0.15) * signals.content_coverage_score
        - w.get("w_risk", 0.15) * signals.risk_penalty
    )
    return round(score, 4)


def score_candidate_r3(
    signals: CandidateSignals,
    weights: dict[str, float] | None = None,
) -> float:
    """Proposed R3: Candidate intrinsic score in raw range [-0.15, 1.00]."""
    return score_candidate_r2(signals, weights=weights)
