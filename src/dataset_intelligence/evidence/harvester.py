"""Harvester bridging M1 CanonicalDataset, SourceAdapters, and raw snapshots into LedgerEntry streams."""

from __future__ import annotations

from typing import Any

from dataset_intelligence.ingestion.adapters import ADAPTERS, SourceAdapter
from dataset_intelligence.ingestion.schema import CanonicalDataset

from .croissant import extract_croissant_claims
from .ledger import LedgerEntry
from .probes import probe_bounded_sample

# Map canonical claim keys to normalized semantic claim_type and native source_field
NATIVE_FIELD_MAP: dict[str, dict[str, tuple[str, str]]] = {
    "huggingface": {
        "dataset_name": ("dataset_name", "id"),
        "description": ("description", "description"),
        "task": ("task", "cardData.task_categories"),
        "modality": ("modality", "cardData.modalities"),
        "sample_count": ("sample_count", "cardData.size_categories"),
        "class_count": ("class_count", "class_count"),
        "license_claim": ("license", "cardData.license"),
        "version_id": ("version_id", "sha"),
        "dataset_family_id": ("dataset_family_id", "dataset_family_id"),
    },
    "openml": {
        "dataset_name": ("dataset_name", "data_set_description.name"),
        "description": ("description", "data_set_description.description"),
        "task": ("task", "data_set_description.tag"),
        "modality": ("modality", "data_set_description.format"),
        "sample_count": ("sample_count", "data_set_description.NumberOfInstances"),
        "class_count": ("class_count", "data_set_description.NumberOfClasses"),
        "license_claim": ("license", "data_set_description.licence"),
        "version_id": ("version_id", "data_set_description.version"),
        "dataset_family_id": ("dataset_family_id", "dataset_family_id"),
    },
    "uci": {
        "dataset_name": ("dataset_name", "name"),
        "description": ("description", "description"),
        "task": ("task", "tasks"),
        "modality": ("modality", "modalities"),
        "sample_count": ("sample_count", "sample_count"),
        "class_count": ("class_count", "class_count"),
        "license_claim": ("license", "license_claim"),
        "version_id": ("version_id", "version"),
        "dataset_family_id": ("dataset_family_id", "dataset_family_id"),
    },
    "kaggle": {
        "dataset_name": ("dataset_name", "title"),
        "description": ("description", "subtitle"),
        "task": ("task", "usabilityRating"),
        "modality": ("modality", "modality"),
        "sample_count": ("sample_count", "sample_count"),
        "class_count": ("class_count", "class_count"),
        "license_claim": ("license", "licenseName"),
        "version_id": ("version_id", "version"),
        "dataset_family_id": ("dataset_family_id", "dataset_family_id"),
    },
}


