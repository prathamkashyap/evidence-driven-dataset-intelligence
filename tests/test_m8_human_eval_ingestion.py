#!/usr/bin/env python3
"""Tests for Milestone 8 post-collection data ingestion and provenance artifacts."""

import csv
import hashlib
import json
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "m8_initial_collection"
PROVENANCE_MANIFEST_PATH = (
    REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_raw_collection_manifest.json"
)
LONG_CSV_PATH = (
    REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_responses_long.csv"
)
BLANK_RESPONSES_CSV_PATH = (
    REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_responses.csv"
)
SESSION_MANIFEST_PATH = (
    REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_session_manifest.json"
)


class TestM8HumanEvalIngestion(unittest.TestCase):
    """Verify integrity of raw data preservation and derived provenance dataset."""

    def test_raw_files_exist_and_unaltered(self) -> None:
        expected_files = ["rater1_form.csv", "rater2_form.csv", "rater3_form.csv"]
        for fname in expected_files:
            p = RAW_DIR / fname
            self.assertTrue(p.exists(), f"Missing raw file: {p}")
            # Ensure non-empty and readable
            self.assertGreater(p.stat().st_size, 10000, f"File unexpectedly small: {p}")

    def test_raw_exports_dimensions(self) -> None:
        """Each of the 3 raw files must contain exactly 57 columns and 3 response rows."""
        for fname in ["rater1_form.csv", "rater2_form.csv", "rater3_form.csv"]:
            p = RAW_DIR / fname
            with open(p, encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                rows = list(reader)
                self.assertEqual(
                    len(header), 57, f"Header in {fname} has {len(header)} cols, expected 57"
                )
                self.assertEqual(
                    len(rows), 3, f"Rows in {fname} has {len(rows)} rows, expected 3"
                )

    def test_blank_responses_csv_preserved(self) -> None:
        """data/benchmarks/m8_human_eval_responses.csv must remain strictly header-only."""
        self.assertTrue(BLANK_RESPONSES_CSV_PATH.exists())
        lines = [line.strip() for line in BLANK_RESPONSES_CSV_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, "m8_human_eval_responses.csv must contain strictly the header row")
        expected_header = "rater_id,task_name,comparison_id,dataset_id,format_presented,presentation_order,trust_score,understanding_score,actionability_score,notes"
        self.assertEqual(lines[0], expected_header)

    def test_provenance_manifest_integrity(self) -> None:
        self.assertTrue(PROVENANCE_MANIFEST_PATH.exists())
        manifest = json.loads(PROVENANCE_MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(manifest["collection_summary"]["total_raw_submissions"], 9)
        self.assertEqual(manifest["collection_summary"]["distinct_human_participants"], 3)
        self.assertEqual(manifest["collection_summary"]["submissions_per_participant"], 3)
        self.assertEqual(manifest["collection_summary"]["total_card_observation_rows"], 126)

        # Check exposure structure
        exp_struct = manifest["experimental_exposure_structure"]
        self.assertIn("RATER_1", exp_struct["exposure_order_chronology"])
        self.assertIn("RATER_2", exp_struct["exposure_order_chronology"])
        self.assertIn("RATER_3", exp_struct["exposure_order_chronology"])
        self.assertFalse(exp_struct["outcome_based_selection"])

        # Check participants (filter metadata keys that start with '_')
        parts = manifest["participant_grouping"]
        participant_keys = [k for k in parts if not k.startswith("_")]
        self.assertEqual(len(participant_keys), 3)
        self.assertIn("participant_1", parts)
        self.assertIn("participant_2", parts)
        self.assertIn("participant_3", parts)

        # Check subsets
        subsets = manifest["subsets"]
        self.assertEqual(len(subsets["first_exposure_subset"]["submission_ids"]), 3)
        self.assertEqual(subsets["first_exposure_subset"]["card_observation_count"], 42)
        self.assertEqual(len(subsets["repeated_exposure_subset"]["submission_ids"]), 6)
        self.assertEqual(subsets["repeated_exposure_subset"]["card_observation_count"], 84)

    def test_long_csv_structure_and_bounds(self) -> None:
        self.assertTrue(LONG_CSV_PATH.exists())
        with open(LONG_CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 126)

        session_manifest = json.loads(SESSION_MANIFEST_PATH.read_text(encoding="utf-8"))
        comp_map = {c["comparison_id"]: c for c in session_manifest["comparisons"]}

        exp1_count = 0
        exp_repeat_count = 0

        for r in rows:
            exp_num = int(r["exposure_number"])
            if exp_num == 1:
                exp1_count += 1
            else:
                exp_repeat_count += 1

            cid = r["comparison_id"]
            slot = r["form_slot"].lower()
            expected_order = comp_map[cid]["presentation_order"][slot]

            pos = r["presentation_order"]
            fmt = r["format_presented"]

            if expected_order == "B_first":
                if pos == "first":
                    self.assertEqual(fmt, "format_b_evidence")
                else:
                    self.assertEqual(fmt, "format_a_plain")
            elif expected_order == "A_first":
                if pos == "first":
                    self.assertEqual(fmt, "format_a_plain")
                else:
                    self.assertEqual(fmt, "format_b_evidence")

            # Check Likert score bounds
            for dim in ["trust_score", "understanding_score", "actionability_score"]:
                score = int(r[dim])
                self.assertTrue(1 <= score <= 5, f"Score out of bounds: {score} in {r}")

        self.assertEqual(exp1_count, 42)
        self.assertEqual(exp_repeat_count, 84)


if __name__ == "__main__":
    unittest.main()
