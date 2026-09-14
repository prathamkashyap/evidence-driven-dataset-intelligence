"""M8 Evaluation Harness orchestrating all preregistered analyses in memory without network egress.

Client of frozen M0-M7 modules and frozen M8 benchmark inputs.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from dataset_intelligence.evaluation.ablations import execute_ablation_rung, recommend_rung_7
from dataset_intelligence.evaluation.benchmark_inputs import EXPECTED_TASK_ORDER, validate_frozen_benchmark_inputs
from dataset_intelligence.evaluation.consistency import evaluate_m7_consistency
from dataset_intelligence.evaluation.hypotheses import (
    evaluate_h1,
    evaluate_h2,
    evaluate_h3,
    evaluate_h4,
    evaluate_h5,
)
from dataset_intelligence.evaluation.resources import (
    build_reproducibility_record,
    measure_peak_rss_bytes,
)
from dataset_intelligence.evaluation.robustness import evaluate_robustness
from dataset_intelligence.evaluation.sensitivity import evaluate_parameter_sensitivity
from dataset_intelligence.exploration.popularity import build_popularity_profiles
from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.ranking.pipeline import RecommendationEngine
from dataset_intelligence.utility.components import UtilityComponent
from dataset_intelligence.utility.estimator import TaskUtilityEstimate
from dataset_intelligence.utility.specification import TaskSpecification
from dataset_intelligence.utility.uncertainty import StructuredUncertainty


class M8EvaluationHarness:
    """Offline, deterministic evaluation harness for the frozen M8 benchmark."""

    def __init__(self, root: Path, config: dict[str, Any] | None = None) -> None:
        self.root = root.resolve()
        config_path = self.root / "configs/m8_evaluation.json"
        self.config = config or json.loads(config_path.read_text(encoding="utf-8"))
        self._loaded = False

    def load_inputs(self) -> None:
        """Validate and load all frozen benchmark artifacts."""
        if self._loaded:
            return

        # 1. Validate frozen inputs contract and hashes
        validate_frozen_benchmark_inputs(self.root)

        # 2. Load manifest, labels, corruption fixtures, human selection
        self.manifest = json.loads((self.root / self.config["inputs"]["manifest"]).read_text(encoding="utf-8"))
        self.labels = json.loads((self.root / self.config["inputs"]["labels"]).read_text(encoding="utf-8"))
        self.corruption_fixtures = json.loads((self.root / self.config["inputs"]["corruption_fixtures"]).read_text(encoding="utf-8"))
        self.human_selection = json.loads((self.root / self.config["inputs"]["human_selection"]).read_text(encoding="utf-8"))

        # 3. Load 24 benchmark corpus records in manifest order
        corpus_path = self.root / self.config["candidate_pool"]["corpus"]
        raw_records = [
            CanonicalDataset(**json.loads(line))
            for line in corpus_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        manifest_order = [item["dataset_id"] for item in self.manifest["corpus"]]
        records_by_id = {r.internal_id: r for r in raw_records}
        self.records = [records_by_id[did] for did in manifest_order]

        # 4. Load evidence ledger entries
        evidence_path = self.root / "experiments/m8/evidence/benchmark_evidence_ledger.jsonl"
        self.evidence_by_dataset: dict[str, list[Any]] = {}
        for line in evidence_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                did = item.get("dataset_id")
                if did:
                    self.evidence_by_dataset.setdefault(did, []).append(item)

        # 5. Load fingerprints
        fp_path = self.root / "experiments/m8/fingerprints/benchmark_fingerprints.jsonl"
        self.fingerprints_by_dataset: dict[str, DatasetFingerprint] = {}
        for line in fp_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                fp_data = json.loads(line)
                if "source_evidence_entry_ids" in fp_data and isinstance(fp_data["source_evidence_entry_ids"], list):
                    fp_data["source_evidence_entry_ids"] = tuple(fp_data["source_evidence_entry_ids"])
                fp = DatasetFingerprint(**fp_data)
                self.fingerprints_by_dataset[fp.dataset_id] = fp

        # 6. Load utility estimates
        util_path = self.root / "experiments/m8/utility/benchmark_utility_estimates.jsonl"
        self.utility_estimates_by_task: dict[str, dict[str, TaskUtilityEstimate]] = {}
        for line in util_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                data = json.loads(line)
                tid = data["task_id"]
                did = data["dataset_id"]
                comp_dict = {k: UtilityComponent(**v) for k, v in data["components"].items()}
                unc = StructuredUncertainty(**data["uncertainty"])
                clean_data = dict(data)
                clean_data["components"] = comp_dict
                clean_data["uncertainty"] = unc
                self.utility_estimates_by_task.setdefault(tid, {})[did] = TaskUtilityEstimate(**clean_data)

        # 7. Popularity profiles
        self.profiles = build_popularity_profiles(self.records)

        # 8. Reconstruct TaskSpecifications in exact preregistered order
        prep_config = json.loads((self.root / "configs/m8_corpus_preparation.json").read_text(encoding="utf-8"))
        raw_specs = prep_config.get("task_specifications", {})
        self.task_specs: dict[str, TaskSpecification] = {}
        for task_name in EXPECTED_TASK_ORDER:
            val = raw_specs[task_name]
            self.task_specs[task_name] = TaskSpecification.create(
                task_type=val.get("task_type", "unknown"),
                primary_modality=val.get("primary_modality", "unknown"),
                domain=val.get("domain"),
                target_requirements=val.get("target_requirements"),
                input_constraints=val.get("input_constraints"),
                scale_constraints=val.get("scale_constraints"),
                governance_constraints=val.get("governance_constraints"),
                access_constraints=val.get("access_constraints"),
                explicit_user_constraints=val.get("explicit_user_constraints"),
                unresolved_requirements=val.get("unresolved_requirements"),
                raw_query=val.get("raw_query"),
            )

        self._loaded = True

    def run_baselines(self) -> dict[str, Any]:
        """Execute Baselines R1, R2, and R3 across all 8 benchmark tasks."""
        self.load_inputs()
        engine = RecommendationEngine(config=self.config)
        target_k = self.config.get("target_k", 3)
        baselines = ["r1_utility_only", "r2_multiobjective_linear", "r3_diversified_set"]

        task_results: dict[str, Any] = {}
        recommendation_sets: list[Any] = []
        r3_sets: list[Any] = []

        for task_name, spec in self.task_specs.items():
            tid = spec.task_id
            u_dict = self.utility_estimates_by_task.get(tid, {})
            task_comparison: dict[str, Any] = {
                "task_id": tid,
                "task_name": task_name,
                "baselines": {},
            }

            for b_mode in baselines:
                rec_set = engine.recommend(
                    task_spec=spec,
                    candidate_records=self.records,
                    utility_estimates=u_dict,
                    popularity_profiles=self.profiles,
                    fingerprints=self.fingerprints_by_dataset,
                    evidence_entries=self.evidence_by_dataset,
                    baseline_mode=b_mode,
                    target_k=target_k,
                )
                recommendation_sets.append(rec_set)
                if b_mode == "r3_diversified_set":
                    r3_sets.append(rec_set)

                selected_ids = list(rec_set.selected_dataset_ids)
                min_u = min([u_dict[did].composite_utility for did in selected_ids]) if selected_ids else 0.0
                roles = [c.assigned_role for c in rec_set.cards if c.assigned_role is not None]

                task_comparison["baselines"][b_mode] = {
                    "selected_dataset_ids": selected_ids,
                    "mean_set_utility": rec_set.mean_set_utility,
                    "min_retained_utility": round(min_u, 4),
                    "set_diversity_score": rec_set.set_diversity_score,
                    "same_family_redundancy_count": rec_set.same_family_redundancy_count,
                    "assigned_roles": roles,
                    "excluded_gated_count": len(rec_set.excluded_gated_candidates),
                }

            task_results[task_name] = task_comparison

        return {
            "task_results": task_results,
            "all_recommendation_sets": recommendation_sets,
            "r3_recommendation_sets": r3_sets,
        }

    def run_ablations(self) -> dict[str, Any]:
        """Execute the 8-rung ablation ladder (Rungs 0 to 8) across all tasks."""
        self.load_inputs()
        target_k = self.config.get("target_k", 3)
        ladder_results: dict[str, Any] = {}

        for task_name, spec in self.task_specs.items():
            tid = spec.task_id
            u_dict = self.utility_estimates_by_task.get(tid, {})
            task_rungs: dict[str, Any] = {}

            for rung_id in range(9):
                rung_res = execute_ablation_rung(
                    rung_id=rung_id,
                    task_spec=spec,
                    candidate_records=self.records,
                    utility_estimates=u_dict,
                    popularity_profiles=self.profiles,
                    fingerprints=self.fingerprints_by_dataset,
                    evidence_entries=self.evidence_by_dataset,
                    target_k=target_k,
                    config=self.config,
                )
                task_rungs[rung_res["rung_name"]] = rung_res

            ladder_results[task_name] = task_rungs

        return ladder_results

    def run_hypotheses(self, baseline_output: dict[str, Any]) -> dict[str, Any]:
        """Evaluate preregistered hypotheses H1 through H5."""
        self.load_inputs()
        task_results = baseline_output["task_results"]
        r3_sets = baseline_output["r3_recommendation_sets"]

        r1_recs = {tname: res["baselines"]["r1_utility_only"]["selected_dataset_ids"] for tname, res in task_results.items()}
        r2_recs = {tname: res["baselines"]["r2_multiobjective_linear"]["selected_dataset_ids"] for tname, res in task_results.items()}

        h1 = evaluate_h1(task_results)
        h2 = evaluate_h2(
            task_specs=self.task_specs,
            candidate_records=self.records,
            utility_estimates_by_task=self.utility_estimates_by_task,
            r1_recommendations_by_task=r1_recs,
            r2_recommendations_by_task=r2_recs,
        )
        h3 = evaluate_h3(task_results, epsilon_tol=0.03)
        h4 = evaluate_h4(
            candidate_records=self.records,
            popularity_profiles=self.profiles,
            r3_recommendation_sets=r3_sets,
        )
        h5 = evaluate_h5(
            r3_recommendation_sets=r3_sets,
            utility_estimates_by_task=self.utility_estimates_by_task,
            popularity_profiles=self.profiles,
            fingerprints=self.fingerprints_by_dataset,
            candidate_records=self.records,
        )

        return {
            "h1_lineage_redundancy": h1,
            "h2_evidence_disambiguation": h2,
            "h3_utility_retention": h3,
            "h4_popularity_neutrality": h4,
            "h5_role_groundedness": h5,
        }

    def run_sensitivity(self) -> dict[str, Any]:
        """Execute parameter sensitivity analysis."""
        self.load_inputs()
        return evaluate_parameter_sensitivity(
            task_specs=self.task_specs,
            candidate_records=self.records,
            utility_estimates_by_task=self.utility_estimates_by_task,
            popularity_profiles=self.profiles,
            fingerprints=self.fingerprints_by_dataset,
            evidence_entries=self.evidence_by_dataset,
            config=self.config,
        )

    def run_robustness(self, baseline_output: dict[str, Any]) -> dict[str, Any]:
        """Execute 4 corruption suites and measure degradation metrics."""
        self.load_inputs()
        clean_r3_sets = {
            tname: rset
            for tname, rset in zip(EXPECTED_TASK_ORDER, baseline_output["r3_recommendation_sets"])
        }
        return evaluate_robustness(
            task_specs=self.task_specs,
            clean_records=self.records,
            clean_utility_estimates_by_task=self.utility_estimates_by_task,
            clean_recommendation_sets=clean_r3_sets,
            popularity_profiles=self.profiles,
            fingerprints=self.fingerprints_by_dataset,
            evidence_entries=self.evidence_by_dataset,
            corruption_fixtures=self.corruption_fixtures,
            ground_truth_labels=self.labels,
            config=self.config,
        )

    def run_consistency_audit(self) -> dict[str, Any]:
        """Execute M7 Pipeline Consistency Audit."""
        self.load_inputs()
        return evaluate_m7_consistency(
            task_specs=self.task_specs,
            candidate_records=self.records,
            utility_estimates_by_task=self.utility_estimates_by_task,
            popularity_profiles=self.profiles,
            fingerprints=self.fingerprints_by_dataset,
            evidence_entries=self.evidence_by_dataset,
            ground_truth_labels=self.labels,
            config=self.config,
        )

    def evaluate_all(self) -> dict[str, Any]:
        """Execute the entire evaluation harness offline in memory."""
        start_time = time.perf_counter()
        self.load_inputs()

        # 1. Run baselines
        baseline_output = self.run_baselines()

        # 2. Run ablations
        ablations = self.run_ablations()

        # 3. Run hypotheses
        hypotheses = self.run_hypotheses(baseline_output)

        # 4. Run sensitivity
        sensitivity = self.run_sensitivity()

        # 5. Run robustness
        robustness = self.run_robustness(baseline_output)

        # 6. Run consistency audit
        consistency = self.run_consistency_audit()

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        peak_rss = measure_peak_rss_bytes()

        reproducibility = build_reproducibility_record(
            config=self.config,
            wall_clock_ms=elapsed_ms,
            peak_rss_bytes=peak_rss,
        )

        return {
            "reproducibility": reproducibility,
            "baselines": baseline_output["task_results"],
            "ablation_ladder": ablations,
            "hypotheses": hypotheses,
            "sensitivity": sensitivity,
            "robustness": robustness,
            "consistency_audit": consistency,
        }