class EvidenceHarvester:
    """Harvests comprehensive evidence across metadata, documentation, access, Croissant, and content."""

    def __init__(self, adapters: dict[str, type[SourceAdapter]] | None = None) -> None:
        self.adapters = {k: v() for k, v in (adapters or ADAPTERS).items()}

    def harvest_metadata_claims(
        self,
        record: CanonicalDataset,
        raw_reference: str | None = None,
    ) -> list[LedgerEntry]:
        entries: list[LedgerEntry] = []
        source = record.identity.get("source_name", "unknown")
        dataset_id = record.internal_id
        canonical_url = record.identity.get("canonical_url")
        adapter_version = record.adapter_version
        field_mapping = NATIVE_FIELD_MAP.get(source, {})

        # 1. Harvest claims explicitly tracked in record.claims
        for key, claim_list in record.claims.items():
            semantic_type, native_field = field_mapping.get(key, (key, key))
            for claim in claim_list:
                c_val = claim.get("value") if isinstance(claim, dict) else claim.value
                c_state = claim.get("state", "single_source_claim") if isinstance(claim, dict) else claim.state
                c_observed_at = claim.get("observed_at") if isinstance(claim, dict) else claim.observed_at
                c_url = claim.get("source_url") if isinstance(claim, dict) else claim.source_url
                entries.append(
                    LedgerEntry.create(
                        dataset_id=dataset_id,
                        claim_type=semantic_type,
                        claim_value=c_val,
                        evidence_type="metadata_claim",
                        source=source,
                        source_field=native_field,
                        observation_state=c_state,
                        procedure="adapter_metadata_extraction",
                        observed_at=c_observed_at,
                        adapter_version=adapter_version,
                        source_url=c_url or canonical_url,
                        raw_reference=raw_reference or (record.provenance[0]["raw_reference"] if record.provenance else None),
                    )
                )

        # 2. Extract documentation claims (e.g. documentation_url, citation)
        doc_url = record.governance.get("documentation_url")
        if doc_url:
            entries.append(
                LedgerEntry.create(
                    dataset_id=dataset_id,
                    claim_type="documentation_link",
                    claim_value=doc_url,
                    evidence_type="documentation_claim",
                    source=source,
                    source_field="governance.documentation_url",
                    observation_state="single_source_claim",
                    procedure="adapter_documentation_reference",
                    observed_at=record.access.get("observed_at", "2026-09-02T00:00:00+00:00"),
                    adapter_version=adapter_version,
                    source_url=doc_url,
                    raw_reference=raw_reference,
                )
            )

        citation = record.governance.get("citation")
        if citation:
            entries.append(
                LedgerEntry.create(
                    dataset_id=dataset_id,
                    claim_type="citation",
                    claim_value=citation,
                    evidence_type="documentation_claim",
                    source=source,
                    source_field="governance.citation",
                    observation_state="single_source_claim",
                    procedure="adapter_documentation_reference",
                    observed_at=record.access.get("observed_at", "2026-09-02T00:00:00+00:00"),
                    adapter_version=adapter_version,
                    source_url=canonical_url,
                    raw_reference=raw_reference,
                )
            )

        return entries

    def harvest_access_probes(
        self,
        record: CanonicalDataset,
    ) -> list[LedgerEntry]:
        entries: list[LedgerEntry] = []
        source = record.identity.get("source_name", "unknown")
        dataset_id = record.internal_id
        adapter = self.adapters.get(source)
        observed_at = record.access.get("observed_at", "2026-09-02T00:00:00+00:00")
        adapter_version = record.adapter_version

        if not adapter:
            return entries

        cap = adapter.capability_report()
        policy = adapter.access_policy()

        # Operational capability observation
        entries.append(
            LedgerEntry.create(
                dataset_id=dataset_id,
                claim_type="access_capability",
                claim_value=cap,
                evidence_type="access_probe",
                source=source,
                source_field="capability_report",
                observation_state="observed",
                procedure="capability_policy_check",
                observed_at=observed_at,
                adapter_version=adapter_version,
                source_url=None,
                raw_reference="adapter_contract",
            )
        )

        # Access policy observation
        entries.append(
            LedgerEntry.create(
                dataset_id=dataset_id,
                claim_type="access_policy",
                claim_value=policy,
                evidence_type="access_probe",
                source=source,
                source_field="access_policy",
                observation_state="observed",
                procedure="access_policy_check",
                observed_at=observed_at,
                adapter_version=adapter_version,
                source_url=policy.get("url"),
                raw_reference="adapter_contract",
            )
        )

        return entries

    def harvest_croissant_claims(
        self,
        record: CanonicalDataset,
        raw_croissant_payload: str | dict[str, Any] | None = None,
        raw_reference: str | None = None,
    ) -> list[LedgerEntry]:
        source = record.identity.get("source_name", "unknown")
        dataset_id = record.internal_id
        croissant_url = record.governance.get("croissant_url")
        observed_at = record.access.get("observed_at", "2026-09-02T00:00:00+00:00")

        _, entries = extract_croissant_claims(
            dataset_id=dataset_id,
            source_name=source,
            croissant_url=croissant_url,
            raw_croissant_payload=raw_croissant_payload,
            observed_at=observed_at,
            adapter_version=record.adapter_version,
            raw_reference=raw_reference,
        )
        return entries

    def harvest_content_probe(
        self,
        record: CanonicalDataset,
        raw_sample_data: list[Any] | None = None,
        sample_url: str | None = None,
        raw_reference: str | None = None,
        error_reason: str | None = None,
        bytes_examined: int = 0,
    ) -> LedgerEntry:
        source = record.identity.get("source_name", "unknown")
        dataset_id = record.internal_id
        adapter = self.adapters.get(source)
        observed_at = record.access.get("observed_at", "2026-09-02T00:00:00+00:00")

        sample_accessible = "unsupported_or_policy_limited"
        if adapter:
            sample_accessible = str(adapter.capability_report().get("sample_accessible", "unsupported_or_policy_limited"))

        return probe_bounded_sample(
            dataset_id=dataset_id,
            source=source,
            sample_accessible=sample_accessible,
            raw_sample_data=raw_sample_data,
            observed_at=observed_at,
            procedure="bounded_sample_digest",
            adapter_version=record.adapter_version,
            sample_url=sample_url,
            raw_reference=raw_reference,
            error_reason=error_reason,
            bytes_examined=bytes_examined,
        )

    def harvest_all(
        self,
        record: CanonicalDataset,
        raw_croissant_payload: str | dict[str, Any] | None = None,
        raw_sample_data: list[Any] | None = None,
        sample_url: str | None = None,
        raw_reference: str | None = None,
        error_reason: str | None = None,
        bytes_examined: int = 0,
    ) -> list[LedgerEntry]:
        entries: list[LedgerEntry] = []
        entries.extend(self.harvest_metadata_claims(record, raw_reference=raw_reference))
        entries.extend(self.harvest_access_probes(record))
        entries.extend(self.harvest_croissant_claims(record, raw_croissant_payload=raw_croissant_payload, raw_reference=raw_reference))
        entries.append(
            self.harvest_content_probe(
                record,
                raw_sample_data=raw_sample_data,
                sample_url=sample_url,
                raw_reference=raw_reference,
                error_reason=error_reason,
                bytes_examined=bytes_examined,
            )
        )
        return entries
