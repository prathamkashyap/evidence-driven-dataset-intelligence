"""Versioned schema and deterministic ID generation for DatasetFingerprint."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any

SCHEMA_VERSION = "1.0"
SUPPORTED_MODALITIES = frozenset({
    "tabular", "text", "image", "multimodal", "unsupported", "failed", "unknown"
})


def compute_fingerprint_id(
    dataset_id: str,
    fingerprint_version: str,
    primary_modality: str,
    sample_scope: dict[str, Any],
    structural_summary: dict[str, Any],
    modality_details: dict[str, Any],
    target_diagnostics: dict[str, Any],
    quality_heuristics: dict[str, Any],
    source_evidence_entry_ids: tuple[str, ...] | list[str],
) -> str:
    """Derive deterministic content-addressed identity from stable fingerprint fields.

    observed_at is intentionally excluded so that replayed or re-computed identical
    fingerprints produce the exact same fingerprint ID regardless of runtime clock.
    """
    payload = {
        "dataset_id": dataset_id,
        "fingerprint_version": fingerprint_version,
        "primary_modality": primary_modality,
        "sample_scope": sample_scope,
        "structural_summary": structural_summary,
        "modality_details": modality_details,
        "target_diagnostics": target_diagnostics,
        "quality_heuristics": quality_heuristics,
        "source_evidence_entry_ids": sorted(source_evidence_entry_ids),
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "fp_" + hashlib.sha256(canonical_bytes).hexdigest()[:24]


@dataclass(frozen=True)
class DatasetFingerprint:
    """A deterministic, content-addressed package of bounded-sample measurements."""

    fingerprint_id: str
    dataset_id: str
    fingerprint_version: str
    primary_modality: str
    sample_scope: dict[str, Any]
    structural_summary: dict[str, Any]
    modality_details: dict[str, Any]
    target_diagnostics: dict[str, Any]
    quality_heuristics: dict[str, Any]
    provenance: dict[str, Any]

    @classmethod
    def create(
        cls,
        *,
        dataset_id: str,
        primary_modality: str,
        sample_scope: dict[str, Any] | None = None,
        structural_summary: dict[str, Any] | None = None,
        modality_details: dict[str, Any] | None = None,
        target_diagnostics: dict[str, Any] | None = None,
        quality_heuristics: dict[str, Any] | None = None,
        observed_at: str,
        source_evidence_entry_ids: tuple[str, ...] | list[str] | None = None,
        extractor_version: str = "1.0",
        fingerprint_version: str = SCHEMA_VERSION,
        raw_reference: str | None = None,
    ) -> DatasetFingerprint:
        scope = sample_scope or {}
        struct = structural_summary or {}
        details = modality_details or {}
        target = target_diagnostics or {}
        quality = quality_heuristics or {}
        evidence_ids = tuple(sorted(source_evidence_entry_ids or ()))

        fp_id = compute_fingerprint_id(
            dataset_id=dataset_id,
            fingerprint_version=fingerprint_version,
            primary_modality=primary_modality,
            sample_scope=scope,
            structural_summary=struct,
            modality_details=details,
            target_diagnostics=target,
            quality_heuristics=quality,
            source_evidence_entry_ids=evidence_ids,
        )

        prov = {
            "observed_at": observed_at,
            "source_evidence_entry_ids": list(evidence_ids),
            "extractor_version": extractor_version,
            "raw_reference": raw_reference,
        }

        fp = cls(
            fingerprint_id=fp_id,
            dataset_id=dataset_id,
            fingerprint_version=fingerprint_version,
            primary_modality=primary_modality,
            sample_scope=scope,
            structural_summary=struct,
            modality_details=details,
            target_diagnostics=target,
            quality_heuristics=quality,
            provenance=prov,
        )
        fp.validate()
        return fp

    def validate(self) -> None:
        if not self.fingerprint_id:
            raise ValueError("fingerprint_id cannot be blank.")
        if not self.dataset_id:
            raise ValueError("dataset_id cannot be blank.")
        if self.primary_modality not in SUPPORTED_MODALITIES:
            raise ValueError(f"Unsupported primary modality: {self.primary_modality}")
        if self.fingerprint_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported fingerprint version: {self.fingerprint_version}")
        if not self.provenance.get("observed_at"):
            raise ValueError("provenance.observed_at is mandatory.")

        expected_id = compute_fingerprint_id(
            dataset_id=self.dataset_id,
            fingerprint_version=self.fingerprint_version,
            primary_modality=self.primary_modality,
            sample_scope=self.sample_scope,
            structural_summary=self.structural_summary,
            modality_details=self.modality_details,
            target_diagnostics=self.target_diagnostics,
            quality_heuristics=self.quality_heuristics,
            source_evidence_entry_ids=self.provenance.get("source_evidence_entry_ids", []),
        )
        if self.fingerprint_id != expected_id:
            raise ValueError(f"fingerprint_id mismatch: expected {expected_id}, got {self.fingerprint_id}")

        # Non-negative validation for numeric scopes
        for k, v in self.sample_scope.items():
            if isinstance(v, (int, float)) and v < 0:
                raise ValueError(f"Sample scope field '{k}' cannot be negative: {v}")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
