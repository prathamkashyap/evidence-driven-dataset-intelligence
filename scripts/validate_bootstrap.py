#!/usr/bin/env python3
"""Validate M0's intentionally small repository and experiment configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "m0_compute_budget.json"
REQUIRED_DOCUMENTS = (
    "README.md",
    "AGENTS.md",
    "docs/PROJECT_SPEC.md",
    "docs/RESEARCH_FOUNDATION.md",
    "docs/BOOTSTRAP_RECONNAISSANCE.md",
    "docs/IMPLEMENTATION_PLAN.md",
    "docs/M0_COMPUTE_BUDGET_PLAN.md",
)
REQUIRED_METRICS = {
    "candidate_retrieval_time",
    "evidence_collection_time",
    "sample_acquisition_feasibility",
    "probe_runtime",
    "peak_memory",
    "repository_access_failure_rate",
}


def validate() -> list[str]:
    """Return bootstrap validation errors without performing network activity."""
    errors = [f"Missing required document: {path}" for path in REQUIRED_DOCUMENTS if not (ROOT / path).is_file()]

    if not CONFIG_PATH.is_file():
        return [*errors, f"Missing M0 configuration: {CONFIG_PATH.relative_to(ROOT)}"]

    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [*errors, f"Invalid JSON in {CONFIG_PATH.relative_to(ROOT)}: {error}"]

    if config.get("schema_version") != 1:
        errors.append("M0 configuration must use schema_version 1.")
    if config.get("dataset_record_target") != 10:
        errors.append("M0 must target exactly 10 dataset records.")
    if config.get("source_access_combination_target") != 5:
        errors.append("M0 must target five source/access combinations.")
    if config.get("query_target") != 3:
        errors.append("M0 must define three task queries.")
    if set(config.get("measurement_requirements", [])) != REQUIRED_METRICS:
        errors.append("M0 must define the six required efficiency measurements exactly.")

    sample_cap = config.get("sample_cap", {})
    if sample_cap.get("max_records_per_dataset") != 32 or sample_cap.get("max_bytes_per_dataset") != 64 * 1024 * 1024:
        errors.append("M0 sample caps must be 32 records and 64 MiB per dataset.")
    if config.get("candidate_discovery", {}).get("ranking_implementation_required") is not False:
        errors.append("M0 must not require ranking implementation.")
    if not (ROOT / config.get("output_directory", "")).is_dir():
        errors.append("M0 output directory must exist in the bootstrap structure.")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Bootstrap validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("Bootstrap configuration is valid. No network calls or dataset analysis were performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
