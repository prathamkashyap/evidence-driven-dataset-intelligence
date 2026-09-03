#!/usr/bin/env python3
"""Run Milestone 5 Task Utility Estimation over the development corpus across Baselines A, B, and C."""

from __future__ import annotations

import json
import math
from pathlib import Path
import resource
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evidence.ledger import LedgerEntry
from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.utility.estimator import (
    TaskUtilityEstimate,
    TaskUtilityEstimator,
)
from dataset_intelligence.utility.specification import TaskSpecification


def compute_dcg(scores: list[float], k: int) -> float:
    """Compute Discounted Cumulative Gain at rank k."""
    dcg = 0.0
    for i, score in enumerate(scores[:k]):
        dcg += (2.0 ** score - 1.0) / math.log2(i + 2.0)
    return dcg


def compute_ndcg(predicted_ranks: list[tuple[str, float]], reference_judgments: dict[str, int], k: int) -> float:
    """Compute Normalized Discounted Cumulative Gain at rank k."""
    actual_gains = [reference_judgments.get(did, 0) for did, _ in predicted_ranks]
    dcg = compute_dcg(actual_gains, k)

    ideal_gains = sorted([reference_judgments.get(did, 0) for did, _ in predicted_ranks], reverse=True)
    idcg = compute_dcg(ideal_gains, k)

    if idcg <= 0.0:
        return 1.0 if dcg <= 0.0 else 0.0
    return round(dcg / idcg, 4)


def compute_spearman_rho(predicted_ranks: list[tuple[str, float]], reference_judgments: dict[str, int]) -> float:
    """Compute Spearman rank correlation between predicted utility and reference judgment."""
    n = len(predicted_ranks)
    if n < 2:
        return 1.0

    # Sort by predicted score descending with dataset_id tie breaker
    sorted_by_pred = sorted(predicted_ranks, key=lambda x: (-x[1], x[0]))
    rank_pred = {did: i + 1 for i, (did, _) in enumerate(sorted_by_pred)}

    # Sort by reference judgment descending
    sorted_by_ref = sorted(predicted_ranks, key=lambda x: (-reference_judgments.get(x[0], 0), x[0]))
    rank_ref = {did: i + 1 for i, (did, _) in enumerate(sorted_by_ref)}

    d_sq_sum = sum((rank_pred[did] - rank_ref[did]) ** 2 for did, _ in predicted_ranks)
    rho = 1.0 - (6.0 * d_sq_sum) / (n * (n * n - 1.0))
    return round(rho, 4)


