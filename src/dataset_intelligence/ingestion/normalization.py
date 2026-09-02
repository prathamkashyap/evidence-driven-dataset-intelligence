"""Conservative deterministic normalization; unmapped source values stay visible."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit


TASK_MAP = {"text-classification": "classification", "image-classification": "classification", "classification": "classification"}
MODALITY_MAP = {"image": "image", "text": "text", "tabular": "tabular", "arff": "tabular", "csv": "tabular"}


def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    parts = urlsplit(value.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def normalize_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return re.sub(r"\s+", " ", value).strip() or None


def normalize_count(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        count = int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return count if count >= 0 else None


def normalize_timestamp(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return parsed.astimezone(UTC).isoformat() if parsed.tzinfo else parsed.replace(tzinfo=UTC).isoformat()


def normalized_terms(values: object, mapping: dict[str, str]) -> tuple[list[str], list[str]]:
    items = [values] if isinstance(values, str) else values if isinstance(values, list) else []
    known, unresolved = [], []
    for value in items:
        term = normalize_text(value)
        if not term:
            continue
        key = term.lower().replace("_", "-").replace(" ", "-")
        (known if key in mapping else unresolved).append(mapping.get(key, term))
    return sorted(set(known)), sorted(set(unresolved))


def stable_internal_id(source_name: str, source_dataset_id: str, version_id: str | None) -> str:
    material = "\x1f".join((source_name, source_dataset_id, version_id or ""))
    return f"ds_{hashlib.sha256(material.encode()).hexdigest()[:24]}"
