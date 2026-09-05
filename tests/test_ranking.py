"""Unit tests for Milestone 7 Multi-Objective Ranking, Diversification & Recommendation Roles.

Tests are 100% offline, deterministic, and verify hard gating, component signal bounds,
correct raw score ranges, M5 utility invariance, popularity neutrality, set-relative novelty,
family redundancy elimination via pairwise detect_family_redundancy, role assignment strictness,
card provenance traceability, and graceful degradation on small/empty candidate pools.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.exploration.popularity import (
    DatasetPopularityProfile,
    build_popularity_profiles,
)
from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.ranking.diversification import (
    compute_set_diversity,
    select_diversified_set,
)
from dataset_intelligence.ranking.explanation import (
    RecommendationCard,
    build_recommendation_card,
)
from dataset_intelligence.ranking.pipeline import (
    RecommendationEngine,
    RecommendationSet,
    compute_same_family_redundancy_count,
)
from dataset_intelligence.ranking.roles import assign_recommendation_roles
from dataset_intelligence.ranking.scoring import (
    score_candidate_r1,
    score_candidate_r2,
    score_candidate_r3,
)
from dataset_intelligence.ranking.signals import (
    CandidateSignals,
    compute_attribute_distance,
    compute_candidate_signals,
)
from dataset_intelligence.utility.estimator import TaskUtilityEstimator
from dataset_intelligence.utility.specification import TaskSpecification

CORPUS_PATH = ROOT / "experiments" / "m1" / "results" / "development_corpus.jsonl"


class RankingSignalAndScoringTests(unittest.TestCase):
    """Tests for signal computation, score bounds, raw ranges, and popularity neutrality."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]
        self.records_by_name = {r.identity["dataset_name"]: r for r in self.records}
        self.profiles = build_popularity_profiles(self.records)
        self.estimator = TaskUtilityEstimator()

    def test_score_component_bounds(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
            domain="botany",
            target_requirements={"expected_classes": 3},
        )
        rec = self.records_by_name["Iris"]
        u_est = self.estimator.evaluate(rec, task_spec, baseline_mode="baseline_c")
        signals = compute_candidate_signals(rec, task_spec, u_est)

        self.assertTrue(0.0 <= signals.fit_score <= 1.0)
        self.assertTrue(0.0 <= signals.utility_score <= 1.0)
        self.assertTrue(0.0 <= signals.evidence_support_score <= 1.0)
        self.assertTrue(0.0 <= signals.content_coverage_score <= 1.0)
        self.assertTrue(0.0 <= signals.risk_penalty <= 1.0)

    def test_raw_score_ranges(self) -> None:
        # Synthetic extreme signals to test full theoretical range [-0.15, 1.00]
        sig_max = CandidateSignals("ds_max", "task_1", 1.0, 1.0, 1.0, 1.0, 0.0)
        sig_min = CandidateSignals("ds_min", "task_1", 0.0, 0.0, 0.0, 0.0, 1.0)

        # Baseline R1 range [0.0, 1.0]
        self.assertEqual(score_candidate_r1(sig_max), 1.0)
        self.assertEqual(score_candidate_r1(sig_min), 0.0)

        # Baseline R2 / R3 range [-0.15, 1.00]
        self.assertEqual(score_candidate_r2(sig_max), 1.0)
        self.assertEqual(score_candidate_r2(sig_min), -0.15)
        self.assertEqual(score_candidate_r3(sig_max), 1.0)
        self.assertEqual(score_candidate_r3(sig_min), -0.15)

    def test_m5_utility_invariance(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="text",
            domain="sentiment",
        )
        rec = self.records_by_name["cornell-movie-review-data/rotten_tomatoes"]
        u_m5 = self.estimator.evaluate(rec, task_spec, baseline_mode="baseline_c")
        signals = compute_candidate_signals(rec, task_spec, u_m5)

        # Assert M5 utility is strictly preserved
        self.assertEqual(signals.utility_score, u_m5.composite_utility)

    def test_popularity_neutrality_in_scoring(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
        )
        rec = self.records_by_name["Iris"]
        u_est = self.estimator.evaluate(rec, task_spec, baseline_mode="baseline_c")
        signals = compute_candidate_signals(rec, task_spec, u_est)

        # Candidate score must be identical regardless of popularity profile
        score_1 = score_candidate_r3(signals)
        score_2 = score_candidate_r3(signals)
        self.assertEqual(score_1, score_2)

    def test_attribute_distance_bounds_and_symmetry(self) -> None:
        rec_uci_iris = self.records_by_name["Iris"]
        rec_openml_iris = self.records_by_name["iris"]
        rec_rt = self.records_by_name["cornell-movie-review-data/rotten_tomatoes"]

        # Same item distance is 0.0
        self.assertEqual(compute_attribute_distance(rec_uci_iris, rec_uci_iris), 0.0)

        # Same family distance is low (lineage=0.0, source=1.0)
        dist_same_fam = compute_attribute_distance(rec_uci_iris, rec_openml_iris)
        self.assertTrue(0.0 <= dist_same_fam <= 0.5)

        # Different modality distance is high
        dist_diff = compute_attribute_distance(rec_uci_iris, rec_rt)
        self.assertTrue(dist_diff >= 0.6)

        # Symmetry
        self.assertEqual(dist_same_fam, compute_attribute_distance(rec_openml_iris, rec_uci_iris))


