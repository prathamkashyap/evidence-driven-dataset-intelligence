"""Popularity-bias audit and long-tail exploration foundation for M6."""

from .audit import (
    ExposureAuditor,
    compute_exposure_disparity_ratio,
    compute_mean_utility_by_stratum,
    compute_stratum_exposure_share,
    compute_utility_weighted_exposure,
)
from .family import (
    LINKAGE_STATES,
    detect_family_redundancy,
    evaluate_family_linkage,
)
from .pool import (
    DEFAULT_EXPLORATION_CONFIG,
    ExplorationCandidateSet,
    ExplorationPoolBuilder,
    check_exploration_eligibility,
    check_hidden_gem,
)
from .popularity import (
    MEASUREMENT_STATES,
    POPULARITY_STRATA,
    DatasetPopularityProfile,
    build_popularity_profiles,
    compute_profile_id,
    extract_raw_popularity,
)

__all__ = [
    "DEFAULT_EXPLORATION_CONFIG",
    "DatasetPopularityProfile",
    "ExplorationCandidateSet",
    "ExplorationPoolBuilder",
    "ExposureAuditor",
    "LINKAGE_STATES",
    "MEASUREMENT_STATES",
    "POPULARITY_STRATA",
    "build_popularity_profiles",
    "check_exploration_eligibility",
    "check_hidden_gem",
    "compute_exposure_disparity_ratio",
    "compute_mean_utility_by_stratum",
    "compute_profile_id",
    "compute_stratum_exposure_share",
    "compute_utility_weighted_exposure",
    "detect_family_redundancy",
    "evaluate_family_linkage",
    "extract_raw_popularity",
]
