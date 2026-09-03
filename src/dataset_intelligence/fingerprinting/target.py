"""Deterministic target and class distribution diagnostics on bounded samples."""

from __future__ import annotations

from typing import Any

TARGET_CANDIDATE_NAMES = (
    "label", "target", "class", "species", "disease_label", "sentiment", "category", "y"
)


def _is_null(val: Any) -> bool:
    return val is None or val == "" or str(val).strip().lower() in {"null", "none", "nan", "?"}


def extract_target_diagnostics(
    records: list[dict[str, Any]] | list[Any],
    explicit_target_col: str | None = None,
) -> dict[str, Any]:
    """Extract deterministic label cardinality and frequency characteristics from at most 32 records."""
    if not records:
        return {
            "target_column_name": None,
            "missing_target_rate": 0.0,
            "observed_sample_class_count": 0,
            "observed_class_frequencies": {},
            "observed_majority_class_ratio": 0.0,
            "observed_minority_class_ratio": 0.0,
        }

    sample = records[:32]
    num_records = len(sample)

    target_col: str | None = explicit_target_col
    target_values: list[Any] = []

    # If records are dicts, locate target column
    if isinstance(sample[0], dict):
        if not target_col:
            # Check candidate names case-insensitively
            col_map = {str(k).lower(): str(k) for k in sample[0].keys()}
            for candidate in TARGET_CANDIDATE_NAMES:
                if candidate in col_map:
                    target_col = col_map[candidate]
                    break

        if target_col:
            target_values = [row.get(target_col) for row in sample if isinstance(row, dict)]
    elif isinstance(sample[0], (list, tuple)) and len(sample[0]) > 1:
        # Check last column if explicit target not set
        target_col = explicit_target_col or "last_column"
        target_values = [row[-1] for row in sample if isinstance(row, (list, tuple))]

    if not target_col or not target_values:
        return {
            "target_column_name": None,
            "missing_target_rate": 0.0,
            "observed_sample_class_count": 0,
            "observed_class_frequencies": {},
            "observed_majority_class_ratio": 0.0,
            "observed_minority_class_ratio": 0.0,
        }

    non_null_labels = [str(v) for v in target_values if not _is_null(v)]
    null_count = num_records - len(non_null_labels)
    missing_rate = round(null_count / num_records, 4) if num_records else 0.0

    freqs: dict[str, int] = {}
    for lbl in non_null_labels:
        freqs[lbl] = freqs.get(lbl, 0) + 1

    unique_classes = len(freqs)
    total_labeled = len(non_null_labels)

    if total_labeled > 0 and unique_classes > 0:
        majority_count = max(freqs.values())
        minority_count = min(freqs.values())
        majority_ratio = round(majority_count / total_labeled, 4)
        minority_ratio = round(minority_count / total_labeled, 4)
    else:
        majority_ratio = 0.0
        minority_ratio = 0.0

    return {
        "target_column_name": target_col,
        "missing_target_rate": missing_rate,
        "observed_sample_class_count": unique_classes,
        "observed_class_frequencies": dict(sorted(freqs.items())),
        "observed_majority_class_ratio": majority_ratio,
        "observed_minority_class_ratio": minority_ratio,
    }
