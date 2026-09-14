"""M7 Pipeline Consistency Audit (formerly Calibration Protocol).

Per B1 decision and docs/M8_EVALUATION.md §7:
This analysis measures whether M7 candidate scores are internally consistent
with the M5 Development Reference Compatibility Rubric. It is NOT an independent
external calibration analysis and does NOT establish that M7 scores are calibrated probabilities.
"""

from __future__ import annotations

from typing import Any

from dataset_intelligence.evaluation.metrics import (
    brier_score,
    descriptive_ece,
    map_m7_score_to_unit_interval,
)
from dataset_intelligence.ranking.scoring import score_candidate_r2
from dataset_intelligence.ranking.signals import compute_candidate_signals

OPTION_C_LIMITATION_STATEMENT = (
    "Option C M7 Pipeline Consistency Audit: Measures internal consistency between "
    "M7 scores and M5 design rubric; not an independent calibration, and not evidence "
    "that M7 scores are calibrated probabilities."
)


def evaluate_m7_consistency(
    task_specs: dict[str, Any],
    candidate_records: list[Any],
    utility_estimates_by_task: dict[str, dict[str, Any]],
    popularity_profiles: dict[str, Any],
    fingerprints: dict[str, Any],
    evidence_entries: dict[str, list[Any]],
    ground_truth_labels: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute Brier score and descriptive ECE across all frozen candidate-task pairs."""
    manifest_tasks = ground_truth_labels.get("tasks", {})
    manifest_datasets = ground_truth_labels.get("dataset_order", [getattr(r, "internal_id", "") for r in candidate_records])
    cfg = config or {}

    probabilities: list[float] = []
    labels: list[int] = []
    pair_details: list[dict[str, Any]] = []

    for task_name, spec in task_specs.items():
        tid = getattr(spec, "task_id", "")
        t_labels = manifest_tasks.get(task_name, {}).get("binary_suitability", [])
        u_dict = utility_estimates_by_task.get(tid, {})

        for d_idx, rec in enumerate(candidate_records):
            did = getattr(rec, "internal_id", "")
            u_est = u_dict.get(did)
            if not u_est:
                continue

            # Candidate intrinsic score under M7 R2 / R3 formula
            signals = compute_candidate_signals(
                record=rec,
                task_spec=spec,
                utility_estimate=u_est,
                evidence_entries=evidence_entries.get(did),
                fingerprint=fingerprints.get(did),
                config=cfg,
            )
            raw_score = score_candidate_r2(signals, weights=cfg.get("scoring_weights"))
            prob = map_m7_score_to_unit_interval(raw_score)

            # Ground-truth binary label
            y = t_labels[d_idx] if d_idx < len(t_labels) else 0

            probabilities.append(prob)
            labels.append(y)
            pair_details.append({
                "task_name": task_name,
                "dataset_id": did,
                "raw_m7_score": raw_score,
                "mapped_probability": prob,
                "binary_reference_label": y,
            })

    bs = brier_score(probabilities, labels)
    ece = descriptive_ece(probabilities, labels, bins=5)

    return {
        "status": "completed",
        "audit_framing": "Option C Internal Pipeline Consistency Audit",
        "limitation_statement": OPTION_C_LIMITATION_STATEMENT,
        "total_pairs_evaluated": len(probabilities),
        "brier_score": bs,
        "descriptive_ece_5_bins": ece,
        "mean_mapped_probability": round(sum(probabilities) / len(probabilities), 6) if probabilities else None,
        "positive_label_ratio": round(sum(labels) / len(labels), 6) if labels else None,
        "pair_details": pair_details,
    }
