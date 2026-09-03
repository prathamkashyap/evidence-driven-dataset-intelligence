#!/usr/bin/env python3
"""Run Milestone 6 Popularity-Bias Audit and Long-Tail Exploration over the development corpus."""

from __future__ import annotations

import json
from pathlib import Path
import resource
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.exploration.audit import ExposureAuditor
from dataset_intelligence.exploration.pool import ExplorationPoolBuilder
from dataset_intelligence.exploration.popularity import build_popularity_profiles
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.utility.estimator import TaskUtilityEstimate
from dataset_intelligence.utility.specification import TaskSpecification


def main() -> int:
    config_path = ROOT / "configs" / "m6_popularity.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    start_time = time.perf_counter()

    corpus_path = ROOT / config["input_corpus"]
    m2_path = ROOT / config["input_m2_benchmark"]
    m5_path = ROOT / config["input_m5_utility"]
    out_dir = ROOT / config["output_directory"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load canonical records
    raw_corpus = corpus_path.read_text(encoding="utf-8").splitlines()
    records = [CanonicalDataset(**json.loads(line)) for line in raw_corpus if line.strip()]
    records_by_id = {r.internal_id: r for r in records}
    corpus_dataset_ids = [r.internal_id for r in records]

    # 2. Build popularity profiles
    profiles = build_popularity_profiles(records, config=config)
    profiles_file = out_dir / "popularity_profiles.jsonl"
    with open(profiles_file, "w", encoding="utf-8") as f:
        for did, prof in sorted(profiles.items()):
            f.write(json.dumps(prof.as_dict(), sort_keys=True) + "\n")

    # 3. Load M2 benchmark retrieval runs (extract Hybrid RRF runs)
    m2_data = json.loads(m2_path.read_text(encoding="utf-8"))
    m2_hybrid_runs: dict[str, list[str]] = {}
    for run in m2_data.get("runs", []):
        if run.get("method") == "hybrid_rrf":
            qid = run.get("query_id", "")
            results = [item["dataset_id"] for item in run.get("results", [])]
            m2_hybrid_runs[qid] = results

    # 4. Load M5 utility estimates (filter to baseline_c)
    raw_m5 = m5_path.read_text(encoding="utf-8").splitlines()
    # Map: {task_id: {dataset_id: TaskUtilityEstimate}}
    m5_estimates_by_task: dict[str, dict[str, TaskUtilityEstimate]] = {}
    for line in raw_m5:
        if line.strip():
            data = json.loads(line)
            if data.get("baseline_mode") == "baseline_c":
                tid = data["task_id"]
                did = data["dataset_id"]
                m5_estimates_by_task.setdefault(tid, {})[did] = data

    # 5. Load reference tasks
    fixtures_path = ROOT / "tests" / "fixtures" / "m5_fixtures.json"
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    ref_tasks = fixtures.get("reference_tasks", {})

    task_spec_map: dict[str, TaskSpecification] = {}
    query_to_task_map = {
        "q_text_sentiment": "task_sentiment_binary",
        "q_news": "task_news_multiclass",
        "q_tabular_wine": "task_tabular_iris",  # Development evaluation alignment
        "q_image_leaf": "task_image_cifar",
    }

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

    # 6. Run Exposure Audit across development queries
    auditor = ExposureAuditor(profiles)
    audit_results: dict[str, Any] = {
        "schema_version": "1.0",
        "disclaimer": "Development simulation on 10 datasets across 4 queries; does not claim generalized web-scale popularity bias.",
        "query_audits": {},
    }

    for qid, retrieved_ids in m2_hybrid_runs.items():
        tname = query_to_task_map.get(qid, "task_sentiment_binary")
        tspec = task_spec_map.get(tname)
        if not tspec:
            continue

        u_dict = m5_estimates_by_task.get(tspec.task_id, {})
        # Convert dictionary data to lightweight objects with .composite_utility
        class TempUtil:
            def __init__(self, comp_u): self.composite_utility = comp_u
        u_objs = {did: TempUtil(d.get("composite_utility", 0.0)) for did, d in u_dict.items()}

        audit_res = auditor.audit_retrieval_run(
            query_id=qid,
            retrieved_dataset_ids=retrieved_ids,
            corpus_dataset_ids=corpus_dataset_ids,
            utility_estimates=u_objs,
            top_k=config["exploration_parameters"].get("retrieval_top_k", 3),
        )
        audit_results["query_audits"][qid] = audit_res

    audit_file = out_dir / "popularity_audit.json"
    audit_file.write_text(json.dumps(audit_results, indent=2, sort_keys=True), encoding="utf-8")

    # 7. Run Long-Tail Exploration Pool Builder
    builder = ExplorationPoolBuilder(config=config["exploration_parameters"])
    exploration_sets: list[Any] = []
    comparison_summary: dict[str, Any] = {}

    for qid, retrieved_ids in m2_hybrid_runs.items():
        tname = query_to_task_map.get(qid, "task_sentiment_binary")
        tspec = task_spec_map.get(tname)
        if not tspec:
            continue

        u_raw_dict = m5_estimates_by_task.get(tspec.task_id, {})
        # Reconstruct structured objects
        class TempFullUtil:
            def __init__(self, d):
                self.composite_utility = d.get("composite_utility", 0.0)
                self.hard_gated = d.get("hard_gated", False)
                self.components = {
                    k: type("C", (), {"score": v.get("score", 0.0), "epistemic_state": v.get("epistemic_state", "")})()
                    for k, v in d.get("components", {}).items()
                }
        u_full_objs = {did: TempFullUtil(d) for did, d in u_raw_dict.items()}

        exp_set = builder.build_exploration_set(
            task_id=tspec.task_id,
            query_id=qid,
            retrieved_dataset_ids=retrieved_ids,
            corpus_records=records,
            popularity_profiles=profiles,
            utility_estimates=u_full_objs,
        )
        exploration_sets.append(exp_set)

        # Compute Condition A vs Condition B set metrics
        cond_a_ids = exp_set.main_pool_dataset_ids
        cond_b_ids = tuple(list(exp_set.main_pool_dataset_ids) + list(exp_set.selected_exploration_dataset_ids))

        u_a = [u_full_objs[did].composite_utility for did in cond_a_ids if did in u_full_objs]
        u_b = [u_full_objs[did].composite_utility for did in cond_b_ids if did in u_full_objs]

        mean_u_a = round(sum(u_a) / len(u_a), 4) if u_a else 0.0
        mean_u_b = round(sum(u_b) / len(u_b), 4) if u_b else 0.0

        comparison_summary[qid] = {
            "task_name": tname,
            "condition_a_main_pool": cond_a_ids,
            "condition_a_mean_utility": mean_u_a,
            "condition_b_augmented_pool": cond_b_ids,
            "condition_b_mean_utility": mean_u_b,
            "under_exposed_candidates_count": len(exp_set.under_exposed_dataset_ids),
            "eligible_exploration_count": len(exp_set.eligible_exploration_dataset_ids),
            "selected_exploration_additions_count": len(exp_set.selected_exploration_dataset_ids),
            "hidden_gems_found": exp_set.hidden_gem_dataset_ids,
            "under_observed_high_utility_found": exp_set.under_observed_high_utility_dataset_ids,
            "redundant_family_variants_detected": exp_set.redundant_family_variants,
        }

    pools_file = out_dir / "exploration_pools.jsonl"
    with open(pools_file, "w", encoding="utf-8") as f:
        for eset in exploration_sets:
            f.write(json.dumps(eset.as_dict(), sort_keys=True) + "\n")

    # 8. Resource and Summary Statistics
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss = rss if sys.platform == "darwin" else rss * 1024

    measured_count = sum(1 for p in profiles.values() if p.popularity_measurement_state == "measured")
    under_obs_count = sum(1 for p in profiles.values() if p.popularity_measurement_state == "under_observed")
    strata_dist = {}
    for p in profiles.values():
        strata_dist[p.popularity_stratum] = strata_dist.get(p.popularity_stratum, 0) + 1

    total_gems = sum(len(s.hidden_gem_dataset_ids) for s in exploration_sets)
    total_under_obs_hi_u = sum(len(s.under_observed_high_utility_dataset_ids) for s in exploration_sets)

    summary = {
        "schema_version": "1.0",
        "total_profiles_generated": len(profiles),
        "measured_popularity_count": measured_count,
        "under_observed_popularity_count": under_obs_count,
        "popularity_strata_distribution": dict(sorted(strata_dist.items())),
        "total_queries_audited": len(m2_hybrid_runs),
        "total_hidden_gems_identified": total_gems,
        "total_under_observed_high_utility_identified": total_under_obs_hi_u,
        "exploration_simulation_summary": comparison_summary,
        "runtime_metrics": {
            "wall_clock_ms": round(elapsed_ms, 2),
            "peak_rss_bytes": peak_rss,
            "peak_rss_mib": round(peak_rss / (1024 * 1024), 2),
            "m0_ceiling_bytes": 134217728,
            "m0_ceiling_mib": 128.0,
            "within_m0_memory_ceiling": peak_rss <= 134217728,
        },
    }

    summary_file = out_dir / "m6_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"M6 Popularity Profiles written: {profiles_file} ({len(profiles)} records)")
    print(f"M6 Exposure Audit written: {audit_file}")
    print(f"M6 Exploration Pools written: {pools_file} ({len(exploration_sets)} queries)")
    print(f"M6 Summary written: {summary_file}")
    print(f"Popularity Breakdown: {measured_count} measured ({strata_dist}), {under_obs_count} under_observed")
    print(f"Exploration Yield: {total_gems} measured hidden gems, {total_under_obs_hi_u} under-observed high-utility candidates")
    print(f"Peak RSS: {peak_rss / (1024 * 1024):.2f} MiB (M0 ceiling: 128 MiB)")
    print(f"Wall-clock runtime: {elapsed_ms:.2f} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
