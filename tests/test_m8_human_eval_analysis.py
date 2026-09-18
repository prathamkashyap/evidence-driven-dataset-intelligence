#!/usr/bin/env python3
"""
Tests for M8 human evaluation analysis layer.

Verifies:
  - primary dataset shape and schema
  - repeat-exposure dataset shape and schema
  - analysis output JSON structure and key computed values
  - methodological constraints (no inferential stats, N=3 labelling)
  - R3 provenance caveat is present in supplementary section
  - research findings document exists and contains required sections
  - machine-readable results JSON exists and is valid
"""

import csv
import json
import pathlib
import unittest
from collections import Counter

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

PRIMARY_CSV = PROJECT_ROOT / "data" / "benchmarks" / "m8_human_eval_primary.csv"
REPEAT_CSV = PROJECT_ROOT / "data" / "benchmarks" / "m8_human_eval_repeat_exposure.csv"
ANALYSIS_JSON = PROJECT_ROOT / "experiments" / "m8" / "results" / "m8_human_eval_summary.json"
RESULTS_JSON = PROJECT_ROOT / "experiments" / "m8" / "human_eval" / "m8_human_eval_results.json"
FINDINGS_DOC = PROJECT_ROOT / "docs" / "M8_RESEARCH_FINDINGS.md"

EXPECTED_PRIMARY_SCHEMA = {
    "participant_id",
    "submission_id",
    "task_name",
    "comparison_id",
    "dataset_id",
    "format_presented",
    "presentation_order",
    "trust_score",
    "understanding_score",
    "actionability_score",
}

EXPECTED_REPEAT_SCHEMA = {
    "participant_id",
    "submission_id",
    "exposure_number",
    "form_slot",
    "task_name",
    "comparison_id",
    "dataset_id",
    "format_presented",
    "presentation_order",
    "trust_score",
    "understanding_score",
    "actionability_score",
}


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Primary dataset tests
# ---------------------------------------------------------------------------

class TestPrimaryDataset(unittest.TestCase):

    def test_file_exists(self):
        self.assertTrue(PRIMARY_CSV.exists(), f"Missing primary CSV: {PRIMARY_CSV}")

    def test_row_count(self):
        rows = _read_csv(PRIMARY_CSV)
        self.assertEqual(len(rows), 42, f"Expected 42 primary rows, got {len(rows)}")

    def test_schema(self):
        rows = _read_csv(PRIMARY_CSV)
        self.assertTrue(rows, "Primary CSV is empty")
        actual_cols = set(rows[0].keys()) - {"notes"}
        missing = EXPECTED_PRIMARY_SCHEMA - actual_cols
        self.assertFalse(missing, f"Missing columns: {missing}")

    def test_three_participants(self):
        rows = _read_csv(PRIMARY_CSV)
        participants = {r["participant_id"] for r in rows}
        self.assertEqual(len(participants), 3, f"Expected 3 participants, got {participants}")

    def test_two_rows_per_participant_comparison(self):
        rows = _read_csv(PRIMARY_CSV)
        comp_counts = Counter((r["participant_id"], r["comparison_id"]) for r in rows)
        for key, count in comp_counts.items():
            self.assertEqual(
                count, 2,
                f"Expected 2 rows per (participant, comparison), got {count} for {key}"
            )

    def test_likert_scores_in_range(self):
        rows = _read_csv(PRIMARY_CSV)
        for r in rows:
            for col in ("trust_score", "understanding_score", "actionability_score"):
                score = int(r[col])
                self.assertGreaterEqual(score, 1)
                self.assertLessEqual(score, 5)

    def test_no_exposure_column(self):
        """Primary dataset must not contain exposure_number (belongs to repeat CSV)."""
        rows = _read_csv(PRIMARY_CSV)
        self.assertTrue(rows)
        self.assertNotIn(
            "exposure_number", rows[0],
            "exposure_number must not appear in primary CSV"
        )


# ---------------------------------------------------------------------------
# Repeat-exposure dataset tests
# ---------------------------------------------------------------------------

class TestRepeatDataset(unittest.TestCase):

    def test_file_exists(self):
        self.assertTrue(REPEAT_CSV.exists(), f"Missing repeat CSV: {REPEAT_CSV}")

    def test_row_count(self):
        rows = _read_csv(REPEAT_CSV)
        self.assertEqual(len(rows), 84, f"Expected 84 repeat rows, got {len(rows)}")

    def test_schema(self):
        rows = _read_csv(REPEAT_CSV)
        self.assertTrue(rows)
        actual_cols = set(rows[0].keys()) - {"notes"}
        missing = EXPECTED_REPEAT_SCHEMA - actual_cols
        self.assertFalse(missing, f"Missing columns: {missing}")

    def test_exposure_numbers_are_two_or_three(self):
        rows = _read_csv(REPEAT_CSV)
        exposures = {int(r["exposure_number"]) for r in rows}
        self.assertTrue(
            exposures <= {2, 3},
            f"Repeat CSV should only have exposures 2 and 3, got {exposures}"
        )

    def test_likert_scores_in_range(self):
        rows = _read_csv(REPEAT_CSV)
        for r in rows:
            for col in ("trust_score", "understanding_score", "actionability_score"):
                score = int(r[col])
                self.assertGreaterEqual(score, 1)
                self.assertLessEqual(score, 5)


# ---------------------------------------------------------------------------
# Analysis JSON tests
# ---------------------------------------------------------------------------