def main() -> int:
    config_path = ROOT / "configs" / "m5_utility.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    start_time = time.perf_counter()

    corpus_path = ROOT / config["input_corpus"]
    ledger_path = ROOT / config["input_ledger"]
    fp_path = ROOT / config["input_fingerprints"]
    fixtures_path = ROOT / config["reference_tasks_fixture"]
    out_dir = ROOT / config["output_directory"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load canonical records
    raw_corpus = corpus_path.read_text(encoding="utf-8").splitlines()
    records = [CanonicalDataset(**json.loads(line)) for line in raw_corpus if line.strip()]

    # 2. Load M3 ledger entries
    ledger_entries_by_dataset: dict[str, list[LedgerEntry]] = {}
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = LedgerEntry(**json.loads(line))
                ledger_entries_by_dataset.setdefault(entry.dataset_id, []).append(entry)

    # 3. Load M4 fingerprints
    fingerprints_by_dataset: dict[str, DatasetFingerprint] = {}
    if fp_path.is_file():
        for line in fp_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                fp_data = json.loads(line)
                fingerprints_by_dataset[fp_data["dataset_id"]] = DatasetFingerprint(**fp_data)

    # 4. Load reference tasks and reference judgments
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    ref_tasks_raw = fixtures["reference_tasks"]
    ref_judgments_raw = fixtures["reference_compatibility_judgments"]

    tasks: list[TaskSpecification] = []
    for task_name, task_dict in ref_tasks_raw.items():
        spec = TaskSpecification.create(
            task_type=task_dict.get("task_type", "unknown"),
            primary_modality=task_dict.get("primary_modality", "unknown"),
            domain=task_dict.get("domain"),
            target_requirements=task_dict.get("target_requirements"),
            input_constraints=task_dict.get("input_constraints"),
            governance_constraints=task_dict.get("governance_constraints"),
            access_constraints=task_dict.get("access_constraints"),
            raw_query=task_dict.get("raw_query"),
        )
        tasks.append(spec)

    estimator = TaskUtilityEstimator(weights=config.get("baseline_weights"))
    all_estimates: list[TaskUtilityEstimate] = []

    # Structure to hold baseline outputs for metric evaluation: {task_id: {baseline_mode: [(dataset_id, score)]}}
    baseline_predictions: dict[str, dict[str, list[tuple[str, float]]]] = {}

    print(f"Running M5 Task Utility Estimation: {len(tasks)} tasks x {len(records)} datasets x 3 baselines = {len(tasks) * len(records) * 3} evaluations...")

    for task_spec in tasks:
        task_id = task_spec.task_id
        baseline_predictions[task_id] = {"baseline_a": [], "baseline_b": [], "baseline_c": []}

        for record in records:
            did = record.internal_id
            m3_entries = ledger_entries_by_dataset.get(did, [])
            fingerprint = fingerprints_by_dataset.get(did)

            # Baseline A: Metadata only
            est_a = estimator.evaluate(record, task_spec, baseline_mode="baseline_a")
            all_estimates.append(est_a)
            baseline_predictions[task_id]["baseline_a"].append((did, est_a.composite_utility))

            # Baseline B: Metadata + M3 evidence
            est_b = estimator.evaluate(record, task_spec, m3_entries=m3_entries, baseline_mode="baseline_b")
            all_estimates.append(est_b)
            baseline_predictions[task_id]["baseline_b"].append((did, est_b.composite_utility))

            # Baseline C: Metadata + M3 evidence + M4 fingerprint
            est_c = estimator.evaluate(record, task_spec, m3_entries=m3_entries, fingerprint=fingerprint, baseline_mode="baseline_c")
            all_estimates.append(est_c)
            baseline_predictions[task_id]["baseline_c"].append((did, est_c.composite_utility))

    # Export estimates to JSONL
    estimates_file = out_dir / "utility_estimates.jsonl"
    with open(estimates_file, "w", encoding="utf-8") as f:
        for est in all_estimates:
            f.write(json.dumps(est.as_dict(), sort_keys=True) + "\n")

    # Metric evaluation across tasks
    ablation_results: dict[str, Any] = {
        "schema_version": "1.0",
        "reference_rubric_description": "Development reference compatibility judgments on a 0-3 ordinal scale (3=high, 2=moderate, 1=marginal, 0=incompatible).",
        "baselines_evaluated": {
            "baseline_a": "Metadata-only compatibility (naive assumption: unobserved quality and access = 1.0)",
            "baseline_b": "Metadata + M3 evidence ledger (detects M3 conflicts, operational access failures)",
            "baseline_c": "Full evidence-driven utility (Metadata + M3 evidence + M4 fingerprint diagnostics)",
        },
        "metrics_per_task": {},
        "mean_metrics": {},
    }

    # Map task_id back to fixture task name for judgment lookup
    task_name_map = {}
    for task_name, task_dict in ref_tasks_raw.items():
        spec = TaskSpecification.create(
            task_type=task_dict.get("task_type", "unknown"),
            primary_modality=task_dict.get("primary_modality", "unknown"),
            domain=task_dict.get("domain"),
            target_requirements=task_dict.get("target_requirements"),
            input_constraints=task_dict.get("input_constraints"),
            governance_constraints=task_dict.get("governance_constraints"),
            access_constraints=task_dict.get("access_constraints"),
        )
        task_name_map[spec.task_id] = task_name

    baseline_metrics_accum: dict[str, dict[str, list[float]]] = {
        "baseline_a": {"spearman_rho": [], "ndcg_3": [], "ndcg_5": [], "ndcg_10": []},
        "baseline_b": {"spearman_rho": [], "ndcg_3": [], "ndcg_5": [], "ndcg_10": []},
        "baseline_c": {"spearman_rho": [], "ndcg_3": [], "ndcg_5": [], "ndcg_10": []},
    }

    for task_spec in tasks:
        tid = task_spec.task_id
        tname = task_name_map.get(tid, tid)
        ref_judgments_for_task = {
            did: info["level"]
            for did, info in ref_judgments_raw.get(tname, {}).items()
        }

        task_metrics: dict[str, Any] = {}
        for b_mode in ["baseline_a", "baseline_b", "baseline_c"]:
            preds = baseline_predictions[tid][b_mode]
            rho = compute_spearman_rho(preds, ref_judgments_for_task)
            ndcg_3 = compute_ndcg(preds, ref_judgments_for_task, 3)
            ndcg_5 = compute_ndcg(preds, ref_judgments_for_task, 5)
            ndcg_10 = compute_ndcg(preds, ref_judgments_for_task, 10)

            task_metrics[b_mode] = {
                "spearman_rho": rho,
                "ndcg_at_3": ndcg_3,
                "ndcg_at_5": ndcg_5,
                "ndcg_at_10": ndcg_10,
            }
            baseline_metrics_accum[b_mode]["spearman_rho"].append(rho)
            baseline_metrics_accum[b_mode]["ndcg_3"].append(ndcg_3)
            baseline_metrics_accum[b_mode]["ndcg_5"].append(ndcg_5)
            baseline_metrics_accum[b_mode]["ndcg_10"].append(ndcg_10)

        ablation_results["metrics_per_task"][tname] = task_metrics

    # Compute mean metrics across tasks
    for b_mode, m_dict in baseline_metrics_accum.items():
        ablation_results["mean_metrics"][b_mode] = {
            "mean_spearman_rho": round(sum(m_dict["spearman_rho"]) / len(m_dict["spearman_rho"]), 4),
            "mean_ndcg_at_3": round(sum(m_dict["ndcg_3"]) / len(m_dict["ndcg_3"]), 4),
            "mean_ndcg_at_5": round(sum(m_dict["ndcg_5"]) / len(m_dict["ndcg_5"]), 4),
            "mean_ndcg_at_10": round(sum(m_dict["ndcg_10"]) / len(m_dict["ndcg_10"]), 4),
        }

    ablation_file = out_dir / "baseline_ablation.json"
    ablation_file.write_text(json.dumps(ablation_results, indent=2, sort_keys=True), encoding="utf-8")

    # Aggregate summary
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss = rss if sys.platform == "darwin" else rss * 1024

    hard_gated_count = sum(1 for e in all_estimates if e.hard_gated)
    epistemic_states_counts: dict[str, int] = {}
    for est in all_estimates:
        for comp in est.components.values():
            epistemic_states_counts[comp.epistemic_state] = epistemic_states_counts.get(comp.epistemic_state, 0) + 1

    summary = {
        "schema_version": "1.0",
        "total_evaluations": len(all_estimates),
        "tasks_evaluated": len(tasks),
        "candidates_evaluated": len(records),
        "baselines_evaluated": 3,
        "hard_gated_evaluations_count": hard_gated_count,
        "epistemic_states_distribution": dict(sorted(epistemic_states_counts.items())),
        "ablation_summary": ablation_results["mean_metrics"],
        "runtime_metrics": {
            "wall_clock_ms": round(elapsed_ms, 2),
            "per_eval_ms": round(elapsed_ms / len(all_estimates), 3),
            "peak_rss_bytes": peak_rss,
            "peak_rss_mib": round(peak_rss / (1024 * 1024), 2),
            "m0_ceiling_bytes": 134217728,
            "m0_ceiling_mib": 128.0,
            "within_m0_memory_ceiling": peak_rss <= 134217728,
        },
    }

    summary_file = out_dir / "utility_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Estimates exported: {estimates_file} ({len(all_estimates)} records)")
    print(f"Ablation results written: {ablation_file}")
    print(f"Summary written: {summary_file}")
    print(f"Baseline A Mean Spearman rho: {ablation_results['mean_metrics']['baseline_a']['mean_spearman_rho']}, NDCG@3: {ablation_results['mean_metrics']['baseline_a']['mean_ndcg_at_3']}")
    print(f"Baseline B Mean Spearman rho: {ablation_results['mean_metrics']['baseline_b']['mean_spearman_rho']}, NDCG@3: {ablation_results['mean_metrics']['baseline_b']['mean_ndcg_at_3']}")
    print(f"Baseline C Mean Spearman rho: {ablation_results['mean_metrics']['baseline_c']['mean_spearman_rho']}, NDCG@3: {ablation_results['mean_metrics']['baseline_c']['mean_ndcg_at_3']}")
    print(f"Peak RSS: {peak_rss / (1024 * 1024):.2f} MiB (M0 ceiling: 128 MiB)")
    print(f"Wall-clock runtime: {elapsed_ms:.2f} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
