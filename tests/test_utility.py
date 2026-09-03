"""Unit tests for Milestone 5 Task Utility Estimation.

Tests are 100% offline, deterministic, and verify TaskSpecification immutability,
the seven utility component dimensions, the slice-bias rule, hard gating,
Baselines A/B/C separation, and the categorical uncertainty model.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evidence.ledger import LedgerEntry
from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.utility.components import (
    UtilityComponent,
    score_access_feasibility,
    score_governance_compatibility,
    score_modality_compatibility,
    score_quality_compatibility,
    score_structural_compatibility,
    score_target_compatibility,
    score_task_compatibility,
)
from dataset_intelligence.utility.estimator import (
    DEFAULT_WEIGHTS,
    TaskUtilityEstimate,
    TaskUtilityEstimator,
    compute_estimate_id,
)
from dataset_intelligence.utility.specification import (
    TaskSpecification,
    compute_task_id,
)
from dataset_intelligence.utility.uncertainty import (
    EPISTEMIC_STATES,
    EVIDENCE_BASES,
    StructuredUncertainty,
)

FIXTURES_PATH = ROOT / "tests" / "fixtures" / "m5_fixtures.json"
CORPUS_PATH = ROOT / "experiments" / "m1" / "results" / "development_corpus.jsonl"


class TaskSpecificationTests(unittest.TestCase):
    """Tests for TaskSpecification schema, validation, and content-addressed ID derivation."""

    def test_task_specification_immutability(self) -> None:
        spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="text",
            domain="movie_reviews",
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            spec.task_type = "regression"  # type: ignore[misc]

    def test_deterministic_task_id(self) -> None:
        id1 = compute_task_id(
            specification_version="1.0",
            task_type="classification",
            primary_modality="text",
            domain="movie_reviews",
            target_requirements={"expected_classes": 2},
            input_constraints={"max_tokens": 512},
            scale_constraints={},
            governance_constraints={"allowed_licenses": ["mit"]},
            access_constraints={"public_access_required": True},
            explicit_user_constraints={},
            unresolved_requirements=["commercial_use"],
        )
        id2 = compute_task_id(
            specification_version="1.0",
            task_type="classification",
            primary_modality="text",
            domain="movie_reviews",
            target_requirements={"expected_classes": 2},
            input_constraints={"max_tokens": 512},
            scale_constraints={},
            governance_constraints={"allowed_licenses": ["mit"]},
            access_constraints={"public_access_required": True},
            explicit_user_constraints={},
            unresolved_requirements=["commercial_use"],
        )
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("task_"))

    def test_invalid_task_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            TaskSpecification.create(task_type="invalid_quantum_computing_task")


class UtilityComponentTests(unittest.TestCase):
    """Tests for individual utility component evaluation logic."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = {
            r["identity"]["dataset_name"]: CanonicalDataset(**r)
            for r in [json.loads(l) for l in raw_lines if l.strip()]
        }

    def test_task_compatibility_exact_match(self) -> None:
        spec = TaskSpecification.create(task_type="classification", primary_modality="text")
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        comp = score_task_compatibility(rec, spec, baseline_mode="baseline_c")
        self.assertEqual(comp.score, 1.0)
        self.assertEqual(comp.epistemic_state, "known_favorable")

    def test_modality_compatibility_clash(self) -> None:
        spec = TaskSpecification.create(task_type="classification", primary_modality="image")
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        comp = score_modality_compatibility(rec, spec, baseline_mode="baseline_c")
        self.assertEqual(comp.score, 0.0)
        self.assertEqual(comp.epistemic_state, "known_unfavorable")

    def test_target_compatibility_slice_bias_rule(self) -> None:
        spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="text",
            target_requirements={"target_type": "binary", "expected_classes": 2},
        )
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        # Synthetic fingerprint with 1 observed class (mirroring Rotten Tomatoes slice)
        fp = DatasetFingerprint.create(
            dataset_id=rec.internal_id,
            primary_modality="text",
            target_diagnostics={"observed_sample_class_count": 1, "target_column_name": "label"},
            observed_at="2026-09-02T00:00:00+00:00",
        )
        comp = score_target_compatibility(rec, spec, fingerprint=fp, baseline_mode="baseline_c")
        self.assertEqual(comp.score, 0.8)
        self.assertEqual(comp.epistemic_state, "sample_limited_inference")
        self.assertEqual(comp.evidence_basis, "bounded_sample")
        self.assertIn("slice bias", comp.explanation.lower())

    def test_structural_constraints_text_length(self) -> None:
        spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="text",
            input_constraints={"max_tokens": 100},
        )
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        fp = DatasetFingerprint.create(
            dataset_id=rec.internal_id,
            primary_modality="text",
            modality_details={"word_count_distribution": {"max": 38, "mean": 16.5}},
            observed_at="2026-09-02T00:00:00+00:00",
        )
        comp = score_structural_compatibility(rec, spec, fingerprint=fp, baseline_mode="baseline_c")
        self.assertEqual(comp.score, 1.0)
        self.assertEqual(comp.epistemic_state, "known_favorable")

    def test_quality_compatibility_penalties(self) -> None:
        spec = TaskSpecification.create(task_type="classification", primary_modality="tabular")
        rec = self.records["iris"]
        fp = DatasetFingerprint.create(
            dataset_id=rec.internal_id,
            primary_modality="tabular",
            quality_heuristics={"overall_null_rate": 0.1, "duplicate_record_rate": 0.05, "constant_columns": ["col_x"]},
            observed_at="2026-09-02T00:00:00+00:00",
        )
        comp = score_quality_compatibility(rec, spec, fingerprint=fp, baseline_mode="baseline_c")
        self.assertAlmostEqual(comp.score, 0.8, places=2)
        self.assertEqual(comp.epistemic_state, "known_favorable")

    def test_governance_and_access_separation(self) -> None:
        spec = TaskSpecification.create(task_type="classification", primary_modality="text")
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        # Rotten Tomatoes has MIT license metadata; pair with a failed HTTP 502 sample fingerprint
        fp = DatasetFingerprint.create(
            dataset_id=rec.internal_id,
            primary_modality="failed",
            sample_scope={"error_reason": "HTTP 502"},
            observed_at="2026-09-02T00:00:00+00:00",
        )
        c_gov = score_governance_compatibility(rec, spec, fingerprint=fp, baseline_mode="baseline_c")
        c_acc = score_access_feasibility(rec, spec, fingerprint=fp, baseline_mode="baseline_c")

        self.assertEqual(c_gov.score, 1.0)
        self.assertEqual(c_gov.epistemic_state, "known_favorable")
        self.assertEqual(c_acc.score, 0.2)
        self.assertEqual(c_acc.epistemic_state, "failed")


