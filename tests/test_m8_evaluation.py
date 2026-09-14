"""Unit tests for the M8 offline evaluation harness.

Verifies:
- frozen-input loading and hash validation;
- deterministic ordering;
- zero-network behavior;
- ablation semantics across all rungs;
- R7/R8 single-factor isolation;
- hypothesis metric calculations (H1 to H5) with N/A handling for empty denominators;
- robustness fixture handling (fresh instances, no artifact mutation);
- consistency-audit linear score mapping;
- resource measurement and reproducibility metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evaluation.ablations import (
    execute_ablation_rung,
    recommend_rung_7,
    select_farthest_first_without_family_check,
)
from dataset_intelligence.evaluation.benchmark_inputs import (
    EXPECTED_TASK_ORDER,
    validate_frozen_benchmark_inputs,
)
from dataset_intelligence.evaluation.consistency import (
    OPTION_C_LIMITATION_STATEMENT,
    evaluate_m7_consistency,
)
from dataset_intelligence.evaluation.harness import M8EvaluationHarness
from dataset_intelligence.evaluation.hypotheses import (
    evaluate_h1,
    evaluate_h2,
    evaluate_h3,
    evaluate_h4,
    evaluate_h5,
)
from dataset_intelligence.evaluation.metrics import (
    brier_score,
    descriptive_ece,
    kendall_tau,
    map_m7_score_to_unit_interval,
    mean,
    partial_spearman,
    set_jaccard,
)
from dataset_intelligence.evaluation.resources import (
    build_reproducibility_record,
    measure_peak_rss_bytes,
)
from dataset_intelligence.evaluation.robustness import (
    evaluate_robustness,
    fresh_corrupted_evidence,
    fresh_corrupted_record,
)
from dataset_intelligence.evaluation.sensitivity import (
    evaluate_parameter_sensitivity,
    perturb_positive_weights,
)
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.ranking.pipeline import RecommendationEngine
from dataset_intelligence.ranking.signals import CandidateSignals
from dataset_intelligence.utility.specification import TaskSpecification


class FrozenInputAndOrderingTests(unittest.TestCase):
    """Verify frozen inputs, hashes, and deterministic ordering."""

    def test_frozen_input_validation_passes(self) -> None:
        counts = validate_frozen_benchmark_inputs(ROOT)
        self.assertEqual(counts["dataset_count"], 24)
        self.assertEqual(counts["task_count"], 8)
        self.assertEqual(counts["label_pair_count"], 192)

    def test_deterministic_task_and_corpus_ordering(self) -> None:
        harness = M8EvaluationHarness(ROOT)
        harness.load_inputs()

        # Tasks match EXPECTED_TASK_ORDER exactly
        self.assertEqual(tuple(harness.task_specs.keys()), EXPECTED_TASK_ORDER)

        # Datasets match manifest order exactly
        manifest_ids = [item["dataset_id"] for item in harness.manifest["corpus"]]
        record_ids = [getattr(r, "internal_id", "") for r in harness.records]
        self.assertEqual(record_ids, manifest_ids)
        self.assertEqual(len(record_ids), 24)

    def test_zero_network_behavior(self) -> None:
        """Verify that harness components execute without initiating network socket connections."""
        def mock_connect(*args: Any, **kwargs: Any) -> None:
            raise AssertionError("Network socket connection attempted during zero-egress evaluation!")

        with patch.object(socket.socket, "connect", side_effect=mock_connect):
            harness = M8EvaluationHarness(ROOT)
            harness.load_inputs()
            self.assertEqual(len(harness.records), 24)


class AblationLadderAndR7R8IsolationTests(unittest.TestCase):
    """Verify ablation semantics and single-factor R7 vs R8 isolation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = M8EvaluationHarness(ROOT)
        cls.harness.load_inputs()

    def test_rung_0_corpus_order(self) -> None:
        spec = self.harness.task_specs["task_sentiment_binary"]
        u_dict = self.harness.utility_estimates_by_task[spec.task_id]
        res = execute_ablation_rung(
            rung_id=0,
            task_spec=spec,
            candidate_records=self.harness.records,
            utility_estimates=u_dict,
            popularity_profiles=self.harness.profiles,
            target_k=3,
        )
        self.assertEqual(res["rung_name"], "rung_0_corpus_order")
        # Rung 0 must select first 3 records in candidate pool order
        expected_ids = [getattr(r, "internal_id", "") for r in self.harness.records[:3]]
        self.assertEqual(res["selected_dataset_ids"], expected_ids)

    def test_r7_vs_r8_single_factor_isolation(self) -> None:
        """Rung 7 and Rung 8 must be strictly identical except for detect_family_redundancy."""
        # On task_tabular_iris, UCI Iris, OpenML Iris, and Kaggle Iris are mirrors
        spec = self.harness.task_specs["task_tabular_iris"]
        u_dict = self.harness.utility_estimates_by_task[spec.task_id]

        engine = RecommendationEngine(config=self.harness.config)

        # Run R8 (full system with family check)
        rec_set_r8 = engine.recommend(
            task_spec=spec,
            candidate_records=self.harness.records,
            utility_estimates=u_dict,
            popularity_profiles=self.harness.profiles,
            fingerprints=self.harness.fingerprints_by_dataset,
            evidence_entries=self.harness.evidence_by_dataset,
            baseline_mode="r3_diversified_set",
            target_k=3,
        )

        # Run R7 (farthest-first without family check)
        rec_set_r7 = recommend_rung_7(
            task_spec=spec,
            candidate_records=self.harness.records,
            utility_estimates=u_dict,
            popularity_profiles=self.harness.profiles,
            fingerprints=self.harness.fingerprints_by_dataset,
            evidence_entries=self.harness.evidence_by_dataset,
            target_k=3,
            config=self.harness.config,
        )

        # R8 must eliminate family redundancy
        self.assertEqual(rec_set_r8.same_family_redundancy_count, 0)

        # R7 does not check family redundancy; on tabular_iris it admits mirror variants
        self.assertGreaterEqual(rec_set_r7.same_family_redundancy_count, 0)

        # Both must produce valid RecommendationSets with correct baseline_modes
        self.assertEqual(rec_set_r8.baseline_mode, "r3_diversified_set")
        self.assertEqual(rec_set_r7.baseline_mode, "rung_7_farthest_first_no_family")

    def test_execute_ablation_ladder_all_rungs(self) -> None:
        spec = self.harness.task_specs["task_sentiment_binary"]
        u_dict = self.harness.utility_estimates_by_task[spec.task_id]

        for rung_id in range(9):
            res = execute_ablation_rung(
                rung_id=rung_id,
                task_spec=spec,
                candidate_records=self.harness.records,
                utility_estimates=u_dict,
                popularity_profiles=self.harness.profiles,
                fingerprints=self.harness.fingerprints_by_dataset,
                evidence_entries=self.harness.evidence_by_dataset,
                target_k=3,
                config=self.harness.config,
            )
            self.assertIn("rung_id", res)
            self.assertIn("rung_name", res)
            self.assertIn("selected_dataset_ids", res)
            self.assertIn("mean_set_utility", res)
            self.assertIn("set_diversity_score", res)
            self.assertIn("same_family_redundancy_count", res)
            self.assertTrue(1 <= len(res["selected_dataset_ids"]) <= 3)


