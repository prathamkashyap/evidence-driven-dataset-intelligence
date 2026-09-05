#!/usr/bin/env python3
"""Run Milestone 7 Multi-Objective Ranking, Diversification & Recommendation Roles benchmark."""

from __future__ import annotations

import json
from pathlib import Path
import resource
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.ranking.pipeline import RecommendationEngine
from dataset_intelligence.utility.estimator import TaskUtilityEstimate
from dataset_intelligence.utility.specification import TaskSpecification


def main() -> int:
    config_path = ROOT / "configs" / "m7_ranking.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    start_time = time.perf_counter()

    out_dir = ROOT / config["output_directory"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load M1 canonical records
    corpus_path = ROOT / config["input_corpus"]
    records = [
        CanonicalDataset(**json.loads(line))
        for line in corpus_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records_by_id = {r.internal_id: r for r in records}

    # 2. Load M3 evidence ledger entries
    m3_path = ROOT / config["input_m3_ledger"]
    evidence_by_dataset: dict[str, list[Any]] = {}
    if m3_path.exists():
        for line in m3_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                did = item.get("dataset_id")
                if did:
                    evidence_by_dataset.setdefault(did, []).append(item)

    # 3. Load M4 fingerprints
    m4_path = ROOT / config["input_m4_fingerprints"]
    fingerprints_by_dataset: dict[str, DatasetFingerprint] = {}
    if m4_path.exists():
        for line in m4_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                fp_data = json.loads(line)
                if "source_evidence_entry_ids" in fp_data and isinstance(fp_data["source_evidence_entry_ids"], list):
                    fp_data["source_evidence_entry_ids"] = tuple(fp_data["source_evidence_entry_ids"])
                fp = DatasetFingerprint(**fp_data)
                fingerprints_by_dataset[fp.dataset_id] = fp

    # 4. Load M5 utility estimates (filter to baseline_c)
    from dataset_intelligence.utility.components import UtilityComponent
    from dataset_intelligence.utility.uncertainty import StructuredUncertainty

    m5_path = ROOT / config["input_m5_utility"]
    m5_estimates_by_task: dict[str, dict[str, Any]] = {}
    for line in m5_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            if data.get("baseline_mode") == "baseline_c":
                tid = data["task_id"]
                did = data["dataset_id"]
                comp_dict = {
                    k: UtilityComponent(**v) for k, v in data["components"].items()
                }
                unc = StructuredUncertainty(**data["uncertainty"])
                data_clean = dict(data)
                data_clean["components"] = comp_dict
                data_clean["uncertainty"] = unc
                m5_estimates_by_task.setdefault(tid, {})[did] = TaskUtilityEstimate(**data_clean)

    # 5. Load M6 popularity profiles
    m6_prof_path = ROOT / config["input_m6_profiles"]
    profiles_by_dataset: dict[str, Any] = {}
    if m6_prof_path.exists():
        for line in m6_prof_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                pdata = json.loads(line)
                did = pdata["dataset_id"]
                # Convert to simple attribute object
                profiles_by_dataset[did] = type("P", (), pdata)()

    # 6. Load reference tasks
    fixtures_path = ROOT / "tests" / "fixtures" / "m5_fixtures.json"
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    ref_tasks = fixtures.get("reference_tasks", {})

    task_spec_map: dict[str, TaskSpecification] = {}
    for task_name, task_dict in ref_tasks.items():
        spec = TaskSpecification.create(
            task_type=task_dict.get("task_type", "unknown"),
            primary_modality=task_dict.get("primary_modality", "unknown"),
            domain=task_dict.get("domain"),
            target_requirements=task_dict.get("target_requirements"),
            input_constraints=task_dict.get("input_constraints"),
            governance_constraints=task_dict.get("governance_constraints"),
            access_constraints=task_dict.get("access_constraints"),
        )
        task_spec_map[task_name] = spec

    # 7. Execute Baselines R1, R2, R3 across all tasks
    engine = RecommendationEngine(config=config)
    target_k = config.get("target_k", 3)
    baselines = ["r1_utility_only", "r2_multiobjective_linear", "r3_diversified_set"]

    comparison_results: dict[str, Any] = {}
    all_recommendation_sets: list[Any] = []

    for task_name, task_spec in task_spec_map.items():
        u_dict = m5_estimates_by_task.get(task_spec.task_id, {})
        task_comparison: dict[str, Any] = {
            "task_id": task_spec.task_id,
            "task_name": task_name,
            "baselines": {},
        }

        for b_mode in baselines:
            rec_set = engine.recommend(
                task_spec=task_spec,
                candidate_records=records,
                utility_estimates=u_dict,
                popularity_profiles=profiles_by_dataset,
                fingerprints=fingerprints_by_dataset,
                evidence_entries=evidence_by_dataset,
                baseline_mode=b_mode,
                target_k=target_k,
            )
            all_recommendation_sets.append(rec_set)

            selected_ids = rec_set.selected_dataset_ids
            min_u = min([u_dict[did].composite_utility for did in selected_ids]) if selected_ids else 0.0
            roles = [c.assigned_role for c in rec_set.cards if c.assigned_role is not None]

            task_comparison["baselines"][b_mode] = {
                "selected_dataset_ids": list(selected_ids),
                "selected_dataset_names": [
                    records_by_id[did].identity.get("dataset_name", did) for did in selected_ids if did in records_by_id
                ],
                "mean_set_utility": rec_set.mean_set_utility,
                "min_retained_utility": round(min_u, 4),
                "set_diversity_score": rec_set.set_diversity_score,
                "same_family_redundancy_count": rec_set.same_family_redundancy_count,
                "assigned_roles": roles,
                "excluded_gated_count": len(rec_set.excluded_gated_candidates),
            }

        comparison_results[task_name] = task_comparison

    # 8. Write Artifacts
    comparison_file = out_dir / "ranking_comparison.json"
    comparison_file.write_text(json.dumps(comparison_results, indent=2, sort_keys=True), encoding="utf-8")

    rec_sets_file = out_dir / "recommendation_sets.jsonl"
    with open(rec_sets_file, "w", encoding="utf-8") as f:
        for rset in all_recommendation_sets:
            f.write(json.dumps(rset.as_dict(), sort_keys=True) + "\n")

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss = rss if sys.platform == "darwin" else rss * 1024

    # Aggregate metrics across baselines
    agg_metrics: dict[str, dict[str, float]] = {b: {"mean_utility": 0.0, "mean_diversity": 0.0, "total_redundancy": 0.0} for b in baselines}
    for t_res in comparison_results.values():
        for b_mode in baselines:
            b_data = t_res["baselines"][b_mode]
            agg_metrics[b_mode]["mean_utility"] += b_data["mean_set_utility"]
            agg_metrics[b_mode]["mean_diversity"] += b_data["set_diversity_score"]
            agg_metrics[b_mode]["total_redundancy"] += b_data["same_family_redundancy_count"]

    num_tasks = len(task_spec_map)
    for b_mode in baselines:
        agg_metrics[b_mode]["mean_utility"] = round(agg_metrics[b_mode]["mean_utility"] / num_tasks, 4)
        agg_metrics[b_mode]["mean_diversity"] = round(agg_metrics[b_mode]["mean_diversity"] / num_tasks, 4)

    summary = {
        "schema_version": "1.0",
        "total_tasks_evaluated": num_tasks,
        "total_recommendation_sets_generated": len(all_recommendation_sets),
        "target_set_size_k": target_k,
        "baseline_aggregates": agg_metrics,
        "runtime_metrics": {
            "wall_clock_ms": round(elapsed_ms, 2),
            "peak_rss_bytes": peak_rss,
            "peak_rss_mib": round(peak_rss / (1024 * 1024), 2),
            "m0_ceiling_bytes": 134217728,
            "m0_ceiling_mib": 128.0,
            "within_m0_memory_ceiling": peak_rss <= 134217728,
        },
    }

    summary_file = out_dir / "m7_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"M7 Ranking Comparison written: {comparison_file}")
    print(f"M7 Recommendation Sets written: {rec_sets_file} ({len(all_recommendation_sets)} sets)")
    print(f"M7 Summary written: {summary_file}")
    print("\n--- Baseline Comparison Summary ---")
    for b_mode, vals in agg_metrics.items():
        print(f"  {b_mode:25s} | Mean Utility: {vals['mean_utility']:.4f} | Mean Diversity: {vals['mean_diversity']:.4f} | Total Redundancy: {int(vals['total_redundancy'])}")
    print(f"\nPeak RSS: {peak_rss / (1024 * 1024):.2f} MiB (M0 ceiling: 128 MiB)")
    print(f"Wall-clock runtime: {elapsed_ms:.2f} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
