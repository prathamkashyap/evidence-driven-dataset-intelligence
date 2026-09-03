"""Unit tests for Milestone 3 Evidence Foundation.

Tests are 100% offline, deterministic, and verify the immutable ledger,
non-numerical resolution, Croissant parsing, bounded probing, and adapter integration.
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

from dataset_intelligence.evidence.croissant import extract_croissant_claims
from dataset_intelligence.evidence.harvester import EvidenceHarvester
from dataset_intelligence.evidence.ledger import (
    EvidenceLedger,
    LedgerEntry,
    compute_entry_id,
)
from dataset_intelligence.evidence.probes import (
    compute_sample_diagnostics,
    probe_bounded_sample,
)
from dataset_intelligence.evidence.resolver import (
    ClaimResolution,
    ProvisionalResolver,
    compute_resolution_id,
)
from dataset_intelligence.evidence.statuses import (
    CROISSANT_STATUSES,
    EVIDENCE_TYPES,
    OBSERVATION_STATES,
    RESOLUTION_STATES,
)
from dataset_intelligence.ingestion.adapters import ADAPTERS

FIXTURES_PATH = ROOT / "tests" / "fixtures" / "m3_fixtures.json"
M1_CORPUS_PATH = ROOT / "experiments" / "m1" / "results" / "development_corpus.jsonl"


class EvidenceLedgerTests(unittest.TestCase):
    """Tests for immutable LedgerEntry and EvidenceLedger."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    def test_ledger_entry_immutability(self) -> None:
        entry = LedgerEntry.create(
            dataset_id="ds_test1",
            claim_type="license",
            claim_value="MIT",
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.license",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
            adapter_version="1.0",
            source_url="https://example.com/test",
            raw_reference="fixture_1",
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            entry.claim_value = "Apache-2.0"  # type: ignore[misc]

        with self.assertRaises((FrozenInstanceError, AttributeError)):
            entry.observation_state = "corroborated"  # type: ignore[misc]

    def test_deterministic_entry_id(self) -> None:
        id1 = compute_entry_id(
            dataset_id="ds_test1",
            claim_type="license",
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.license",
            claim_value="MIT",
            procedure="adapter_metadata_extraction",
            sample_scope={},
            adapter_version="1.0",
            raw_reference="ref1",
            source_url="https://example.com",
        )
        id2 = compute_entry_id(
            dataset_id="ds_test1",
            claim_type="license",
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.license",
            claim_value="MIT",
            procedure="adapter_metadata_extraction",
            sample_scope={},
            adapter_version="1.0",
            raw_reference="ref1",
            source_url="https://example.com",
        )
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("ev_"))

    def test_different_timestamps_produce_identical_ids(self) -> None:
        """observed_at is provenance metadata and MUST NOT affect entry_id."""
        entry1 = LedgerEntry.create(
            dataset_id="ds_test1",
            claim_type="task",
            claim_value=["classification"],
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.task_categories",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
            adapter_version="1.0",
        )
        entry2 = LedgerEntry.create(
            dataset_id="ds_test1",
            claim_type="task",
            claim_value=["classification"],
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.task_categories",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-03T12:34:56+00:00",  # Different timestamp
            adapter_version="1.0",
        )
        self.assertEqual(entry1.entry_id, entry2.entry_id)

    def test_distinct_observation_states(self) -> None:
        self.assertEqual(
            OBSERVATION_STATES,
            {"observed", "single_source_claim", "unsupported", "failed", "unknown"},
        )
        # Invalid state rejected
        with self.assertRaises(ValueError):
            LedgerEntry.create(
                dataset_id="ds_test1",
                claim_type="license",
                claim_value="MIT",
                evidence_type="metadata_claim",
                source="huggingface",
                source_field="cardData.license",
                observation_state="verified_ground_truth",  # Invalid
                procedure="adapter_metadata_extraction",
                observed_at="2026-09-02T00:00:00+00:00",
            )

    def test_provenance_flexibility(self) -> None:
        """source_url can be None for internal probes, but observed_at is always mandatory."""
        probe_entry = LedgerEntry.create(
            dataset_id="ds_test1",
            claim_type="access_capability",
            claim_value={"sample_accessible": "conditional"},
            evidence_type="access_probe",
            source="huggingface",
            source_field="capability_report",
            observation_state="observed",
            procedure="capability_policy_check",
            observed_at="2026-09-02T00:00:00+00:00",
            source_url=None,  # Not addressable; purely operational
            raw_reference=None,
        )
        self.assertIsNone(probe_entry.source_url)
        self.assertEqual(probe_entry.observed_at, "2026-09-02T00:00:00+00:00")

        # Missing observed_at is rejected
        with self.assertRaises(ValueError):
            LedgerEntry.create(
                dataset_id="ds_test1",
                claim_type="license",
                claim_value="MIT",
                evidence_type="metadata_claim",
                source="huggingface",
                source_field="cardData.license",
                observation_state="single_source_claim",
                procedure="adapter_metadata_extraction",
                observed_at="",  # Empty
            )

    def test_ledger_jsonl_roundtrip_and_deduplication(self) -> None:
        entry1 = LedgerEntry.create(
            dataset_id="ds_1",
            claim_type="license",
            claim_value="MIT",
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.license",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        entry2 = LedgerEntry.create(
            dataset_id="ds_1",
            claim_type="sample_count",
            claim_value=150,
            evidence_type="metadata_claim",
            source="openml",
            source_field="NumberOfInstances",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        ledger = EvidenceLedger([entry1, entry2])
        # Re-adding identical entry is an idempotent no-op
        ledger.add_entry(entry1)
        self.assertEqual(len(ledger), 2)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "ledger.jsonl"
            ledger.export_jsonl(out_file)
            loaded = EvidenceLedger.from_jsonl(out_file)
            self.assertEqual(len(loaded), 2)
            self.assertEqual([e.entry_id for e in loaded], [e.entry_id for e in ledger])

        summary = ledger.summary()
        self.assertEqual(summary["total_entries"], 2)
        self.assertEqual(summary["unique_datasets"], 1)


class ProvisionalResolverTests(unittest.TestCase):
    """Tests for non-numerical provisional resolution."""

    def setUp(self) -> None:
        self.resolver = ProvisionalResolver()

    def test_single_entry_unresolved(self) -> None:
        entry = LedgerEntry.create(
            dataset_id="ds_1",
            claim_type="license",
            claim_value="MIT",
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.license",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        res = self.resolver.resolve_claim("ds_1", "license", [entry])
        self.assertEqual(res.resolution_state, "unresolved")
        self.assertEqual(res.resolved_value, "MIT")
        self.assertEqual(res.corroborating_entry_ids, ())
        self.assertEqual(res.conflicting_entry_ids, ())
        self.assertIn("uncorroborated", res.explanation.lower())

    def test_non_numerical_corroboration(self) -> None:
        entry1 = LedgerEntry.create(
            dataset_id="ds_iris",
            claim_type="sample_count",
            claim_value=150,
            evidence_type="metadata_claim",
            source="openml",
            source_field="NumberOfInstances",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        entry2 = LedgerEntry.create(
            dataset_id="ds_iris",
            claim_type="sample_count",
            claim_value=150,
            evidence_type="metadata_claim",
            source="uci",
            source_field="sample_count",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        res = self.resolver.resolve_claim("ds_iris", "sample_count", [entry1, entry2])
        self.assertEqual(res.resolution_state, "corroborated")
        self.assertEqual(res.resolved_value, 150)
        self.assertEqual(len(res.corroborating_entry_ids), 2)
        self.assertEqual(res.conflicting_entry_ids, ())

    def test_non_numerical_conflict_detection(self) -> None:
        entry1 = LedgerEntry.create(
            dataset_id="ds_1",
            claim_type="license",
            claim_value="MIT",
            evidence_type="metadata_claim",
            source="huggingface",
            source_field="cardData.license",
            observation_state="single_source_claim",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        entry2 = LedgerEntry.create(
            dataset_id="ds_1",
            claim_type="license",
            claim_value="GPL-3.0",  # Contradiction
            evidence_type="documentation_claim",
            source="github",
            source_field="readme.license",
            observation_state="single_source_claim",
            procedure="adapter_documentation_read",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        res = self.resolver.resolve_claim("ds_1", "license", [entry1, entry2])
        self.assertEqual(res.resolution_state, "conflicting")
        self.assertIsNone(res.resolved_value)
        self.assertEqual(res.corroborating_entry_ids, ())
        self.assertEqual(len(res.conflicting_entry_ids), 2)
        self.assertIn("Conflicting claims", res.explanation)

    def test_all_failed_or_unknown_resolves_to_unknown(self) -> None:
        entry = LedgerEntry.create(
            dataset_id="ds_1",
            claim_type="sample_count",
            claim_value=None,
            evidence_type="metadata_claim",
            source="kaggle",
            source_field="sample_count",
            observation_state="unknown",
            procedure="adapter_metadata_extraction",
            observed_at="2026-09-02T00:00:00+00:00",
        )
        res = self.resolver.resolve_claim("ds_1", "sample_count", [entry])
        self.assertEqual(res.resolution_state, "unknown")
        self.assertIsNone(res.resolved_value)


class CroissantStateTests(unittest.TestCase):
    """Tests for Croissant 4-state handling."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    def test_absent_croissant(self) -> None:
        status, entries = extract_croissant_claims(
            dataset_id="ds_test",
            source_name="openml",
            croissant_url=None,
            raw_croissant_payload=None,
            observed_at="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual(status, "absent")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].observation_state, "unknown")
        self.assertEqual(entries[0].claim_value, {"status": "absent"})

    def test_referenced_but_unavailable(self) -> None:
        status, entries = extract_croissant_claims(
            dataset_id="ds_test",
            source_name="huggingface",
            croissant_url="https://example.com/croissant.jsonld",
            raw_croissant_payload=None,  # Not available in cache
            observed_at="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual(status, "referenced_but_unavailable")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].observation_state, "failed")

    def test_parse_failed(self) -> None:
        status, entries = extract_croissant_claims(
            dataset_id="ds_test",
            source_name="huggingface",
            croissant_url="https://example.com/croissant.jsonld",
            raw_croissant_payload=self.fixtures["croissant_malformed"],
            observed_at="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual(status, "parse_failed")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].observation_state, "failed")

    def test_available_and_parsed(self) -> None:
        status, entries = extract_croissant_claims(
            dataset_id="ds_test",
            source_name="huggingface",
            croissant_url="https://example.com/croissant.jsonld",
            raw_croissant_payload=self.fixtures["croissant_valid"],
            observed_at="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual(status, "available_and_parsed")
        claim_types = {e.claim_type for e in entries}
        self.assertIn("croissant_metadata", claim_types)
        self.assertIn("license", claim_types)
        self.assertIn("feature_schema", claim_types)
        self.assertIn("formats", claim_types)


class BoundedProbingTests(unittest.TestCase):
    """Tests for bounded content probing under M0 limits."""

    def setUp(self) -> None:
        self.fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

    def test_sample_capped_at_32_records(self) -> None:
        # Create 50 synthetic records
        large_sample = [{"id": i, "val": f"item_{i}"} for i in range(50)]
        diag = compute_sample_diagnostics(large_sample)
        self.assertEqual(diag["records_observed"], 32)

    def test_sample_diagnostics_correctness(self) -> None:
        sample = self.fixtures["samples"]["tabular_iris"]
        diag = compute_sample_diagnostics(sample)
        self.assertEqual(diag["records_observed"], 4)
        self.assertEqual(
            set(diag["column_names"]),
            {"sepal_length", "sepal_width", "petal_length", "petal_width", "species"},
        )
        self.assertEqual(diag["column_types"]["sepal_length"], "numeric")
        self.assertEqual(diag["column_types"]["species"], "string")
        self.assertEqual(diag["null_rate"], 0.0)
        self.assertEqual(diag["duplicate_rate"], 0.0)
        self.assertTrue(len(diag["sample_sha256"]) == 64)

    def test_unsupported_sample_capability_enforced(self) -> None:
        entry = probe_bounded_sample(
            dataset_id="ds_kaggle",
            source="kaggle",
            sample_accessible="unsupported_or_policy_limited",
            raw_sample_data=None,
            observed_at="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual(entry.observation_state, "unsupported")
        self.assertEqual(entry.claim_type, "sample_inspection")
        self.assertEqual(entry.sample_scope["records_examined"], 0)

    def test_negative_sample_scope_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LedgerEntry.create(
                dataset_id="ds_test",
                claim_type="sample_inspection",
                claim_value={},
                evidence_type="content_observation",
                source="openml",
                source_field="bounded_sample",
                observation_state="observed",
                procedure="bounded_sample_digest",
                observed_at="2026-09-02T00:00:00+00:00",
                sample_scope={"records_examined": -5},
            )


class HarvesterAdapterBridgeTests(unittest.TestCase):
    """Tests verifying clean bridge from M1 CanonicalDataset to M3 LedgerEntry."""

    def test_harvest_all_for_m1_development_corpus(self) -> None:
        from dataset_intelligence.ingestion.schema import CanonicalDataset

        harvester = EvidenceHarvester()
        lines = M1_CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        records = [CanonicalDataset(**json.loads(line)) for line in lines if line.strip()]

        total_entries = 0
        ledger = EvidenceLedger()

        for rec in records:
            entries = harvester.harvest_all(
                rec,
                raw_croissant_payload=None,
                raw_sample_data=[{"dummy": 1, "col2": "val"}],
            )
            self.assertTrue(len(entries) >= 5)
            for entry in entries:
                ledger.add_entry(entry)
                total_entries += 1

        self.assertEqual(len(ledger), total_entries)
        summary = ledger.summary()
        self.assertEqual(summary["unique_datasets"], 10)
        self.assertIn("metadata_claim", summary["by_evidence_type"])
        self.assertIn("access_probe", summary["by_evidence_type"])
        self.assertIn("croissant_claim", summary["by_evidence_type"])
        self.assertIn("content_observation", summary["by_evidence_type"])

    def test_native_field_traceability(self) -> None:
        """Verifies semantic claim_type is normalized while native source_field is preserved."""
        from dataset_intelligence.ingestion.schema import CanonicalDataset

        harvester = EvidenceHarvester()
        lines = M1_CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        hf_record = CanonicalDataset(**json.loads(lines[0]))  # Rotten Tomatoes
        entries = harvester.harvest_metadata_claims(hf_record)

        license_entries = [e for e in entries if e.claim_type == "license"]
        self.assertEqual(len(license_entries), 1)
        self.assertEqual(license_entries[0].source_field, "cardData.license")
        self.assertEqual(license_entries[0].claim_value, "MIT")


if __name__ == "__main__":
    unittest.main()