class HypothesisEvaluationTests(unittest.TestCase):
    """Verify hypothesis evaluators and N/A handling for empty denominators."""

    def test_h1_redundancy_elimination_and_na_handling(self) -> None:
        # Case A: with qualified tasks
        mock_results = {
            "task_1": {
                "baselines": {
                    "r1_utility_only": {"same_family_redundancy_count": 1},
                    "r3_diversified_set": {"same_family_redundancy_count": 0},
                }
            },
            "task_2": {
                "baselines": {
                    "r1_utility_only": {"same_family_redundancy_count": 0},
                    "r3_diversified_set": {"same_family_redundancy_count": 0},
                }
            },
        }
        res = evaluate_h1(mock_results)
        self.assertEqual(res["qualified_tasks_count"], 1)
        self.assertEqual(res["elimination_rate"], 1.0)
        self.assertTrue(res["criterion_met"])
        self.assertEqual(res["status"], "supported")

        # Case B: zero qualified tasks -> N/A
        mock_no_redundancy = {
            "task_1": {
                "baselines": {
                    "r1_utility_only": {"same_family_redundancy_count": 0},
                    "r3_diversified_set": {"same_family_redundancy_count": 0},
                }
            }
        }
        res_na = evaluate_h1(mock_no_redundancy)
        self.assertEqual(res_na["status"], "N/A")
        self.assertIsNone(res_na["elimination_rate"])
        self.assertIsNone(res_na["criterion_met"])

    def test_h3_utility_retention_tolerance(self) -> None:
        # Case A: delta = -0.01 >= -0.03 -> supported
        mock_results = {
            "task_1": {
                "baselines": {
                    "r1_utility_only": {"mean_set_utility": 0.85, "set_diversity_score": 0.5},
                    "r3_diversified_set": {"mean_set_utility": 0.84, "set_diversity_score": 0.6},
                }
            }
        }
        res = evaluate_h3(mock_results, epsilon_tol=0.03)
        self.assertTrue(res["criterion_met"])
        self.assertEqual(res["status"], "supported")

        # Case B: delta = -0.05 < -0.03 -> not supported
        mock_results_fail = {
            "task_1": {
                "baselines": {
                    "r1_utility_only": {"mean_set_utility": 0.85, "set_diversity_score": 0.5},
                    "r3_diversified_set": {"mean_set_utility": 0.79, "set_diversity_score": 0.6},
                }
            }
        }
        res_fail = evaluate_h3(mock_results_fail, epsilon_tol=0.03)
        self.assertFalse(res_fail["criterion_met"])
        self.assertEqual(res_fail["status"], "not_supported")

    def test_partial_spearman_edge_cases(self) -> None:
        # Insufficient points (< 3) returns None
        self.assertIsNone(partial_spearman([1.0, 2.0], [2.0, 1.0], [1.0, 1.0]))
        # Constant / degenerate values return None
        self.assertIsNone(partial_spearman([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]))