class HardGatingAndUncertaintyTests(unittest.TestCase):
    """Tests for hard-gating rules and non-numerical StructuredUncertainty."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = {
            r["identity"]["dataset_name"]: CanonicalDataset(**r)
            for r in [json.loads(l) for l in raw_lines if l.strip()]
        }
        self.estimator = TaskUtilityEstimator()

    def test_hard_gating_on_modality_clash(self) -> None:
        spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="image",
        )
        rec = self.records["iris"]  # Confirmed tabular
        est = self.estimator.evaluate(rec, spec, baseline_mode="baseline_c")
        self.assertTrue(est.hard_gated)
        self.assertEqual(est.composite_utility, 0.0)
        self.assertIsNotNone(est.gating_reason)

    def test_no_hard_gating_on_soft_mismatch(self) -> None:
        spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="text",
            domain="movie_reviews",
        )
        rec = self.records["fancyzhx/ag_news"]  # Text, but news domain
        est = self.estimator.evaluate(rec, spec, baseline_mode="baseline_c")
        self.assertFalse(est.hard_gated)
        self.assertTrue(est.composite_utility > 0.0)

    def test_structured_uncertainty_fields_and_no_confidence(self) -> None:
        spec = TaskSpecification.create(task_type="classification", primary_modality="text")
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        est = self.estimator.evaluate(rec, spec, baseline_mode="baseline_c")

        unc = est.uncertainty
        self.assertIsInstance(unc, StructuredUncertainty)
        self.assertIsInstance(unc.uncertainty_states, tuple)
        self.assertIsInstance(unc.uncertainty_reasons, tuple)
        self.assertFalse(hasattr(unc, "uncertainty_mass"))
        self.assertFalse(hasattr(unc, "confidence"))
        for comp in est.components.values():
            self.assertFalse(hasattr(comp, "confidence"))


class BaselineAblationTests(unittest.TestCase):
    """Tests verifying Baseline A, B, and C behavioral distinctions and serialization."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = {
            r["identity"]["dataset_name"]: CanonicalDataset(**r)
            for r in [json.loads(l) for l in raw_lines if l.strip()]
        }
        self.estimator = TaskUtilityEstimator()

    def test_baseline_a_b_c_distinctions(self) -> None:
        spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="text",
            governance_constraints={"allowed_licenses": ["mit"]},
        )
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        entry_conflict = LedgerEntry.create(
            dataset_id=rec.internal_id,
            claim_type="license",
            claim_value="https://opensource.org/licenses/MIT",
            evidence_type="croissant_claim",
            source="huggingface",
            source_field="croissant.license",
            observation_state="single_source_claim",
            procedure="croissant_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        fp = DatasetFingerprint.create(
            dataset_id=rec.internal_id,
            primary_modality="text",
            quality_heuristics={"overall_null_rate": 0.0, "duplicate_record_rate": 0.0},
            observed_at="2026-09-02T00:00:00+00:00",
        )

        est_a = self.estimator.evaluate(rec, spec, baseline_mode="baseline_a")
        est_b = self.estimator.evaluate(rec, spec, m3_entries=[entry_conflict], baseline_mode="baseline_b")
        est_c = self.estimator.evaluate(rec, spec, m3_entries=[entry_conflict], fingerprint=fp, baseline_mode="baseline_c")

        self.assertEqual(est_a.baseline_mode, "baseline_a")
        self.assertEqual(est_b.baseline_mode, "baseline_b")
        self.assertEqual(est_c.baseline_mode, "baseline_c")

        # Baseline A naively trusts card -> gov = 1.0; Baseline B/C surface conflict -> gov = 0.5
        self.assertEqual(est_a.components["governance_compatibility"].score, 1.0)
        self.assertEqual(est_b.components["governance_compatibility"].score, 0.5)
        self.assertEqual(est_b.components["governance_compatibility"].epistemic_state, "conflicting")

        # Baseline C incorporates empirical quality -> quality = 1.0; Baseline B unobserved -> quality = 0.5
        self.assertEqual(est_b.components["quality_compatibility"].score, 0.5)
        self.assertEqual(est_c.components["quality_compatibility"].score, 1.0)

    def test_deterministic_serialization_roundtrip(self) -> None:
        spec = TaskSpecification.create(task_type="classification", primary_modality="text")
        rec = self.records["cornell-movie-review-data/rotten_tomatoes"]
        est = self.estimator.evaluate(rec, spec, baseline_mode="baseline_c")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "estimates.jsonl"
            out_file.write_text(json.dumps(est.as_dict()) + "\n", encoding="utf-8")

            raw = json.loads(out_file.read_text(encoding="utf-8").strip())
            self.assertEqual(raw["estimate_id"], est.estimate_id)
            self.assertEqual(raw["composite_utility"], est.composite_utility)
            self.assertEqual(len(raw["components"]), 7)


if __name__ == "__main__":
    unittest.main()
