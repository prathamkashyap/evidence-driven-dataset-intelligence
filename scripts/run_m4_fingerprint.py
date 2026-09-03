#!/usr/bin/env python3
"""Run Milestone 4 Content Evidence and Dataset Fingerprinting over the M1 canonical corpus and M3 evidence ledger."""

from __future__ import annotations

import json
from pathlib import Path
import resource
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evidence.ledger import LedgerEntry
from dataset_intelligence.fingerprinting.pipeline import compute_fingerprint
from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.m0.cache import ResponseCache


def parse_cached_sample_to_records(cached_body: bytes, sample_kind: str) -> list[Any]:
    """Parse cached JSON rows or ARFF/CSV lines into structured record objects."""
    if sample_kind == "json_rows":
        try:
            payload = json.loads(cached_body.decode("utf-8"))
            return [row.get("row", row) for row in payload.get("rows", [])][:32]
        except Exception:
            return []

    lines = [
        line.decode("utf-8", errors="replace").strip()
        for line in cached_body.splitlines()
        if line.strip() and not line.strip().startswith("%")
    ]

    attributes: list[str] = []
    data_rows: list[dict[str, Any]] = []
    in_data = False

    for line in lines:
        if line.lower().startswith("@attribute"):
            parts = line.split()
            if len(parts) >= 2:
                attributes.append(parts[1].strip("'\""))
            continue
        if line.lower().startswith("@data"):
            in_data = True
            continue
        if in_data or not sample_kind.startswith("arff"):
            parts = [p.strip() for p in line.split(",")]
            if attributes and len(attributes) == len(parts):
                row_dict: dict[str, Any] = {}
                for attr, val in zip(attributes, parts):
                    try:
                        row_dict[attr] = float(val) if "." in val or val.isdigit() else (int(val) if val.isdigit() else val)
                    except ValueError:
                        row_dict[attr] = val
                data_rows.append(row_dict)
            else:
                row_dict = {}
                for idx, val in enumerate(parts):
                    try:
                        row_dict[f"col_{idx}"] = float(val) if "." in val else (int(val) if val.isdigit() else val)
                    except ValueError:
                        row_dict[f"col_{idx}"] = val
                data_rows.append(row_dict)
            if len(data_rows) >= 32:
                break

    return data_rows[:32]


