"""Unit tests for Milestone 4 Dataset Fingerprinting.

Tests are 100% offline, deterministic, and verify structural summary extraction,
modality-specific diagnostics, target distributions, quality heuristics, and M3 linkage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evidence.ledger import EvidenceLedger, LedgerEntry
from dataset_intelligence.fingerprinting.image import (
    extract_image_features,
    parse_image_header,
)
from dataset_intelligence.fingerprinting.pipeline import compute_fingerprint
from dataset_intelligence.fingerprinting.quality import compute_quality_heuristics
from dataset_intelligence.fingerprinting.schema import (
    DatasetFingerprint,
    compute_fingerprint_id,
)
from dataset_intelligence.fingerprinting.tabular import extract_tabular_features
from dataset_intelligence.fingerprinting.target import extract_target_diagnostics
from dataset_intelligence.fingerprinting.text import extract_text_features

FIXTURES_PATH = ROOT / "tests" / "fixtures" / "m4_fixtures.json"


def _make_dummy_png_bytes(width: int = 100, height: int = 200) -> bytes:
    """Create minimal valid PNG header bytes."""
    header = b"\x89PNG\r\n\x1a\n"
    # IHDR chunk: 4 bytes len (13), 4 bytes type (IHDR), 13 bytes data, 4 bytes CRC
    ihdr_data = struct.pack(">IIBB", width, height, 8, 2) + b"\x00\x00\x00"
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr_data + b"\x00\x00\x00\x00"
    return header + ihdr_chunk


def _make_dummy_jpeg_bytes(width: int = 320, height: int = 240) -> bytes:
    """Create minimal valid JPEG header with SOF0 marker."""
    soi = b"\xff\xd8"
    # SOF0 marker (0xFF, 0xC0), length (2 bytes: 8+3=11), precision (1 byte), height (2 bytes), width (2 bytes), components (1 byte)
    sof0 = b"\xff\xc0" + struct.pack(">H", 11) + struct.pack(">BHHB", 8, height, width, 3) + b"\x01\x11\x00"
    return soi + sof0


class FingerprintSchemaTests(unittest.TestCase):
    """Tests for DatasetFingerprint schema, immutability, and deterministic ID computation."""

    def test_fingerprint_immutability(self) -> None:
        fp = DatasetFingerprint.create(
            dataset_id="ds_iris",
            primary_modality="tabular",
            sample_scope={"records_observed": 4},
            structural_summary={"feature_count": 5},
            observed_at="2026-09-02T00:00:00+00:00",
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            fp.primary_modality = "text"  # type: ignore[misc]

    def test_deterministic_fingerprint_id(self) -> None:
        id1 = compute_fingerprint_id(
            dataset_id="ds_test",
            fingerprint_version="1.0",
            primary_modality="tabular",
            sample_scope={"records_observed": 32},
            structural_summary={"feature_count": 4},
            modality_details={"observed_sample_row_count": 32},
            target_diagnostics={"observed_sample_class_count": 3},
            quality_heuristics={"overall_null_rate": 0.0},
            source_evidence_entry_ids=["ev_1", "ev_2"],
        )
        id2 = compute_fingerprint_id(
            dataset_id="ds_test",
            fingerprint_version="1.0",
            primary_modality="tabular",
            sample_scope={"records_observed": 32},
            structural_summary={"feature_count": 4},
            modality_details={"observed_sample_row_count": 32},
            target_diagnostics={"observed_sample_class_count": 3},
            quality_heuristics={"overall_null_rate": 0.0},
            source_evidence_entry_ids=["ev_2", "ev_1"],  # Order permutation
        )
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("fp_"))

    def test_different_timestamps_produce_identical_fingerprint_id(self) -> None:
        fp1 = DatasetFingerprint.create(
            dataset_id="ds_1",
            primary_modality="text",
            sample_scope={"records_observed": 5},
            structural_summary={"feature_count": 1},
            observed_at="2026-09-02T00:00:00+00:00",
        )
        fp2 = DatasetFingerprint.create(
            dataset_id="ds_1",
            primary_modality="text",
            sample_scope={"records_observed": 5},
            structural_summary={"feature_count": 1},
            observed_at="2026-09-03T18:00:00+00:00",  # Different timestamp
        )
        self.assertEqual(fp1.fingerprint_id, fp2.fingerprint_id)

    def test_jsonl_serialization_roundtrip(self) -> None:
        fp = DatasetFingerprint.create(
            dataset_id="ds_iris",
            primary_modality="tabular",
            sample_scope={"records_observed": 4, "bytes_observed": 400},
            structural_summary={"feature_count": 5, "feature_names": ["a", "b", "c", "d", "y"]},
            modality_details={"numeric_columns_count": 4},
            target_diagnostics={"observed_sample_class_count": 3},
            quality_heuristics={"overall_null_rate": 0.0},
            observed_at="2026-09-02T00:00:00+00:00",
            source_evidence_entry_ids=["ev_test123"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "fingerprints.jsonl"
            out_file.write_text(json.dumps(fp.as_dict()) + "\n", encoding="utf-8")

            raw = json.loads(out_file.read_text(encoding="utf-8").strip())
            reconstructed = DatasetFingerprint(**raw)
            reconstructed.validate()
            self.assertEqual(fp.fingerprint_id, reconstructed.fingerprint_id)
            self.assertEqual(fp.sample_scope, reconstructed.sample_scope)


class TabularExtractorTests(unittest.TestCase):
    """Tests for tabular feature extraction, numeric statistics, and column type inference."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    def test_tabular_iris_extraction(self) -> None:
        data = self.fixtures["tabular"]["iris"]
        stats = extract_tabular_features(data)

        self.assertEqual(stats["observed_sample_row_count"], 4)
        self.assertEqual(stats["observed_sample_column_count"], 5)
        self.assertEqual(
            stats["column_names"],
            ["petal_length", "petal_width", "sepal_length", "sepal_width", "species"],
        )
        self.assertEqual(stats["numeric_columns_count"], 4)
        self.assertEqual(stats["categorical_columns_count"], 1)
        self.assertEqual(stats["inferred_column_types"]["species"], "categorical")
        self.assertEqual(stats["inferred_column_types"]["sepal_length"], "numeric")

        # Numeric extrema
        sl_extrema = stats["numeric_feature_extrema"]["sepal_length"]
        self.assertEqual(sl_extrema["min"], 4.9)
        self.assertEqual(sl_extrema["max"], 7.0)
        self.assertAlmostEqual(sl_extrema["mean"], 5.825, places=3)

    def test_tabular_mixed_and_degenerate_features(self) -> None:
        data = self.fixtures["tabular"]["mixed_and_degenerate"]
        stats = extract_tabular_features(data)

        self.assertEqual(stats["observed_sample_row_count"], 4)
        self.assertIn("constant_col", stats["constant_columns"])
        self.assertEqual(stats["boolean_columns_count"], 1)
        self.assertEqual(stats["inferred_column_types"]["date"], "datetime")
        self.assertEqual(stats["per_column_missing_rates"]["nullable_col"], 0.75)


