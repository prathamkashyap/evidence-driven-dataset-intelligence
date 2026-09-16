"""Unit tests for minimal append-only human evaluation response capture utility.

Uses temporary filesystem fixtures only. Zero participant data is written to data/benchmarks.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from capture_m8_human_eval_response import (
    REQUIRED_CSV_HEADER,
    append_response_record,
    check_existing_responses,
    init_response_csv_if_missing,
    load_manifest,
    validate_likert_score,
    validate_response_record,
)


class TestCaptureM8HumanEvalResponse(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest_path = ROOT / "data/benchmarks/m8_human_eval_session_manifest.json"
        self.manifest = load_manifest(self.manifest_path)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.output_csv = self.temp_path / "test_responses.csv"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_exact_header_initialization(self) -> None:
        created = init_response_csv_if_missing(self.output_csv)
        self.assertTrue(created)
        self.assertTrue(self.output_csv.exists())
        content = self.output_csv.read_text(encoding="utf-8")
        self.assertEqual(content.strip(), REQUIRED_CSV_HEADER)

        # Append a test record to simulate pre-existing participant data in temp fixture
        append_response_record(
            manifest_path=self.manifest_path,
            output_path=self.output_csv,
            rater_id="rater_1",
            task_name="task_sentiment_binary",
            comparison_id="comp_1",
            dataset_id="ds_3e424a817c66aab45e96797a",
            format_presented="format_b_evidence",
            presentation_order="first",
            trust_score=4,
            understanding_score=5,
            actionability_score=4,
            notes="Test observation for byte preservation check",
        )

        # Capture complete file bytes
        bytes_before = self.output_csv.read_bytes()

        # Calling init on the existing populated file must return False
        created_again = init_response_csv_if_missing(self.output_csv)
        self.assertFalse(created_again)

        # File content must remain strictly byte-identical
        bytes_after = self.output_csv.read_bytes()
        self.assertEqual(bytes_after, bytes_before)

    def test_valid_append_record(self) -> None:
        # comp_1 for rater_1 has scheduled order B_first:
        # format_b_evidence must be 'first', format_a_plain must be 'second'
        record1 = append_response_record(
            manifest_path=self.manifest_path,
            output_path=self.output_csv,
            rater_id="rater_1",
            task_name="task_sentiment_binary",
            comparison_id="comp_1",
            dataset_id="ds_3e424a817c66aab45e96797a",
            format_presented="format_b_evidence",
            presentation_order="first",
            trust_score=4,
            understanding_score=5,
            actionability_score=4,
            notes="Clear presentation",
        )
        self.assertEqual(record1["trust_score"], 4)
        self.assertEqual(record1["notes"], "Clear presentation")

        # Second record for same comparison: format_a_plain at position 'second'
        record2 = append_response_record(
            manifest_path=self.manifest_path,
            output_path=self.output_csv,
            rater_id="rater_1",
            task_name="task_sentiment_binary",
            comparison_id="comp_1",
            dataset_id="ds_3e424a817c66aab45e96797a",
            format_presented="format_a_plain",
            presentation_order="second",
            trust_score=2,
            understanding_score=3,
            actionability_score=2,
            notes="",
        )
        self.assertEqual(record2["presentation_order"], "second")

        # Verify rows in CSV
        existing = check_existing_responses(self.output_csv)
        self.assertEqual(len(existing), 2)
        self.assertEqual(existing[0]["format_presented"], "format_b_evidence")
        self.assertEqual(existing[1]["format_presented"], "format_a_plain")

    def test_invalid_rater_rejection(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_response_record(
                manifest=self.manifest,
                rater_id="rater_unknown",
                task_name="task_sentiment_binary",
                comparison_id="comp_1",
                dataset_id="ds_3e424a817c66aab45e96797a",
                format_presented="format_b_evidence",
                presentation_order="first",
                trust_score=4,
                understanding_score=4,
                actionability_score=4,
            )
        self.assertIn("Unknown rater_id", str(ctx.exception))

    def test_invalid_comparison_rejection(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_response_record(
                manifest=self.manifest,
                rater_id="rater_1",
                task_name="task_sentiment_binary",
                comparison_id="comp_99",
                dataset_id="ds_3e424a817c66aab45e96797a",
                format_presented="format_b_evidence",
                presentation_order="first",
                trust_score=4,
                understanding_score=4,
                actionability_score=4,
            )
        self.assertIn("Unknown comparison_id", str(ctx.exception))

    def test_invalid_task_rejection(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_response_record(
                manifest=self.manifest,
                rater_id="rater_1",
                task_name="task_image_cifar",
                comparison_id="comp_1",
                dataset_id="ds_3e424a817c66aab45e96797a",
                format_presented="format_b_evidence",
                presentation_order="first",
                trust_score=4,
                understanding_score=4,
                actionability_score=4,
            )
        self.assertIn("Task mismatch", str(ctx.exception))

    def test_invalid_dataset_rejection(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_response_record(
                manifest=self.manifest,
                rater_id="rater_1",
                task_name="task_sentiment_binary",
                comparison_id="comp_1",
                dataset_id="ds_wrong_id",
                format_presented="format_b_evidence",
                presentation_order="first",
                trust_score=4,
                understanding_score=4,
                actionability_score=4,
            )
        self.assertIn("Dataset ID mismatch", str(ctx.exception))

    def test_invalid_format_rejection(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_response_record(
                manifest=self.manifest,
                rater_id="rater_1",
                task_name="task_sentiment_binary",
                comparison_id="comp_1",
                dataset_id="ds_3e424a817c66aab45e96797a",
                format_presented="format_c_experimental",
                presentation_order="first",
                trust_score=4,
                understanding_score=4,
                actionability_score=4,
            )
        self.assertIn("Invalid format_presented", str(ctx.exception))

    def test_schedule_presentation_order_mismatch_rejection(self) -> None:
        # For comp_1 and rater_1, schedule is B_first.
        # Presenting format_a_plain at position 'first' violates the randomized schedule.
        with self.assertRaises(ValueError) as ctx:
            validate_response_record(
                manifest=self.manifest,
                rater_id="rater_1",
                task_name="task_sentiment_binary",
                comparison_id="comp_1",
                dataset_id="ds_3e424a817c66aab45e96797a",
                format_presented="format_a_plain",
                presentation_order="first",
                trust_score=3,
                understanding_score=3,
                actionability_score=3,
            )
        self.assertIn("Presentation schedule mismatch", str(ctx.exception))

    def test_likert_score_bounds(self) -> None:
        # Score < 1
        with self.assertRaises(ValueError):
            validate_likert_score(0, "trust_score")
        with self.assertRaises(ValueError):
            validate_likert_score(-1, "trust_score")

        # Score > 5
        with self.assertRaises(ValueError):
            validate_likert_score(6, "trust_score")

        # Non-integer
        with self.assertRaises(ValueError):
            validate_likert_score(3.5, "trust_score")
        with self.assertRaises(ValueError):
            validate_likert_score("four", "trust_score")
        with self.assertRaises(ValueError):
            validate_likert_score(True, "trust_score")

        # Valid scores 1..5
        for s in [1, 2, 3, 4, 5, "1", "5"]:
            self.assertEqual(validate_likert_score(s, "trust"), int(s))

    def test_duplicate_row_rejection(self) -> None:
        append_response_record(
            manifest_path=self.manifest_path,
            output_path=self.output_csv,
            rater_id="rater_2",
            task_name="task_sentiment_binary",
            comparison_id="comp_1",
            dataset_id="ds_3e424a817c66aab45e96797a",
            format_presented="format_b_evidence",
            presentation_order="first",
            trust_score=4,
            understanding_score=4,
            actionability_score=4,
        )

        # Attempt duplicate of same rater, comparison, format
        with self.assertRaises(ValueError) as ctx:
            append_response_record(
                manifest_path=self.manifest_path,
                output_path=self.output_csv,
                rater_id="rater_2",
                task_name="task_sentiment_binary",
                comparison_id="comp_1",
                dataset_id="ds_3e424a817c66aab45e96797a",
                format_presented="format_b_evidence",
                presentation_order="first",
                trust_score=5,
                understanding_score=5,
                actionability_score=5,
            )
        self.assertIn("Duplicate entry rejected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