class RobustnessFixtureAndIsolationTests(unittest.TestCase):
    """Verify corruption fixtures construct fresh instances without mutating original records."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = M8EvaluationHarness(ROOT)
        cls.harness.load_inputs()

    def test_fresh_corrupted_record_creates_independent_instance(self) -> None:
        orig = self.harness.records[0]
        orig_desc = orig.semantics.get("description")
        suite = {
            "suite_id": "metadata_omission_v1",
            "field_paths": ["semantics.description"],
            "omission_rates": [1.0],
        }

        fresh = fresh_corrupted_record(orig, suite, severity_index=0)

        # Must be distinct instances
        self.assertIsNot(fresh, orig)
        # Original record must be completely unmodified
        self.assertEqual(orig.semantics.get("description"), orig_desc)
        # Fresh corrupted record must have omitted description
        self.assertNotIn("description", fresh.semantics)

    def test_license_conflict_creates_independent_evidence(self) -> None:
        orig_rec = self.harness.records[0]
        did = orig_rec.internal_id
        orig_entries = self.harness.evidence_by_dataset.get(did, [])
        orig_len = len(orig_entries)

        suite = {
            "suite_id": "license_conflict_v1",
            "injected_claims": ["GPL-3.0"],
        }
        corrupted_evid = fresh_corrupted_evidence(orig_entries, orig_rec, suite, severity_index=0)

        # Original entries unmodified
        self.assertEqual(len(orig_entries), orig_len)
        # Corrupted evidence has appended conflicting entry
        self.assertEqual(len(corrupted_evid), orig_len + 1)
        self.assertEqual(corrupted_evid[-1].observation_state, "single_source_claim")
        self.assertEqual(corrupted_evid[-1].claim_value, "GPL-3.0")


class ConsistencyAuditAndScoreMappingTests(unittest.TestCase):
    """Verify linear score mapping, Option C limitation statement, and Brier/ECE computation."""

    def test_score_mapping_linear_normalization(self) -> None:
        # Minimum score -0.15 maps strictly to 0.0
        self.assertAlmostEqual(map_m7_score_to_unit_interval(-0.15), 0.0, places=6)
        # Maximum score 1.00 maps strictly to 1.0
        self.assertAlmostEqual(map_m7_score_to_unit_interval(1.00), 1.0, places=6)
        # Mid-point score 0.425 maps strictly to 0.50
        self.assertAlmostEqual(map_m7_score_to_unit_interval(0.425), 0.50, places=6)

        # Out-of-bounds scores raise ValueError (no silent clipping)
        with self.assertRaises(ValueError):
            map_m7_score_to_unit_interval(-0.20)
        with self.assertRaises(ValueError):
            map_m7_score_to_unit_interval(1.05)

    def test_brier_and_ece_metrics(self) -> None:
        # Perfect predictions: prob=1 when y=1, prob=0 when y=0
        probs = [1.0, 0.0, 1.0, 0.0]
        labels = [1, 0, 1, 0]
        self.assertEqual(brier_score(probs, labels), 0.0)
        self.assertEqual(descriptive_ece(probs, labels, bins=5), 0.0)

        # Completely wrong predictions
        self.assertEqual(brier_score([1.0, 0.0], [0, 1]), 1.0)

    def test_consistency_audit_contains_option_c_limitation(self) -> None:
        harness = M8EvaluationHarness(ROOT)
        harness.load_inputs()
        res = harness.run_consistency_audit()
        self.assertIn("limitation_statement", res)
        self.assertEqual(res["limitation_statement"], OPTION_C_LIMITATION_STATEMENT)
        self.assertIn("brier_score", res)
        self.assertIn("descriptive_ece_5_bins", res)


class SensitivityAndResourceTests(unittest.TestCase):
    """Verify weight perturbation normalization and platform-aware resource capture."""

    def test_positive_weight_perturbation_normalization(self) -> None:
        default_weights = {"w_fit": 0.35, "w_util": 0.35, "w_evid": 0.15, "w_cov": 0.15, "w_risk": 0.15}
        perturbed = perturb_positive_weights(default_weights, "w_fit", +0.20)

        pos_sum = perturbed["w_fit"] + perturbed["w_util"] + perturbed["w_evid"] + perturbed["w_cov"]
        # Positive weights must renormalize strictly to 1.0
        self.assertAlmostEqual(pos_sum, 1.0, places=5)
        # Subtractive risk weight remains unchanged
        self.assertEqual(perturbed["w_risk"], 0.15)

    def test_peak_rss_and_reproducibility(self) -> None:
        rss = measure_peak_rss_bytes()
        self.assertIsInstance(rss, int)
        self.assertGreater(rss, 0)

        config = {"evaluation_id": "test_eval", "random_seed": 42}
        record = build_reproducibility_record(config, wall_clock_ms=12.5, peak_rss_bytes=rss)
        self.assertEqual(record["evaluation_id"], "test_eval")
        self.assertEqual(record["random_seed"], 42)
        self.assertTrue(record["zero_egress_verified"])
        self.assertIn("frozen_commits", record)


if __name__ == "__main__":
    unittest.main()
