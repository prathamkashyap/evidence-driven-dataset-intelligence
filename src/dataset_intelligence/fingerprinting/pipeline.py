"""Orchestrator pipeline connecting M3 evidence to deterministic DatasetFingerprints."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .image import extract_image_features
from .quality import compute_quality_heuristics
from .schema import DatasetFingerprint
from .tabular import extract_tabular_features
from .target import extract_target_diagnostics
from .text import extract_text_features

MAX_RECORDS = 32


def compute_fingerprint(
    dataset_id: str,
    primary_modality: str,
    raw_sample_records: list[Any] | None,
    observed_at: str,
    source_evidence_entry_ids: tuple[str, ...] | list[str] | None = None,
    target_column_name: str | None = None,
    acquisition_method: str = "bounded_sample",
    raw_reference: str | None = None,
    error_reason: str | None = None,
    bytes_observed: int = 0,
) -> DatasetFingerprint:
    """Compute a deterministic DatasetFingerprint from bounded sample records."""
    evidence_ids = tuple(sorted(source_evidence_entry_ids or ()))

    # Handle unsupported, failed, or missing sample cases
    if primary_modality in {"unsupported", "failed", "unknown"} or raw_sample_records is None:
        modality_status = primary_modality if primary_modality in {"unsupported", "failed"} else ("failed" if error_reason else "unknown")
        scope = {
            "records_observed": 0,
            "bytes_observed": bytes_observed,
            "acquisition_method": acquisition_method,
            "error_reason": error_reason or f"Sample access {modality_status}.",
            "sample_sha256": hashlib.sha256(b"").hexdigest(),
        }
        return DatasetFingerprint.create(
            dataset_id=dataset_id,
            primary_modality=modality_status,
            sample_scope=scope,
            structural_summary={"feature_count": 0, "feature_names": [], "feature_types": {}},
            modality_details={"status": modality_status, "reason": error_reason},
            target_diagnostics={},
            quality_heuristics={},
            observed_at=observed_at,
            source_evidence_entry_ids=evidence_ids,
            raw_reference=raw_reference,
        )

    sample = raw_sample_records[:MAX_RECORDS]
    num_records = len(sample)

    # Compute raw sample hash
    canonical_rows = [
        json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        for r in sample
    ]
    sample_sha256 = hashlib.sha256(b"\n".join(canonical_rows)).hexdigest()
    bytes_total = bytes_observed or sum(len(b) for b in canonical_rows)

    modality_norm = primary_modality.lower()
    if modality_norm not in {"tabular", "text", "image", "multimodal"}:
        modality_norm = "tabular"

    modality_details: dict[str, Any] = {}
    structural_summary: dict[str, Any] = {}

    if modality_norm == "tabular":
        tab_stats = extract_tabular_features(sample)
        modality_details = tab_stats
        structural_summary = {
            "feature_count": tab_stats["observed_sample_column_count"],
            "feature_names": tab_stats["column_names"],
            "feature_types": tab_stats["inferred_column_types"],
            "numeric_features": tab_stats["numeric_columns_count"],
            "categorical_features": tab_stats["categorical_columns_count"],
        }
    elif modality_norm == "text":
        txt_stats = extract_text_features(sample)
        modality_details = txt_stats
        structural_summary = {
            "feature_count": 1,
            "feature_names": ["text"],
            "feature_types": {"text": "text"},
            "empty_text_records": txt_stats["empty_text_records_count"],
        }
    elif modality_norm == "image":
        img_stats = extract_image_features(sample)
        modality_details = img_stats
        structural_summary = {
            "feature_count": 1,
            "feature_names": ["image"],
            "feature_types": {"image": "image"},
            "image_bytes_available": img_stats["image_bytes_available"],
        }
    else:
        # Multimodal
        tab_stats = extract_tabular_features(sample)
        txt_stats = extract_text_features(sample)
        modality_details = {"tabular": tab_stats, "text": txt_stats}
        structural_summary = {
            "feature_count": tab_stats["observed_sample_column_count"],
            "feature_names": tab_stats["column_names"],
            "feature_types": tab_stats["inferred_column_types"],
        }

    target_diag = extract_target_diagnostics(sample, explicit_target_col=target_column_name)
    quality_diag = compute_quality_heuristics(sample)

    scope = {
        "records_observed": num_records,
        "bytes_observed": bytes_total,
        "acquisition_method": acquisition_method,
        "sample_sha256": sample_sha256,
    }

    return DatasetFingerprint.create(
        dataset_id=dataset_id,
        primary_modality=modality_norm,
        sample_scope=scope,
        structural_summary=structural_summary,
        modality_details=modality_details,
        target_diagnostics=target_diag,
        quality_heuristics=quality_diag,
        observed_at=observed_at,
        source_evidence_entry_ids=evidence_ids,
        raw_reference=raw_reference,
    )
