"""Bounded content probing enforcing M0 empirical resource ceilings."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .ledger import LedgerEntry

MAX_RECORDS_DEFAULT = 32
MAX_BYTES_DEFAULT = 64 * 1024 * 1024  # 64 MiB hard cap


def compute_sample_diagnostics(records: list[Any]) -> dict[str, Any]:
    """Compute bounded shape, missingness, and duplicate diagnostics from at most 32 records."""
    if not records:
        return {
            "records_observed": 0,
            "column_names": [],
            "column_types": {},
            "null_rate": 0.0,
            "duplicate_rate": 0.0,
            "sample_sha256": hashlib.sha256(b"").hexdigest(),
        }

    sample = records[:MAX_RECORDS_DEFAULT]
    num_records = len(sample)

    # Standardize records into rows of key-value or item lists
    canonical_rows: list[bytes] = []
    columns: set[str] = set()
    col_type_counts: dict[str, dict[str, int]] = {}
    total_cells = 0
    null_cells = 0

    for item in sample:
        # Canonical serialization for duplicate detection and hashing
        row_bytes = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        canonical_rows.append(row_bytes)

        if isinstance(item, dict):
            for col, val in item.items():
                col_name = str(col)
                columns.add(col_name)
                total_cells += 1
                col_type_counts.setdefault(col_name, {})

                if val is None or val == "":
                    null_cells += 1
                    t = "null"
                elif isinstance(val, (int, float)) and not isinstance(val, bool):
                    t = "numeric"
                elif isinstance(val, bool):
                    t = "boolean"
                elif isinstance(val, str):
                    t = "string"
                else:
                    t = "complex"
                col_type_counts[col_name][t] = col_type_counts[col_name].get(t, 0) + 1
        elif isinstance(item, (list, tuple)):
            for idx, val in enumerate(item):
                col_name = f"col_{idx}"
                columns.add(col_name)
                total_cells += 1
                col_type_counts.setdefault(col_name, {})
                if val is None or val == "":
                    null_cells += 1
                    t = "null"
                elif isinstance(val, (int, float)) and not isinstance(val, bool):
                    t = "numeric"
                elif isinstance(val, bool):
                    t = "boolean"
                elif isinstance(val, str):
                    t = "string"
                else:
                    t = "complex"
                col_type_counts[col_name][t] = col_type_counts[col_name].get(t, 0) + 1
        else:
            # Plain string line or scalar
            columns.add("line")
            total_cells += 1
            col_type_counts.setdefault("line", {})
            t = "string" if str(item).strip() else "null"
            if t == "null":
                null_cells += 1
            col_type_counts["line"][t] = col_type_counts["line"].get(t, 0) + 1

    sorted_cols = sorted(columns)
    col_types: dict[str, str] = {}
    for col in sorted_cols:
        counts = col_type_counts.get(col, {})
        # Pick dominant non-null type if available
        non_null = {k: v for k, v in counts.items() if k != "null"}
        if non_null:
            dominant = max(non_null.items(), key=lambda x: x[1])[0]
        else:
            dominant = "null"
        col_types[col] = dominant

    unique_rows = len(set(canonical_rows))
    duplicate_rows = num_records - unique_rows
    duplicate_rate = duplicate_rows / num_records if num_records else 0.0
    null_rate = null_cells / total_cells if total_cells else 0.0
    sample_sha256 = hashlib.sha256(b"\n".join(canonical_rows)).hexdigest()

    return {
        "records_observed": num_records,
        "column_names": sorted_cols,
        "column_types": col_types,
        "null_rate": round(null_rate, 4),
        "duplicate_rate": round(duplicate_rate, 4),
        "sample_sha256": sample_sha256,
    }


def probe_bounded_sample(
    dataset_id: str,
    source: str,
    sample_accessible: str,
    raw_sample_data: list[Any] | None,
    observed_at: str,
    procedure: str = "bounded_sample_digest",
    adapter_version: str = "1.0",
    sample_url: str | None = None,
    raw_reference: str | None = None,
    error_reason: str | None = None,
    bytes_examined: int = 0,
) -> LedgerEntry:
    """Evaluate a bounded content sample under M0 limits and produce a content_observation LedgerEntry."""
    if sample_accessible == "unsupported_or_policy_limited":
        return LedgerEntry.create(
            dataset_id=dataset_id,
            claim_type="sample_inspection",
            claim_value={
                "status": "unsupported",
                "reason": error_reason or "Bounded sample access unsupported without credentials under M0 policy.",
            },
            evidence_type="content_observation",
            source=source,
            source_field="sample_accessibility",
            observation_state="unsupported",
            procedure="capability_policy_check",
            observed_at=observed_at,
            adapter_version=adapter_version,
            source_url=None,
            raw_reference=raw_reference,
            sample_scope={"records_examined": 0, "bytes_examined": 0},
        )

    if error_reason or raw_sample_data is None:
        return LedgerEntry.create(
            dataset_id=dataset_id,
            claim_type="sample_inspection",
            claim_value={
                "status": "failed",
                "reason": error_reason or "No bounded sample records could be retrieved.",
            },
            evidence_type="content_observation",
            source=source,
            source_field="sample_endpoint",
            observation_state="failed",
            procedure=procedure,
            observed_at=observed_at,
            adapter_version=adapter_version,
            source_url=sample_url,
            raw_reference=raw_reference,
            sample_scope={"records_examined": 0, "bytes_examined": bytes_examined},
        )

    # Bounded slice at max 32
    records = raw_sample_data[:MAX_RECORDS_DEFAULT]
    diagnostics = compute_sample_diagnostics(records)

    scope = {
        "records_examined": diagnostics["records_observed"],
        "bytes_examined": bytes_examined or sum(len(json.dumps(r).encode()) for r in records),
    }

    return LedgerEntry.create(
        dataset_id=dataset_id,
        claim_type="sample_inspection",
        claim_value=diagnostics,
        evidence_type="content_observation",
        source=source,
        source_field="bounded_sample_records",
        observation_state="observed",
        procedure=procedure,
        observed_at=observed_at,
        adapter_version=adapter_version,
        source_url=sample_url,
        raw_reference=raw_reference,
        sample_scope=scope,
    )