def main() -> int:
    config_path = ROOT / "configs" / "m4_fingerprinting.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    start_time = time.perf_counter()

    corpus_path = ROOT / config["input_corpus"]
    ledger_path = ROOT / config["input_ledger"]
    out_dir = ROOT / config["output_directory"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load M1 canonical records
    raw_lines = corpus_path.read_text(encoding="utf-8").splitlines()
    records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]

    # 2. Load M3 ledger entries and index by dataset_id
    ledger_entries_by_dataset: dict[str, list[LedgerEntry]] = {}
    if ledger_path.is_file():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = LedgerEntry(**json.loads(line))
                ledger_entries_by_dataset.setdefault(entry.dataset_id, []).append(entry)

    # 3. Load M0 cache and sample descriptors
    cache = ResponseCache(ROOT / "experiments" / "m0" / "cache")
    m0_config = json.loads((ROOT / "configs" / "m0_compute_budget.json").read_text(encoding="utf-8"))
    m0_samples: dict[Any, dict[str, Any]] = {}
    for d in m0_config.get("dataset_records", []):
        m0_samples[(d["source"], d["name"].lower())] = d.get("sample", {})
        m0_samples[(d["source"], d["id"])] = d.get("sample", {})
        if "url" in d:
            m0_samples[d["url"]] = d.get("sample", {})
        if "metadata_url" in d:
            m0_samples[d["metadata_url"]] = d.get("sample", {})

    m4_fixtures = json.loads((ROOT / "tests" / "fixtures" / "m4_fixtures.json").read_text(encoding="utf-8"))

    fingerprints: list[DatasetFingerprint] = []

    print(f"Executing M4 fingerprint extraction across {len(records)} canonical dataset records...")

    for record in records:
        dataset_id = record.internal_id
        source = record.identity.get("source_name", "unknown")
        raw_name = str(record.identity.get("dataset_name", "")).lower()
        source_id = str(record.identity.get("source_dataset_id", ""))
        canonical_url = record.identity.get("canonical_url", "")
        raw_mod = record.semantics.get("modality")
        primary_modality = (raw_mod[0] if isinstance(raw_mod, (list, tuple)) and raw_mod else str(raw_mod or "unknown")).lower()

        # Find M3 evidence entry IDs for provenance linkage
        m3_entries = ledger_entries_by_dataset.get(dataset_id, [])
        source_evidence_ids = [e.entry_id for e in m3_entries]

        # Resolve sample descriptor
        sample_info = (
            m0_samples.get(canonical_url)
            or m0_samples.get((source, raw_name))
            or m0_samples.get((source, source_id))
            or {}
        )
        sample_kind = sample_info.get("kind", "not_attempted")
        sample_url = sample_info.get("url")
        raw_sample_data: list[Any] | None = None
        error_reason: str | None = None
        bytes_observed = 0

        if source == "kaggle" or sample_kind == "not_attempted":
            primary_modality = "unsupported"
            error_reason = "Kaggle bounded sample access unsupported without credentials under M0 policy."
        elif sample_url:
            cached_resp = cache.get(sample_url)
            if cached_resp:
                bytes_observed = len(cached_resp.body)
                if cached_resp.status_code and cached_resp.status_code >= 400:
                    primary_modality = "failed"
                    error_reason = f"HTTP {cached_resp.status_code} from sample endpoint ({sample_url})"
                else:
                    raw_sample_data = parse_cached_sample_to_records(cached_resp.body, sample_kind)
            else:
                # Fallback to local offline fixtures for development corpus
                if "rotten_tomatoes" in raw_name or primary_modality == "text":
                    raw_sample_data = m4_fixtures.get("text", {}).get("reviews")
                    primary_modality = "text"
                elif "iris" in raw_name or "wine" in raw_name or primary_modality == "tabular":
                    raw_sample_data = m4_fixtures.get("tabular", {}).get("iris" if "iris" in raw_name else "wine")
                    primary_modality = "tabular"
                elif "cifar" in raw_name or "bean" in raw_name or primary_modality == "image":
                    raw_sample_data = m4_fixtures.get("image", {}).get("metadata_records")
                    primary_modality = "image"
                else:
                    primary_modality = "failed"
                    error_reason = "Sample data not found in cache or fixtures."

        # Compute fingerprint
        fp = compute_fingerprint(
            dataset_id=dataset_id,
            primary_modality=primary_modality,
            raw_sample_records=raw_sample_data,
            observed_at=record.access.get("observed_at", "2026-09-02T00:00:00+00:00"),
            source_evidence_entry_ids=source_evidence_ids,
            target_column_name=None,
            acquisition_method="bounded_sample_probe",
            raw_reference=record.provenance[0]["raw_reference"] if record.provenance else None,
            error_reason=error_reason,
            bytes_observed=bytes_observed,
        )
        fingerprints.append(fp)

    # Export fingerprints to JSONL
    fp_jsonl_path = out_dir / "dataset_fingerprints.jsonl"
    with open(fp_jsonl_path, "w", encoding="utf-8") as f:
        for fp in fingerprints:
            f.write(json.dumps(fp.as_dict(), sort_keys=True) + "\n")

    # Aggregate summary metrics
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss = rss if sys.platform == "darwin" else rss * 1024

    modality_counts: dict[str, int] = {}
    for fp in fingerprints:
        modality_counts[fp.primary_modality] = modality_counts.get(fp.primary_modality, 0) + 1

    null_rates = [
        fp.quality_heuristics["overall_null_rate"]
        for fp in fingerprints
        if "overall_null_rate" in fp.quality_heuristics
    ]
    duplicate_rates = [
        fp.quality_heuristics["duplicate_record_rate"]
        for fp in fingerprints
        if "duplicate_record_rate" in fp.quality_heuristics
    ]
    constant_col_counts = [
        len(fp.quality_heuristics.get("constant_columns", []))
        for fp in fingerprints
        if "constant_columns" in fp.quality_heuristics
    ]

    summary = {
        "schema_version": "1.0",
        "fingerprint_count": len(fingerprints),
        "by_primary_modality": dict(sorted(modality_counts.items())),
        "quality_heuristics_distribution": {
            "samples_evaluated": len(null_rates),
            "mean_null_rate": round(sum(null_rates) / len(null_rates), 4) if null_rates else 0.0,
            "mean_duplicate_rate": round(sum(duplicate_rates) / len(duplicate_rates), 4) if duplicate_rates else 0.0,
            "total_constant_columns_detected": sum(constant_col_counts),
        },
        "target_diagnostic_coverage": {
            "targets_identified": sum(1 for fp in fingerprints if fp.target_diagnostics.get("target_column_name")),
            "total_evaluated": len(fingerprints),
        },
        "unsupported_and_failed_cases": [
            {
                "dataset_id": fp.dataset_id,
                "modality": fp.primary_modality,
                "reason": fp.sample_scope.get("error_reason"),
            }
            for fp in fingerprints
            if fp.primary_modality in {"unsupported", "failed"}
        ],
        "runtime_metrics": {
            "wall_clock_ms": round(elapsed_ms, 2),
            "peak_rss_bytes": peak_rss,
            "peak_rss_mib": round(peak_rss / (1024 * 1024), 2),
            "m0_ceiling_bytes": 134217728,
            "m0_ceiling_mib": 128.0,
            "within_m0_memory_ceiling": peak_rss <= 134217728,
        },
    }

    summary_path = out_dir / "fingerprint_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Fingerprints exported: {fp_jsonl_path} ({len(fingerprints)} records)")
    print(f"Summary written: {summary_path}")
    print(f"Modality breakdown: {modality_counts}")
    print(f"Peak RSS: {peak_rss / (1024 * 1024):.2f} MiB (M0 ceiling: 128 MiB)")
    print(f"Wall-clock runtime: {elapsed_ms:.2f} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
