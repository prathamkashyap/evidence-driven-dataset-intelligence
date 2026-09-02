"""Versioned source-independent record contract for M1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class SourceClaim:
    value: Any
    source_url: str
    source_field: str
    observed_at: str
    state: str = "single_source_claim"


@dataclass(frozen=True)
class CanonicalDataset:
    schema_version: str
    adapter_version: str
    internal_id: str
    identity: dict[str, Any]
    semantics: dict[str, Any]
    structure: dict[str, Any]
    governance: dict[str, Any]
    community_context: dict[str, Any]
    access: dict[str, Any]
    observed_content: dict[str, Any]
    risk_uncertainty: dict[str, Any]
    claims: dict[str, list[SourceClaim]]
    provenance: list[dict[str, Any]]

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported canonical schema version.")
        required_identity = {"source_name", "source_dataset_id", "dataset_name", "canonical_url", "version_id", "dataset_family_id", "lineage"}
        if not required_identity.issubset(self.identity):
            raise ValueError("Canonical identity fields are incomplete.")
        if not self.internal_id or not self.identity["source_name"] or not self.identity["source_dataset_id"]:
            raise ValueError("Canonical identity cannot be blank.")
        if not self.provenance:
            raise ValueError("At least one source snapshot is required.")
        if set(self.observed_content) != {"sample_count_observed", "content_fingerprint", "duplicate_rate", "outlier_rate", "label_issue_rate", "probe_metrics", "utility_estimate"}:
            raise ValueError("Observed-content placeholders must remain explicit.")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
