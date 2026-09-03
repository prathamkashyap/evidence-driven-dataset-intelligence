"""Task utility estimation foundation: TaskSpecification, components, and baselines."""

from .components import (
    UtilityComponent,
    score_access_feasibility,
    score_governance_compatibility,
    score_modality_compatibility,
    score_quality_compatibility,
    score_structural_compatibility,
    score_target_compatibility,
    score_task_compatibility,
)
from .estimator import (
    DEFAULT_WEIGHTS,
    TaskUtilityEstimate,
    TaskUtilityEstimator,
    compute_estimate_id,
)
from .specification import TaskSpecification, compute_task_id
from .uncertainty import (
    EPISTEMIC_STATES,
    EVIDENCE_BASES,
    StructuredUncertainty,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "EPISTEMIC_STATES",
    "EVIDENCE_BASES",
    "StructuredUncertainty",
    "TaskSpecification",
    "TaskUtilityEstimate",
    "TaskUtilityEstimator",
    "UtilityComponent",
    "compute_estimate_id",
    "compute_task_id",
    "score_access_feasibility",
    "score_governance_compatibility",
    "score_modality_compatibility",
    "score_quality_compatibility",
    "score_structural_compatibility",
    "score_target_compatibility",
    "score_task_compatibility",
]
