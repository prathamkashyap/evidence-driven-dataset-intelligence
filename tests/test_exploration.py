"""Unit tests for Milestone 6 Popularity-Bias Audit and Long-Tail Exploration.

Tests are 100% offline, deterministic, and verify popularity profiling,
source-relative normalization, guarded exposure metrics, under-exposed exploration,
hidden-gem strictness, conservative family linkage, and M5 utility independence.
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

from dataset_intelligence.exploration.audit import (
    ExposureAuditor,
    compute_exposure_disparity_ratio,
    compute_mean_utility_by_stratum,
    compute_stratum_exposure_share,
    compute_utility_weighted_exposure,
)
from dataset_intelligence.exploration.family import (
    detect_family_redundancy,
    evaluate_family_linkage,
)
from dataset_intelligence.exploration.pool import (
    ExplorationCandidateSet,
    ExplorationPoolBuilder,
    check_exploration_eligibility,
    check_hidden_gem,
)
from dataset_intelligence.exploration.popularity import (
    DatasetPopularityProfile,
    build_popularity_profiles,
    compute_profile_id,
    extract_raw_popularity,
)
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.utility.estimator import TaskUtilityEstimator
from dataset_intelligence.utility.specification import TaskSpecification

CORPUS_PATH = ROOT / "experiments" / "m1" / "results" / "development_corpus.jsonl"
FIXTURES_PATH = ROOT / "tests" / "fixtures" / "m6_fixtures.json"


class PopularityProfileTests(unittest.TestCase):
    """Tests for DatasetPopularityProfile schema, immutability, and source-relative stratification."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]
        self.records_by_name = {r.identity["dataset_name"]: r for r in self.records}

    def test_profile_immutability(self) -> None:
        rec = self.records_by_name["cornell-movie-review-data/rotten_tomatoes"]
        prof = build_popularity_profiles([rec])[rec.internal_id]
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            prof.popularity_stratum = "very_low"  # type: ignore[misc]

    def test_deterministic_profile_id(self) -> None:
        id1 = compute_profile_id("1.0", "ds_1", "huggingface", {"downloads": 100}, "downloads", 100.0, "measured", "high")
        id2 = compute_profile_id("1.0", "ds_1", "huggingface", {"downloads": 100}, "downloads", 100.0, "measured", "high")
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("pop_"))

    def test_raw_popularity_preservation(self) -> None:
        rec = self.records_by_name["cornell-movie-review-data/rotten_tomatoes"]
        raw_sig, p_name, p_val, state, obs_at = extract_raw_popularity(rec)
        self.assertEqual(p_name, "downloads")
        self.assertEqual(p_val, 1200.0)
        self.assertEqual(state, "measured")
        self.assertEqual(raw_sig.get("stars"), 8)

    def test_missing_popularity_becomes_under_observed_not_zero(self) -> None:
        rec = self.records_by_name["iris"]  # OpenML Iris
        raw_sig, p_name, p_val, state, obs_at = extract_raw_popularity(rec)
        self.assertIsNone(p_name)
        self.assertIsNone(p_val)
        self.assertEqual(state, "under_observed")

        profiles = build_popularity_profiles(self.records)
        prof = profiles[rec.internal_id]
        self.assertEqual(prof.popularity_measurement_state, "under_observed")
        self.assertEqual(prof.popularity_stratum, "unknown")
        self.assertIsNone(prof.primary_metric_value)
        self.assertIsNone(prof.source_relative_percentile)

    def test_source_relative_percentile_and_strata(self) -> None:
        profiles = build_popularity_profiles(self.records)

        # Rotten Tomatoes: 1200 downloads (highest of HF) -> very_high
        rt = profiles[self.records_by_name["cornell-movie-review-data/rotten_tomatoes"].internal_id]
        self.assertEqual(rt.source_name, "huggingface")
        self.assertEqual(rt.source_relative_percentile, 1.0)
        self.assertEqual(rt.popularity_stratum, "very_high")

        # Beans: 300 downloads (lowest of HF) -> very_low
        beans = profiles[self.records_by_name["AI-Lab-Makerere/beans"].internal_id]
        self.assertEqual(beans.source_name, "huggingface")
        self.assertEqual(beans.source_relative_percentile, 0.0)
        self.assertEqual(beans.popularity_stratum, "very_low")

    def test_single_record_source_handling(self) -> None:
        # Single record in Kaggle measured population should have percentile 1.0
        kaggle_rec = self.records_by_name["Iris Species"]
        profiles = build_popularity_profiles([kaggle_rec])
        prof = profiles[kaggle_rec.internal_id]
        self.assertEqual(prof.source_relative_percentile, 1.0)
        self.assertEqual(prof.popularity_stratum, "very_high")