class TextExtractorTests(unittest.TestCase):
    """Tests for text character length, word count distributions, and duplicate rates."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    def test_text_reviews_extraction(self) -> None:
        data = self.fixtures["text"]["reviews"]
        stats = extract_text_features(data)

        self.assertEqual(stats["observed_text_records_count"], 6)
        self.assertEqual(stats["empty_text_records_count"], 2)
        self.assertTrue(stats["duplicate_text_rate"] > 0)
        self.assertEqual(stats["ascii_character_ratio"], 1.0)

        # Length distribution
        char_dist = stats["character_length_distribution"]
        self.assertEqual(char_dist["min"], 0)
        self.assertTrue(char_dist["max"] > 40)
        self.assertTrue(char_dist["mean"] > 20)

        # Word count distribution
        word_dist = stats["word_count_distribution"]
        self.assertEqual(word_dist["min"], 0)
        self.assertTrue(word_dist["max"] >= 6)


class ImageExtractorTests(unittest.TestCase):
    """Tests for pure-Python image header extraction and metadata handling."""

    def test_png_header_parsing(self) -> None:
        png_bytes = _make_dummy_png_bytes(width=128, height=256)
        parsed = parse_image_header(png_bytes)
        self.assertIsNotNone(parsed)
        fmt, w, h, ch = parsed  # type: ignore[misc]
        self.assertEqual(fmt, "PNG")
        self.assertEqual(w, 128)
        self.assertEqual(h, 256)
        self.assertEqual(ch, 3)

    def test_jpeg_header_parsing(self) -> None:
        jpeg_bytes = _make_dummy_jpeg_bytes(width=640, height=480)
        parsed = parse_image_header(jpeg_bytes)
        self.assertIsNotNone(parsed)
        fmt, w, h, ch = parsed  # type: ignore[misc]
        self.assertEqual(fmt, "JPEG")
        self.assertEqual(w, 640)
        self.assertEqual(h, 480)
        self.assertEqual(ch, 3)

    def test_image_metadata_only_records(self) -> None:
        fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
        records = fixtures["image"]["metadata_records"]
        stats = extract_image_features(records)

        self.assertEqual(stats["observed_images_count"], 3)
        self.assertFalse(stats["image_bytes_available"])
        self.assertIn("JPEG", stats["detected_formats"])
        self.assertEqual(stats["dimensions_summary"]["min_width"], 640)
        self.assertEqual(stats["dimensions_summary"]["max_width"], 1024)
        self.assertEqual(stats["corrupt_images_count"], 0)


class TargetDiagnosticsTests(unittest.TestCase):
    """Tests for target/label extraction and class distribution diagnostics."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    def test_target_diagnostics_iris(self) -> None:
        data = self.fixtures["tabular"]["iris"]
        diag = extract_target_diagnostics(data, explicit_target_col="species")

        self.assertEqual(diag["target_column_name"], "species")
        self.assertEqual(diag["missing_target_rate"], 0.0)
        self.assertEqual(diag["observed_sample_class_count"], 3)
        self.assertEqual(
            diag["observed_class_frequencies"],
            {"setosa": 2, "versicolor": 1, "virginica": 1},
        )
        self.assertEqual(diag["observed_majority_class_ratio"], 0.5)
        self.assertEqual(diag["observed_minority_class_ratio"], 0.25)

    def test_target_diagnostics_text_reviews(self) -> None:
        data = self.fixtures["text"]["reviews"]
        diag = extract_target_diagnostics(data)

        self.assertEqual(diag["target_column_name"], "label")
        self.assertEqual(diag["observed_sample_class_count"], 3)
        self.assertIn("positive", diag["observed_class_frequencies"])


