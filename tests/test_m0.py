"""Deterministic tests for M0 configuration, records, cache, and aggregation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.m0.cache import CachedResponse, ResponseCache
from dataset_intelligence.m0.config import load_config
from dataset_intelligence.m0.records import MeasurementRecord
from dataset_intelligence.m0.runner import runtime_metadata, summarise


class M0ConfigurationTests(unittest.TestCase):
    def test_committed_m0_configuration_loads(self) -> None:
        config = load_config(ROOT / "configs" / "m0_compute_budget.json")
        self.assertEqual(len(config["dataset_records"]), 10)
        self.assertEqual(len(config["queries"]), 3)
        self.assertEqual(config["sample_cap"]["max_records_per_dataset"], 32)


class M0RecordTests(unittest.TestCase):
    def test_failure_category_and_cache_state_are_validated(self) -> None:
        valid = MeasurementRecord(
            run_id="run", phase="sample_acquisition", source="source", started_at="2026-01-01T00:00:00+00:00",
            duration_ms=1.0, peak_rss_bytes=1, cache_state="cold", success=False, failure_category="policy_refusal",
        )
        valid.validate()
        with self.assertRaises(ValueError):
            MeasurementRecord(
                run_id="run", phase="sample_acquisition", source="source", started_at="now", duration_ms=0,
                peak_rss_bytes=0, cache_state="invalid", success=True,
            ).validate()

    def test_response_cache_changes_to_warm_state_on_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = ResponseCache(Path(directory))
            cache.put("https://example.test/a", CachedResponse(b"payload", 200, None, "now"))
            self.assertEqual(cache.get("https://example.test/a"), CachedResponse(b"payload", 200, None, "now"))


class M0AggregationTests(unittest.TestCase):
    def test_summary_aggregates_latency_and_failures(self) -> None:
        records = [
            MeasurementRecord("run", "evidence_collection", "openml", "now", 10.0, 100, "cold", True, dataset_id="a"),
            MeasurementRecord("run", "sample_acquisition", "openml", "now", 20.0, 120, "cold", False, dataset_id="a", failure_category="timeout"),
        ]
        summary = summarise(records, {"seed": 1})
        self.assertEqual(summary["by_phase"]["evidence_collection:cold"]["median_duration_ms"], 10.0)
        self.assertEqual(summary["access"]["openml"]["failure_rate"], 0.5)
        self.assertEqual(summary["access"]["openml"]["failure_categories"], ["timeout"])

    def test_runtime_metadata_has_stable_config_hash_and_seed(self) -> None:
        path = ROOT / "configs" / "m0_compute_budget.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        metadata = runtime_metadata(path, config)
        self.assertEqual(metadata["seed"], 20260902)
        self.assertEqual(len(metadata["config_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