class GuardedExposureMetricsTests(unittest.TestCase):
    """Tests for guarded zero-denominator exposure disparity and audit calculations."""

    def test_exposure_share_basic(self) -> None:
        strata = ["very_high", "very_high", "low", "unknown"]
        self.assertEqual(compute_stratum_exposure_share(strata, "very_high"), 0.5)
        self.assertEqual(compute_stratum_exposure_share(strata, "medium"), 0.0)
        self.assertEqual(compute_stratum_exposure_share([], "very_high"), 0.0)

    def test_exposure_disparity_ratio_zero_denominator_guard(self) -> None:
        exposed = ["very_high", "very_high"]
        corpus = ["very_high", "high", "low", "unknown"]

        # Medium does not exist in corpus -> guarded not_estimable
        edr_med = compute_exposure_disparity_ratio(exposed, corpus, "medium")
        self.assertIsInstance(edr_med, str)
        self.assertIn("not_estimable", edr_med)

        # very_high exists in both -> valid ratio
        edr_vh = compute_exposure_disparity_ratio(exposed, corpus, "very_high")
        self.assertEqual(edr_vh, 4.0)

    def test_utility_weighted_exposure_zero_utility_guard(self) -> None:
        # Zero total exposed utility
        items_zero = [("very_high", 0.0), ("low", 0.0)]
        uwe_zero = compute_utility_weighted_exposure(items_zero, "very_high")
        self.assertIsInstance(uwe_zero, str)
        self.assertIn("not_estimable", uwe_zero)

        # Non-zero utility
        items_pos = [("very_high", 0.8), ("low", 0.2)]
        uwe_pos = compute_utility_weighted_exposure(items_pos, "very_high")
        self.assertEqual(uwe_pos, 0.8)

    def test_mean_utility_by_stratum_missing_guard(self) -> None:
        items = [("very_high", 0.9), ("low", 0.5)]
        mean_u = compute_mean_utility_by_stratum(items)
        self.assertEqual(mean_u["very_high"], 0.9)
        self.assertEqual(mean_u["low"], 0.5)
        self.assertIn("not_estimable", str(mean_u["medium"]))