class QualityHeuristicsTests(unittest.TestCase):
    """Tests for data cleanliness indicators (nulls, duplicates, constant columns, mixed types)."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    def test_quality_diagnostics_on_degenerate_data(self) -> None:
        data = self.fixtures["tabular"]["mixed_and_degenerate"]
        qual = compute_quality_heuristics(data)

        self.assertIn("constant_col", qual["constant_columns"])
        self.assertIn("nullable_col", qual["columns_with_nulls"])
        self.assertIn("mixed_col", qual["type_inconsistent_columns"])
        self.assertTrue(qual["overall_null_rate"] > 0)

    def test_duplicate_and_empty_records(self) -> None:
        data = self.fixtures["tabular"]["with_duplicates_and_empty"]
        qual = compute_quality_heuristics(data)

        self.assertAlmostEqual(qual["duplicate_record_rate"], 0.3333, places=3)
        self.assertAlmostEqual(qual["degenerate_record_rate"], 0.3333, places=3)


class PipelineAndM3LinkageTests(unittest.TestCase):
    """Tests verifying pipeline integration, 32-record cap, and M3 evidence ledger linkage."""

    def test_sample_cap_enforced_at_32(self) -> None:
        large_sample = [{"f1": i, "label": i % 2} for i in range(100)]
        fp = compute_fingerprint(
            dataset_id="ds_large",
            primary_modality="tabular",
            raw_sample_records=large_sample,
            observed_at="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual(fp.sample_scope["records_observed"], 32)
        self.assertEqual(fp.structural_summary["feature_count"], 2)

    def test_m3_ledger_entry_id_linkage(self) -> None:
        entry = LedgerEntry.create(
            dataset_id="ds_linkage",
            claim_type="sample_inspection",
            claim_value={"status": "observed"},
            evidence_type="content_observation",
            source="openml",
            source_field="bounded_sample",
            observation_state="observed",
            procedure="bounded_sample_digest",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        ledger = EvidenceLedger([entry])

        fp = compute_fingerprint(
            dataset_id="ds_linkage",
            primary_modality="tabular",
            raw_sample_records=[{"a": 1, "b": 2}],
            observed_at="2026-09-02T00:00:00+00:00",
            source_evidence_entry_ids=[entry.entry_id],
        )
        self.assertEqual(fp.provenance["source_evidence_entry_ids"], [entry.entry_id])

    def test_unsupported_and_failed_sample_handling(self) -> None:
        # Kaggle policy unsupported
        fp_unsupported = compute_fingerprint(
            dataset_id="ds_kaggle_test",
            primary_modality="unsupported",
            raw_sample_records=None,
            observed_at="2026-09-02T00:00:00+00:00",
            error_reason="Kaggle sample access unsupported without credentials.",
        )
        self.assertEqual(fp_unsupported.primary_modality, "unsupported")
        self.assertEqual(fp_unsupported.sample_scope["records_observed"], 0)
        self.assertIn("unsupported", fp_unsupported.sample_scope["error_reason"])

        # Beans HTTP 502 failed
        fp_failed = compute_fingerprint(
            dataset_id="ds_beans_test",
            primary_modality="failed",
            raw_sample_records=None,
            observed_at="2026-09-02T00:00:00+00:00",
            error_reason="HTTP 502 Bad Gateway from HF Viewer.",
        )
        self.assertEqual(fp_failed.primary_modality, "failed")
        self.assertEqual(fp_failed.sample_scope["records_observed"], 0)
        self.assertIn("502", fp_failed.sample_scope["error_reason"])


if __name__ == "__main__":
    unittest.main()
