from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dataset_intelligence.ingestion.adapters import ADAPTERS
from dataset_intelligence.ingestion.normalization import normalize_count, normalize_timestamp, normalize_url, stable_internal_id
from dataset_intelligence.ingestion.snapshots import SnapshotStore, SourceSnapshot

FIXTURES = json.loads((ROOT / "tests/fixtures/m1_records.json").read_text())

class CanonicalSchemaTests(unittest.TestCase):
    def test_all_fixture_records_validate_and_preserve_claims(self):
        records = [ADAPTERS[item["source"]]().normalize(item["raw"], "2026-09-02T00:00:00+00:00") for item in FIXTURES]
        self.assertEqual(len(records), 10)
        for record in records:
            record.validate(); self.assertEqual(record.schema_version, "1.0")
            self.assertTrue(record.claims); self.assertTrue(record.provenance)
            self.assertTrue(all(value is None for value in record.observed_content.values()))
    def test_normalization_is_conservative_and_deterministic(self):
        self.assertEqual(normalize_url("HTTPS://Example.COM/path/?a=1#x"), "https://example.com/path")
        self.assertEqual(normalize_count("1,200"), 1200); self.assertIsNone(normalize_count("unknown"))
        self.assertEqual(normalize_timestamp("2026-01-01T00:00:00Z"), "2026-01-01T00:00:00+00:00")
        self.assertEqual(stable_internal_id("a", "b", None), stable_internal_id("a", "b", None))
    def test_identity_does_not_merge_same_names_from_different_sources(self):
        iris = [ADAPTERS[item["source"]]().normalize(item["raw"], "2026-09-02T00:00:00+00:00") for item in FIXTURES if item["raw"].get("name") == "Iris" or item["raw"].get("ref") == "uciml/iris"]
        self.assertEqual(len({record.internal_id for record in iris}), 2)
    def test_capabilities_keep_kaggle_metadata_only_and_uci_discovery_unknown(self):
        self.assertEqual(ADAPTERS["kaggle"]().capability_report()["sample_accessible"], "unsupported_or_policy_limited")
        self.assertFalse(ADAPTERS["uci"]().capability_report()["metadata_discovery"])
    def test_snapshot_cache_retains_raw_provenance_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SnapshotStore(Path(directory)); snapshot = SourceSnapshot("openml", "https://example.test/61", "2026-09-02T00:00:00+00:00", "1.0", "61", {"did":"61"})
            store.put(snapshot); self.assertEqual(store.get("openml", "https://example.test/61"), snapshot)

if __name__ == "__main__": unittest.main()
