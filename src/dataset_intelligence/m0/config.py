"""M0-only configuration loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("Only M0 schema version 1 is supported.")
    if len(config.get("queries", [])) != config.get("query_target"):
        raise ValueError("query_target must match the configured query count.")
    if len(config.get("dataset_records", [])) != config.get("dataset_record_target"):
        raise ValueError("dataset_record_target must match the configured dataset count.")
    if config["sample_cap"]["max_records_per_dataset"] != 32:
        raise ValueError("M0 must cap acquired records at 32.")
    if config["sample_cap"]["max_bytes_per_dataset"] != 64 * 1024 * 1024:
        raise ValueError("M0 must cap acquisition at 64 MiB.")
    if config.get("diagnostic", {}).get("id") != "record_shape_digest_v1":
        raise ValueError("M0 uses exactly one predeclared lightweight diagnostic.")
    return config
