"""Deterministic tabular feature extraction and statistics for bounded samples."""

from __future__ import annotations

import re
from typing import Any

DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)?$")


def _is_null(val: Any) -> bool:
    return val is None or val == "" or str(val).strip().lower() in {"null", "none", "nan", "?"}


def _infer_value_primitive(val: Any) -> str:
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
        pass
    if DATETIME_RE.match(s):
        return "datetime"
    if len(s) > 30 or " " in s:
        return "text"
    return "categorical"


def extract_tabular_features(rows: list[dict[str, Any]] | list[list[Any]]) -> dict[str, Any]:
    """Extract deterministic structural and statistical tabular characteristics from at most 32 rows."""
    if not rows:
        return {
            "observed_sample_row_count": 0,
            "observed_sample_column_count": 0,
            "column_names": [],
            "inferred_column_types": {},
            "numeric_columns_count": 0,
            "categorical_columns_count": 0,
            "text_columns_count": 0,
            "boolean_columns_count": 0,
            "per_column_unique_counts": {},
            "numeric_feature_extrema": {},
            "constant_columns": [],
            "per_column_missing_rates": {},
        }

    sample = rows[:32]
    num_rows = len(sample)

    # Standardize rows into dictionary format
    dict_rows: list[dict[str, Any]] = []
    columns_set: set[str] = set()

    for item in sample:
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

    column_names = sorted(columns_set)
    num_cols = len(column_names)

    inferred_types: dict[str, str] = {}
    unique_counts: dict[str, int] = {}
    missing_rates: dict[str, float] = {}
    numeric_extrema: dict[str, dict[str, float]] = {}
    constant_cols: list[str] = []

    type_counts_summary = {"numeric": 0, "categorical": 0, "text": 0, "boolean": 0, "datetime": 0, "unknown": 0}

    for col in column_names:
        values = [row.get(col) for row in dict_rows]
        non_null_values = [v for v in values if not _is_null(v)]
        null_count = num_rows - len(non_null_values)
        missing_rate = round(null_count / num_rows, 4) if num_rows else 0.0
        missing_rates[col] = missing_rate

        # Unique values
        canonical_uniques = {str(v) for v in non_null_values}
        unique_counts[col] = len(canonical_uniques)

        if len(canonical_uniques) == 1 and num_rows > 1:
            constant_cols.append(col)

        # Inferred type
        if not non_null_values:
            col_type = "unknown"
        else:
            types = [_infer_value_primitive(v) for v in non_null_values]
            # Count dominant non-null type
            counts: dict[str, int] = {}
            for t in types:
                counts[t] = counts.get(t, 0) + 1
            col_type = max(counts.items(), key=lambda x: x[1])[0]

        inferred_types[col] = col_type
        type_counts_summary[col_type] = type_counts_summary.get(col_type, 0) + 1

        # Compute numeric stats if numeric
        if col_type == "numeric" and non_null_values:
            nums: list[float] = []
            for v in non_null_values:
                try:
                    nums.append(float(v))
                except (ValueError, TypeError):
                    pass
            if nums:
                numeric_extrema[col] = {
                    "min": round(min(nums), 4),
                    "max": round(max(nums), 4),
                    "mean": round(sum(nums) / len(nums), 4),
                }

    return {
        "observed_sample_row_count": num_rows,
        "observed_sample_column_count": num_cols,
        "column_names": column_names,
        "inferred_column_types": inferred_types,
        "numeric_columns_count": type_counts_summary["numeric"],
        "categorical_columns_count": type_counts_summary["categorical"],
        "text_columns_count": type_counts_summary["text"],
        "boolean_columns_count": type_counts_summary["boolean"],
        "per_column_unique_counts": unique_counts,
        "numeric_feature_extrema": numeric_extrema,
        "constant_columns": sorted(constant_cols),
        "per_column_missing_rates": missing_rates,
    }
