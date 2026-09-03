"""Deterministic data quality diagnostics for bounded samples."""

from __future__ import annotations

import json
from typing import Any


def _is_null(val: Any) -> bool:
    return val is None or val == "" or str(val).strip().lower() in {"null", "none", "nan", "?"}


def _primitive_type(val: Any) -> str:
    if _is_null(val):
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, (int, float)):
        return "numeric"
    s = str(val).strip()
    if s.lower() in {"true", "false"}:
        return "boolean"
    try:
        float(s)
        return "numeric"
    except ValueError:
        return "string"


def compute_quality_heuristics(records: list[Any]) -> dict[str, Any]:
    """Compute bounded-sample cleanliness indicators (nulls, duplicates, constant columns, mixed types)."""
    if not records:
        return {
            "overall_null_rate": 0.0,
            "columns_with_nulls": [],
            "constant_columns": [],
            "duplicate_record_rate": 0.0,
            "degenerate_record_rate": 0.0,
            "type_inconsistent_columns": [],
        }

    sample = records[:32]
    num_records = len(sample)

    # Standardize records
    dict_rows: list[dict[str, Any]] = []
    columns_set: set[str] = set()
    canonical_rows: list[bytes] = []

    for item in sample:
        row_bytes = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        canonical_rows.append(row_bytes)

        if isinstance(item, dict):
            dict_rows.append(item)
            columns_set.update(str(k) for k in item.keys())
        elif isinstance(item, (list, tuple)):
            row_d = {f"col_{i}": v for i, v in enumerate(item)}
            dict_rows.append(row_d)
            columns_set.update(row_d.keys())
        else:
            row_d = {"val": item}
            dict_rows.append(row_d)
            columns_set.add("val")

    columns = sorted(columns_set)
    total_cells = num_records * len(columns)
    null_cells = 0
    columns_with_nulls: list[str] = []
    constant_columns: list[str] = []
    type_inconsistent_cols: list[str] = []
    degenerate_count = 0

    # Row-level degeneracy check (all-null records)
    for row in dict_rows:
        row_values = [row.get(col) for col in columns]
        if all(_is_null(v) for v in row_values):
            degenerate_count += 1

    # Column-level diagnostics
    for col in columns:
        col_values = [row.get(col) for row in dict_rows]
        non_null_vals = [v for v in col_values if not _is_null(v)]
        null_count = num_records - len(non_null_vals)
        null_cells += null_count

        if null_count > 0:
            columns_with_nulls.append(col)

        unique_str_values = {str(v) for v in non_null_vals}
        if len(unique_str_values) == 1 and num_records > 1:
            constant_columns.append(col)

        # Check for mixed types (e.g. numeric and string in same column)
        non_null_types = {_primitive_type(v) for v in non_null_vals}
        if len(non_null_types) > 1:
            type_inconsistent_cols.append(col)

    unique_records = len(set(canonical_rows))
    duplicate_count = num_records - unique_records
    duplicate_rate = round(duplicate_count / num_records, 4) if num_records else 0.0
    overall_null_rate = round(null_cells / total_cells, 4) if total_cells else 0.0
    degenerate_rate = round(degenerate_count / num_records, 4) if num_records else 0.0

    return {
        "overall_null_rate": overall_null_rate,
        "columns_with_nulls": sorted(columns_with_nulls),
        "constant_columns": sorted(constant_columns),
        "duplicate_record_rate": duplicate_rate,
        "degenerate_record_rate": degenerate_rate,
        "type_inconsistent_columns": sorted(type_inconsistent_cols),
    }
