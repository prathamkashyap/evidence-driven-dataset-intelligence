"""M8 evaluation package — frozen benchmark evaluation, ablations, robustness, calibration.

All evaluation code consumes M1-M7 interfaces strictly as a client.
No M8 logic is pushed backward into ranking, utility, exploration, evidence, or retrieval.

M0-M7 are frozen at commit 7d6172813e78afd15488ea8995b7365be66e215c.
"""

from __future__ import annotations

from .ablations import execute_ablation_rung, recommend_rung_7, select_farthest_first_without_family_check
from .benchmark_inputs import EXPECTED_TASK_ORDER, validate_frozen_benchmark_inputs
from .consistency import OPTION_C_LIMITATION_STATEMENT, evaluate_m7_consistency
from .harness import M8EvaluationHarness
from .hypotheses import evaluate_h1, evaluate_h2, evaluate_h3, evaluate_h4, evaluate_h5
from .metrics import (
    brier_score,
    descriptive_ece,
    kendall_tau,
    map_m7_score_to_unit_interval,
    mean,
    partial_spearman,
    pearson_correlation,
    rank_values,
    set_jaccard,
)
from .resources import build_reproducibility_record, measure_peak_rss_bytes
from .robustness import evaluate_robustness, fresh_corrupted_evidence, fresh_corrupted_record
from .sensitivity import evaluate_parameter_sensitivity, perturb_positive_weights

__all__ = [
    "EXPECTED_TASK_ORDER",
    "M8EvaluationHarness",
    "OPTION_C_LIMITATION_STATEMENT",
    "brier_score",
    "build_reproducibility_record",
    "descriptive_ece",
    "evaluate_h1",
    "evaluate_h2",
    "evaluate_h3",
    "evaluate_h4",
    "evaluate_h5",
    "evaluate_m7_consistency",
    "evaluate_parameter_sensitivity",
    "evaluate_robustness",
    "execute_ablation_rung",
    "fresh_corrupted_evidence",
    "fresh_corrupted_record",
    "kendall_tau",
    "map_m7_score_to_unit_interval",
    "mean",
    "measure_peak_rss_bytes",
    "partial_spearman",
    "pearson_correlation",
    "perturb_positive_weights",
    "rank_values",
    "recommend_rung_7",
    "select_farthest_first_without_family_check",
    "set_jaccard",
    "validate_frozen_benchmark_inputs",
]
