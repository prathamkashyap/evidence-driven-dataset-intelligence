"""Deterministic text corpus feature extraction for bounded samples."""

from __future__ import annotations

import re
from typing import Any

WORD_TOKEN_RE = re.compile(r"\b\w+\b")


def _compute_distribution(values: list[int | float]) -> dict[str, float | int]:
    if not values:
        return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    val_min = sorted_vals[0]
    val_max = sorted_vals[-1]
    val_mean = round(sum(sorted_vals) / n, 4)
    if n % 2 == 1:
        val_median = float(sorted_vals[n // 2])
    else:
        val_median = round((sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0, 4)
    return {
        "min": val_min,
        "max": val_max,
        "mean": val_mean,
        "median": val_median,
    }


def extract_text_features(records: list[str] | list[dict[str, Any]]) -> dict[str, Any]:
    """Extract deterministic text length, token, duplicate, and character statistics."""
    if not records:
        return {
            "observed_text_records_count": 0,
            "empty_text_records_count": 0,
            "character_length_distribution": {"min": 0, "max": 0, "mean": 0.0, "median": 0.0},
            "word_count_distribution": {"min": 0, "max": 0, "mean": 0.0, "median": 0.0},
            "duplicate_text_rate": 0.0,
            "ascii_character_ratio": 1.0,
        }

    sample = records[:32]
    text_strings: list[str] = []

    for item in sample:
        if isinstance(item, str):
            text_strings.append(item)
        elif isinstance(item, dict):
            # Find primary text field or concatenate text fields
            candidates = [v for k, v in item.items() if isinstance(v, str) and k.lower() not in {"id", "label", "target", "split"}]
            if candidates:
                text_strings.append(" ".join(candidates))
            else:
                # Fall back to any string field
                all_strs = [str(v) for v in item.values() if isinstance(v, str)]
                text_strings.append(" ".join(all_strs) if all_strs else "")
        else:
            text_strings.append(str(item))

    num_records = len(text_strings)
    empty_count = sum(1 for s in text_strings if not s.strip())

    char_lengths = [len(s) for s in text_strings]
    word_counts = [len(WORD_TOKEN_RE.findall(s)) for s in text_strings]

    # Calculate duplicate rate
    unique_texts = len(set(text_strings))
    duplicate_count = num_records - unique_texts
    duplicate_rate = round(duplicate_count / num_records, 4) if num_records else 0.0

    # Character ASCII ratio
    total_chars = sum(len(s) for s in text_strings)
    ascii_chars = sum(sum(1 for c in s if ord(c) < 128) for s in text_strings)
    ascii_ratio = round(ascii_chars / total_chars, 4) if total_chars else 1.0

    return {
        "observed_text_records_count": num_records,
        "empty_text_records_count": empty_count,
        "character_length_distribution": _compute_distribution(char_lengths),
        "word_count_distribution": _compute_distribution(word_counts),
        "duplicate_text_rate": duplicate_rate,
        "ascii_character_ratio": ascii_ratio,
    }
