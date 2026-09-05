"""Multi-objective ranking, diversification, and recommendation roles for M7."""

from .diversification import compute_set_diversity, select_diversified_set
from .explanation import (
    RecommendationCard,
    build_recommendation_card,
    compute_card_id,
    generate_structured_explanations,
)
from .pipeline import (
    DEFAULT_PIPELINE_CONFIG,
    RecommendationEngine,
    RecommendationSet,
    compute_same_family_redundancy_count,
)
from .roles import assign_recommendation_roles
from .scoring import (
    DEFAULT_SCORING_WEIGHTS,
    score_candidate_r1,
    score_candidate_r2,
    score_candidate_r3,
)
from .signals import (
    FACET_WEIGHTS,
    CandidateSignals,
    compute_attribute_distance,
    compute_candidate_signals,
    compute_evidence_support_feature,
    compute_risk_penalty,
)

__all__ = [
    "DEFAULT_PIPELINE_CONFIG",
    "DEFAULT_SCORING_WEIGHTS",
    "FACET_WEIGHTS",
    "CandidateSignals",
    "RecommendationCard",
    "RecommendationEngine",
    "RecommendationSet",
    "assign_recommendation_roles",
    "build_recommendation_card",
    "compute_attribute_distance",
    "compute_candidate_signals",
    "compute_card_id",
    "compute_evidence_support_feature",
    "compute_risk_penalty",
    "compute_same_family_redundancy_count",
    "compute_set_diversity",
    "generate_structured_explanations",
    "score_candidate_r1",
    "score_candidate_r2",
    "score_candidate_r3",
    "select_diversified_set",
]