class TestAnalysisJSON(unittest.TestCase):

    def setUp(self):
        self.data = _read_json(ANALYSIS_JSON)

    def test_file_exists(self):
        self.assertTrue(ANALYSIS_JSON.exists())

    def test_top_level_keys(self):
        required = {
            "study_identifier",
            "sample_size_statement",
            "primary_analysis",
            "supplementary_repeat_exposure",
        }
        self.assertTrue(required.issubset(self.data.keys()))

    def test_primary_analysis_keys(self):
        pa = self.data["primary_analysis"]
        required = {
            "card_level_summary",
            "paired_differences",
            "per_comparison_breakdown",
            "participant_level_summaries",
        }
        self.assertTrue(required.issubset(pa.keys()))

    def test_format_a_trust_mean(self):
        """Format A trust mean should be ~1.95 (21 observations)."""
        val = self.data["primary_analysis"]["card_level_summary"]["format_a"]["trust"]["mean"]
        self.assertAlmostEqual(val, 1.9524, places=2)

    def test_format_b_understanding_mean(self):
        """Format B understanding mean should be ~4.81 (21 observations)."""
        val = self.data["primary_analysis"]["card_level_summary"]["format_b"]["understanding"]["mean"]
        self.assertAlmostEqual(val, 4.8095, places=2)

    def test_paired_difference_trust_min_is_zero(self):
        """The minimum trust difference is 0 (one tie at comp_7, participant_2)."""
        val = self.data["primary_analysis"]["paired_differences"]["trust"]["min"]
        self.assertEqual(val, 0)

    def test_paired_difference_understanding_min_is_two(self):
        """Understanding differences have a floor of +2 in primary data."""
        val = self.data["primary_analysis"]["paired_differences"]["understanding"]["min"]
        self.assertEqual(val, 2)

    def test_seven_comparisons_in_breakdown(self):
        breakdown = self.data["primary_analysis"]["per_comparison_breakdown"]
        self.assertEqual(len(breakdown), 7)

    def test_three_participants_in_summaries(self):
        summaries = self.data["primary_analysis"]["participant_level_summaries"]
        self.assertEqual(len(summaries), 3)

    def test_r3_provenance_caveat_present(self):
        """Supplementary section must document E3 identity uncertainty for p1 and p3."""
        supp = self.data["supplementary_repeat_exposure"]
        for pid in ("participant_1", "participant_3"):
            status = supp["stability_by_participant"][pid]["provenance_linkage_status"].lower()
            self.assertTrue(
                "timestamp" in status or "uncertain" in status,
                f"R3 provenance caveat missing for {pid}: {status!r}"
            )

    def test_participant_2_fully_corroborated(self):
        status = (
            self.data["supplementary_repeat_exposure"]
            ["stability_by_participant"]
            ["participant_2"]
            ["provenance_linkage_status"]
            .lower()
        )
        self.assertIn("corroborated", status)

    def test_no_p_values_in_primary_analysis(self):
        """No inferential statistics keys should appear in primary analysis."""
        raw = json.dumps(self.data["primary_analysis"]).lower()
        for forbidden in ("p_value", "p-value", "significance", "wilcoxon"):
            self.assertNotIn(forbidden, raw, f"Forbidden key '{forbidden}' found")


# ---------------------------------------------------------------------------
# Machine-readable results JSON tests
# ---------------------------------------------------------------------------

class TestResultsJSON(unittest.TestCase):

    def setUp(self):
        self.data = _read_json(RESULTS_JSON)

    def test_file_exists(self):
        self.assertTrue(RESULTS_JSON.exists())

    def test_valid_json(self):
        self.assertIsInstance(self.data, dict)

    def test_n_participants(self):
        self.assertEqual(self.data.get("n_participants_primary"), 3)

    def test_no_significance_testing(self):
        self.assertEqual(self.data.get("statistical_tests_performed"), "none")

    def test_primary_results_present(self):
        self.assertIn("primary_results", self.data)
        pr = self.data["primary_results"]
        self.assertIn("card_level_format_means", pr)
        self.assertIn("paired_differences_b_minus_a", pr)
        self.assertIn("participant_level_b_minus_a_means", pr)

    def test_limitations_listed(self):
        self.assertIn("limitations", self.data)
        self.assertGreaterEqual(len(self.data["limitations"]), 4)


# ---------------------------------------------------------------------------
# Research findings document tests
# ---------------------------------------------------------------------------

class TestFindingsDocument(unittest.TestCase):

    def setUp(self):
        self.text = FINDINGS_DOC.read_text(encoding="utf-8")

    def test_file_exists(self):
        self.assertTrue(FINDINGS_DOC.exists())

    def test_has_study_purpose_section(self):
        self.assertIn("## 1. Study Purpose", self.text)

    def test_has_primary_results_section(self):
        self.assertIn("## 4. Primary Descriptive Results", self.text)

    def test_has_supplementary_section(self):
        self.assertIn("## 5. Supplementary", self.text)

    def test_has_methodological_constraints_section(self):
        self.assertIn("## 6. Methodological Constraints", self.text)

    def test_no_p_value_claims(self):
        lower = self.text.lower()
        for forbidden in ("p < 0.05", "p<0.05", "statistically significant"):
            self.assertNotIn(forbidden, lower)

    def test_n3_stated(self):
        self.assertTrue(
            "N = 3" in self.text or "N=3" in self.text,
            "N=3 sample size not stated in findings document"
        )

    def test_order_confound_documented(self):
        lower = self.text.lower()
        self.assertTrue(
            "order" in lower and "confound" in lower,
            "Findings document must document presentation order confound"
        )

    def test_r3_uncertainty_documented(self):
        lower = self.text.lower()
        self.assertTrue(
            "e3 identity uncertain" in lower or "timestamp" in lower,
            "R3 provenance uncertainty must be mentioned in findings document"
        )

    def test_frozen_artifacts_table_present(self):
        self.assertIn("## 8. Frozen Artifacts Reference", self.text)


if __name__ == "__main__":
    unittest.main()