class ConservativeFamilyLinkageTests(unittest.TestCase):
    """Tests for multi-signal conservative family linkage and redundancy detection."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]
        self.records_by_name = {r.identity["dataset_name"]: r for r in self.records}

    def test_same_family_with_multiple_signals(self) -> None:
        rec_openml_iris = self.records_by_name["iris"]
        rec_uci_iris = self.records_by_name["Iris"]

        state, signals = evaluate_family_linkage(rec_openml_iris, rec_uci_iris)
        self.assertEqual(state, "same_family")
        self.assertTrue(len(signals) >= 2)
        self.assertTrue(any("name_token_overlap" in s for s in signals))
        self.assertTrue(any("compatible_modality" in s for s in signals))

    def test_different_family_on_disjoint_modalities(self) -> None:
        rec_rt = self.records_by_name["cornell-movie-review-data/rotten_tomatoes"]  # Text
        rec_cifar = self.records_by_name["uoft-cs/cifar100"]  # Image

        state, signals = evaluate_family_linkage(rec_rt, rec_cifar)
        self.assertEqual(state, "different_family")

    def test_family_redundancy_detection(self) -> None:
        rec_openml_iris = self.records_by_name["iris"]
        rec_uci_iris = self.records_by_name["Iris"]
        rec_rt = self.records_by_name["cornell-movie-review-data/rotten_tomatoes"]

        main_pool = [rec_uci_iris, rec_rt]
        is_red, reason, match_id = detect_family_redundancy(rec_openml_iris, main_pool)
        self.assertTrue(is_red)
        self.assertEqual(match_id, rec_uci_iris.internal_id)
        self.assertIn("family_variant", str(reason))


class ExplorationPoolAndHiddenGemTests(unittest.TestCase):
    """Tests for under-exposed exploration eligibility, hidden-gem strictness, and M5 independence."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]
        self.records_by_name = {r.identity["dataset_name"]: r for r in self.records}
        self.profiles = build_popularity_profiles(self.records)
        self.estimator = TaskUtilityEstimator()

    def test_under_observed_cannot_become_hidden_gem(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
            domain="botany",
            target_requirements={"expected_classes": 3},
        )
        rec_openml_iris = self.records_by_name["iris"]
        u_est = self.estimator.evaluate(rec_openml_iris, task_spec, baseline_mode="baseline_c")
        prof = self.profiles[rec_openml_iris.internal_id]

        # OpenML Iris has unmeasured popularity -> under_observed
        self.assertEqual(prof.popularity_measurement_state, "under_observed")

        # Must NOT be designated a hidden gem
        is_gem, desig, explanation = check_hidden_gem(prof, u_est, is_family_variant=False)
        self.assertFalse(is_gem)
        self.assertEqual(desig, "under_observed_high_utility")
        self.assertIn("cannot be designated a hidden gem", explanation)

    def test_measured_low_popularity_can_become_hidden_gem(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="image",
            domain="botany",
        )
        rec_beans = self.records_by_name["AI-Lab-Makerere/beans"]
        prof = self.profiles[rec_beans.internal_id]
        self.assertEqual(prof.popularity_stratum, "very_low")

        # Case 1: Beans with failed HTTP 502 sample fingerprint fails access condition
        from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
        fp_failed = DatasetFingerprint.create(
            dataset_id=rec_beans.internal_id,
            primary_modality="failed",
            sample_scope={"error_reason": "HTTP 502"},
            observed_at="2026-09-02T00:00:00+00:00",
        )
        u_est_failed = self.estimator.evaluate(rec_beans, task_spec, fingerprint=fp_failed, baseline_mode="baseline_c")
        is_gem, desig, _ = check_hidden_gem(prof, u_est_failed, is_family_variant=False)
        self.assertFalse(is_gem)
        self.assertEqual(desig, "insufficient_access")

        # Case 2: Synthetic measured low-popularity profile on high-utility dataset becomes hidden gem
        rec_cifar = self.records_by_name["uoft-cs/cifar100"]
        task_cifar = TaskSpecification.create(task_type="classification", primary_modality="image")
        u_est_cifar = self.estimator.evaluate(rec_cifar, task_cifar, baseline_mode="baseline_c")

        prof_low = DatasetPopularityProfile(
            profile_id="pop_synth_low",
            profile_version="1.0",
            dataset_id=rec_cifar.internal_id,
            source_name="huggingface",
            raw_signals={"downloads": 5},
            primary_metric_name="downloads",
            primary_metric_value=5.0,
            popularity_measurement_state="measured",
            source_relative_percentile=0.05,
            popularity_stratum="very_low",
            observed_at="2026-09-02T00:00:00+00:00",
            provenance={},
        )
        is_gem_2, desig_2, _ = check_hidden_gem(prof_low, u_est_cifar, is_family_variant=False)
        self.assertTrue(is_gem_2)
        self.assertEqual(desig_2, "hidden_gem")

    def test_exploration_pool_builder_bounds_and_filtering(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
            domain="botany",
        )
        builder = ExplorationPoolBuilder()

        # Synthetic M2 retrieval top-3 containing UCI Iris, OpenML Wine, UCI Wine
        retrieved_ids = [
            self.records_by_name["Iris"].internal_id,
            self.records_by_name["wine"].internal_id,
            self.records_by_name["Wine"].internal_id,
        ]

        u_estimates = {
            rec.internal_id: self.estimator.evaluate(rec, task_spec, baseline_mode="baseline_c")
            for rec in self.records
        }

        exp_set = builder.build_exploration_set(
            task_id=task_spec.task_id,
            query_id="q_tabular_flower",
            retrieved_dataset_ids=retrieved_ids,
            corpus_records=self.records,
            popularity_profiles=self.profiles,
            utility_estimates=u_estimates,
        )

        self.assertIsInstance(exp_set, ExplorationCandidateSet)
        self.assertEqual(len(exp_set.main_pool_dataset_ids), 3)
        self.assertTrue(len(exp_set.selected_exploration_dataset_ids) <= 5)
        # OpenML Iris is identified as a family variant of UCI Iris
        openml_iris_id = self.records_by_name["iris"].internal_id
        self.assertIn(openml_iris_id, exp_set.redundant_family_variants)

    def test_m5_utility_independence_invariant(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="text",
            domain="movie_reviews",
        )
        rec = self.records_by_name["cornell-movie-review-data/rotten_tomatoes"]

        # Evaluate M5 utility directly
        u_before = self.estimator.evaluate(rec, task_spec, baseline_mode="baseline_c")

        # Build popularity profile
        prof = self.profiles[rec.internal_id]

        # Evaluate M5 utility after popularity profiling
        u_after = self.estimator.evaluate(rec, task_spec, baseline_mode="baseline_c")

        self.assertEqual(u_before.composite_utility, u_after.composite_utility)
        self.assertEqual(u_before.estimate_id, u_after.estimate_id)


if __name__ == "__main__":
    unittest.main()