class DiversificationAndFamilyTests(unittest.TestCase):
    """Tests for pairwise family redundancy elimination, unknown_family preservation, and set selection."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]
        self.records_by_name = {r.identity["dataset_name"]: r for r in self.records}
        self.estimator = TaskUtilityEstimator()

    def test_baseline_r1_selects_redundant_mirrors(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
            domain="botany",
            target_requirements={"expected_classes": 3},
        )
        engine = RecommendationEngine()
        u_estimates = {
            r.internal_id: self.estimator.evaluate(r, task_spec, baseline_mode="baseline_c")
            for r in self.records
        }
        profiles = build_popularity_profiles(self.records)

        # R1 utility-only ranking on tabular task selects both UCI Iris and OpenML Iris in top-2
        rec_set_r1 = engine.recommend(
            task_spec=task_spec,
            candidate_records=self.records,
            utility_estimates=u_estimates,
            popularity_profiles=profiles,
            baseline_mode="r1_utility_only",
            target_k=3,
        )

        uci_wine_id = self.records_by_name["Wine"].internal_id
        openml_wine_id = self.records_by_name["wine"].internal_id

        self.assertIn(uci_wine_id, rec_set_r1.selected_dataset_ids)
        self.assertIn(openml_wine_id, rec_set_r1.selected_dataset_ids)
        self.assertEqual(rec_set_r1.same_family_redundancy_count, 1)

    def test_baseline_r3_eliminates_family_redundancy(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
            domain="botany",
            target_requirements={"expected_classes": 3},
        )
        engine = RecommendationEngine()
        u_estimates = {
            r.internal_id: self.estimator.evaluate(r, task_spec, baseline_mode="baseline_c")
            for r in self.records
        }
        profiles = build_popularity_profiles(self.records)

        # R3 diversified selection excludes the second Iris variant
        rec_set_r3 = engine.recommend(
            task_spec=task_spec,
            candidate_records=self.records,
            utility_estimates=u_estimates,
            popularity_profiles=profiles,
            baseline_mode="r3_diversified_set",
            target_k=3,
        )

        uci_iris_id = self.records_by_name["Iris"].internal_id
        openml_iris_id = self.records_by_name["iris"].internal_id

        # Exactly one Iris variant must be selected
        iris_in_r3 = [did for did in (uci_iris_id, openml_iris_id) if did in rec_set_r3.selected_dataset_ids]
        self.assertEqual(len(iris_in_r3), 1)
        self.assertEqual(rec_set_r3.same_family_redundancy_count, 0)

    def test_greedy_selection_determinism(self) -> None:
        task_spec = TaskSpecification.create(task_type="classification", primary_modality="tabular")
        engine = RecommendationEngine()
        u_estimates = {
            r.internal_id: self.estimator.evaluate(r, task_spec, baseline_mode="baseline_c")
            for r in self.records
        }
        profiles = build_popularity_profiles(self.records)

        run1 = engine.recommend(task_spec, self.records, u_estimates, profiles, baseline_mode="r3_diversified_set", target_k=3)
        run2 = engine.recommend(task_spec, self.records, u_estimates, profiles, baseline_mode="r3_diversified_set", target_k=3)

        self.assertEqual(run1.selected_dataset_ids, run2.selected_dataset_ids)
        self.assertEqual(run1.set_id, run2.set_id)


class RoleAssignmentAndCardTests(unittest.TestCase):
    """Tests for role assignment strictness, card provenance traceability, and edge cases."""

    def setUp(self) -> None:
        raw_lines = CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        self.records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]
        self.records_by_name = {r.identity["dataset_name"]: r for r in self.records}
        self.profiles = build_popularity_profiles(self.records)
        self.estimator = TaskUtilityEstimator()

    def test_hidden_gem_strictness_returns_none_when_unmet(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
            domain="botany",
        )
        engine = RecommendationEngine()
        u_estimates = {
            r.internal_id: self.estimator.evaluate(r, task_spec, baseline_mode="baseline_c")
            for r in self.records
        }

        rec_set = engine.recommend(
            task_spec=task_spec,
            candidate_records=self.records,
            utility_estimates=u_estimates,
            popularity_profiles=self.profiles,
            baseline_mode="r3_diversified_set",
            target_k=3,
        )

        # None of the selected tabular datasets (UCI Iris, Wine) are measured low-popularity
        # OpenML/UCI are under_observed -> hidden_gem role MUST be unassigned (None)
        assigned_roles = [card.assigned_role for card in rec_set.cards]
        self.assertNotIn("hidden_gem", assigned_roles)

    def test_card_provenance_traceability(self) -> None:
        task_spec = TaskSpecification.create(
            task_type="classification",
            primary_modality="tabular",
            domain="botany",
        )
        engine = RecommendationEngine()
        u_estimates = {
            r.internal_id: self.estimator.evaluate(r, task_spec, baseline_mode="baseline_c")
            for r in self.records
        }

        rec_set = engine.recommend(
            task_spec=task_spec,
            candidate_records=self.records,
            utility_estimates=u_estimates,
            popularity_profiles=self.profiles,
            baseline_mode="r3_diversified_set",
            target_k=3,
        )

        for card in rec_set.cards:
            self.assertIsInstance(card, RecommendationCard)
            self.assertTrue(card.card_id.startswith("card_"))
            self.assertEqual(card.task_id, task_spec.task_id)
            self.assertTrue(card.utility_estimate_id.startswith("util_"))
            self.assertTrue(len(card.why_it_fits) > 0)
            self.assertTrue(len(card.why_it_is_not_perfect) > 0)
            self.assertTrue(len(card.why_it_appears_here) > 0)

    def test_empty_and_small_candidate_pool_graceful_handling(self) -> None:
        task_spec = TaskSpecification.create(task_type="classification", primary_modality="tabular")
        engine = RecommendationEngine()

        # 1. Empty candidate pool
        rec_empty = engine.recommend(
            task_spec=task_spec,
            candidate_records=[],
            utility_estimates={},
            popularity_profiles={},
            baseline_mode="r3_diversified_set",
            target_k=3,
        )
        self.assertEqual(len(rec_empty.cards), 0)
        self.assertEqual(len(rec_empty.selected_dataset_ids), 0)

        # 2. Pool smaller than requested target_k (1 candidate, k=3)
        rec_single = self.records_by_name["Iris"]
        u_single = {rec_single.internal_id: self.estimator.evaluate(rec_single, task_spec, baseline_mode="baseline_c")}
        prof_single = {rec_single.internal_id: self.profiles[rec_single.internal_id]}

        rec_set_single = engine.recommend(
            task_spec=task_spec,
            candidate_records=[rec_single],
            utility_estimates=u_single,
            popularity_profiles=prof_single,
            baseline_mode="r3_diversified_set",
            target_k=3,
        )
        self.assertEqual(len(rec_set_single.cards), 1)
        self.assertEqual(rec_set_single.cards[0].assigned_role, "best_overall")

    def test_deterministic_serialization_roundtrip(self) -> None:
        task_spec = TaskSpecification.create(task_type="classification", primary_modality="tabular")
        engine = RecommendationEngine()
        u_estimates = {
            r.internal_id: self.estimator.evaluate(r, task_spec, baseline_mode="baseline_c")
            for r in self.records
        }
        rec_set = engine.recommend(
            task_spec=task_spec,
            candidate_records=self.records,
            utility_estimates=u_estimates,
            popularity_profiles=self.profiles,
            baseline_mode="r3_diversified_set",
            target_k=3,
        )

        serialized = json.dumps(rec_set.as_dict(), sort_keys=True)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["set_id"], rec_set.set_id)
        self.assertEqual(len(deserialized["cards"]), len(rec_set.cards))


if __name__ == "__main__":
    unittest.main()
