"""Lightweight standards-aligned Croissant JSON-LD claim extractor."""

from __future__ import annotations

import json
from typing import Any

from .ledger import LedgerEntry


def extract_croissant_claims(
    dataset_id: str,
    source_name: str,
    croissant_url: str | None,
    raw_croissant_payload: str | dict[str, Any] | None,
    observed_at: str,
    adapter_version: str = "1.0",
    raw_reference: str | None = None,
) -> tuple[str, list[LedgerEntry]]:
    """Extract structured claims from Croissant JSON-LD.

    Returns (status, entries) where status is one of:
    - 'available_and_parsed'
    - 'referenced_but_unavailable'
    - 'absent'
    - 'parse_failed'
    """
    if not croissant_url:
        entry = LedgerEntry.create(
            dataset_id=dataset_id,
            claim_type="croissant_metadata",
            claim_value={"status": "absent"},
            evidence_type="croissant_claim",
            source=source_name,
            source_field="croissant_url",
            observation_state="unknown",
            procedure="croissant_check",
            observed_at=observed_at,
            adapter_version=adapter_version,
            source_url=None,
            raw_reference=raw_reference,
        )
        return "absent", [entry]

    if raw_croissant_payload is None:
        entry = LedgerEntry.create(
            dataset_id=dataset_id,
            claim_type="croissant_metadata",
            claim_value={"status": "referenced_but_unavailable", "url": croissant_url},
            evidence_type="croissant_claim",
            source=source_name,
            source_field="croissant_url",
            observation_state="failed",
            procedure="croissant_fetch",
            observed_at=observed_at,
            adapter_version=adapter_version,
            source_url=croissant_url,
            raw_reference=raw_reference,
        )
        return "referenced_but_unavailable", [entry]

    # Attempt parsing
    data: dict[str, Any] = {}
    if isinstance(raw_croissant_payload, str):
        try:
            data = json.loads(raw_croissant_payload)
        except (ValueError, json.JSONDecodeError):
            entry = LedgerEntry.create(
                dataset_id=dataset_id,
                claim_type="croissant_metadata",
                claim_value={"status": "parse_failed", "url": croissant_url},
                evidence_type="croissant_claim",
                source=source_name,
                source_field="croissant_url",
                observation_state="failed",
                procedure="croissant_parse",
                observed_at=observed_at,
                adapter_version=adapter_version,
                source_url=croissant_url,
                raw_reference=raw_reference,
            )
            return "parse_failed", [entry]
    elif isinstance(raw_croissant_payload, dict):
        data = raw_croissant_payload
    else:
        entry = LedgerEntry.create(
            dataset_id=dataset_id,
            claim_type="croissant_metadata",
            claim_value={"status": "parse_failed", "url": croissant_url},
            evidence_type="croissant_claim",
            source=source_name,
            source_field="croissant_url",
            observation_state="failed",
            procedure="croissant_parse",
            observed_at=observed_at,
            adapter_version=adapter_version,
            source_url=croissant_url,
            raw_reference=raw_reference,
        )
        return "parse_failed", [entry]

    # Look for top-level or @graph entries
    items = data.get("@graph", [data]) if isinstance(data, dict) else []
    record_sets: list[str] = []
    formats: list[str] = []
    license_val: str | None = None

    for item in items:
        if not isinstance(item, dict):
            continue
        if "license" in item or "dct:license" in item:
            license_val = item.get("license") or item.get("dct:license")
        if item.get("@type") == "cr:RecordSet" or "recordSet" in item:
            rsets = item.get("recordSet", [item]) if "recordSet" in item else [item]
            for rs in rsets:
                if isinstance(rs, dict) and rs.get("name"):
                    record_sets.append(str(rs["name"]))
        if "distribution" in item:
            dists = item["distribution"] if isinstance(item["distribution"], list) else [item["distribution"]]
            for d in dists:
                if isinstance(d, dict) and d.get("encodingFormat"):
                    formats.append(str(d["encodingFormat"]))

    entries: list[LedgerEntry] = []

    # Emit general parsed confirmation claim
    entries.append(
        LedgerEntry.create(
            dataset_id=dataset_id,
            claim_type="croissant_metadata",
            claim_value={"status": "available_and_parsed", "url": croissant_url},
            evidence_type="croissant_claim",
            source=source_name,
            source_field="croissant_url",
            observation_state="observed",
            procedure="croissant_parse",
            observed_at=observed_at,
            adapter_version=adapter_version,
            source_url=croissant_url,
            raw_reference=raw_reference,
        )
    )

    if license_val is not None:
        entries.append(
            LedgerEntry.create(
                dataset_id=dataset_id,
                claim_type="license",
                claim_value=license_val,
                evidence_type="croissant_claim",
                source=source_name,
                source_field="croissant.license",
                observation_state="single_source_claim",
                procedure="croissant_extract_license",
                observed_at=observed_at,
                adapter_version=adapter_version,
                source_url=croissant_url,
                raw_reference=raw_reference,
            )
        )

    if record_sets:
        entries.append(
            LedgerEntry.create(
                dataset_id=dataset_id,
                claim_type="feature_schema",
                claim_value=sorted(record_sets),
                evidence_type="croissant_claim",
                source=source_name,
                source_field="croissant.recordSet",
                observation_state="single_source_claim",
                procedure="croissant_extract_recordsets",
                observed_at=observed_at,
                adapter_version=adapter_version,
                source_url=croissant_url,
                raw_reference=raw_reference,
            )
        )

    if formats:
        entries.append(
            LedgerEntry.create(
                dataset_id=dataset_id,
                claim_type="formats",
                claim_value=sorted(set(formats)),
                evidence_type="croissant_claim",
                source=source_name,
                source_field="croissant.distribution",
                observation_state="single_source_claim",
                procedure="croissant_extract_formats",
                observed_at=observed_at,
                adapter_version=adapter_version,
                source_url=croissant_url,
                raw_reference=raw_reference,
            )
        )

    return "available_and_parsed", entries
