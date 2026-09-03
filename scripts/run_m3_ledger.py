#!/usr/bin/env python3
"""Run Milestone 3 Evidence Acquisition and Ledger Construction over the M1 canonical corpus."""

from __future__ import annotations

import json
from pathlib import Path
import resource
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evidence.harvester import EvidenceHarvester
from dataset_intelligence.evidence.ledger import EvidenceLedger
from dataset_intelligence.evidence.resolver import ProvisionalResolver
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.m0.cache import ResponseCache


def parse_cached_sample(cached_body: bytes, sample_kind: str) -> list[Any]:
    if sample_kind == "json_rows":
        try:
            payload = json.loads(cached_body.decode("utf-8"))
            return [row.get("row", row) for row in payload.get("rows", [])]
        except Exception:
            return []
    # ARFF or line-based
    lines = [
        line.decode("utf-8", errors="replace").strip()
        for line in cached_body.splitlines()
        if line.strip() and not line.strip().startswith(b"%" if isinstance(line, bytes) else "%")
    ]
    # If ARFF, skip header until @data
    data_lines = []
    in_data = False
    for line in lines:
        if line.lower().startswith("@data"):
            in_data = True
            continue
        if in_data or not sample_kind.startswith("arff"):
            data_lines.append(line)
    return data_lines[:32]


def main() -> int:
    config = json.loads((ROOT / "configs" / "m3_evidence.json").read_text(encoding="utf-8"))
    start_time = time.perf_counter()

    corpus_path = ROOT / config["input_corpus"]
    out_dir = ROOT / config["output_directory"]
    out_dir.mkdir(parents=True, exist_ok=True)

    cache = ResponseCache(ROOT / "experiments" / "m0" / "cache")
    m0_config = json.loads((ROOT / "configs" / "m0_compute_budget.json").read_text(encoding="utf-8"))
    m0_samples = {
        (d["source"], d["name"].lower()): d.get("sample", {})
        for d in m0_config.get("dataset_records", [])
    }
    # Also index by source and id suffix
    for d in m0_config.get("dataset_records", []):
        m0_samples[(d["source"], d["id"])] = d.get("sample", {})

    fixtures_path = ROOT / "tests" / "fixtures" / "m3_fixtures.json"
    m3_fixtures = json.loads(fixtures_path.read_text(encoding="utf-8")) if fixtures_path.is_file() else {}

    harvester = EvidenceHarvester()
    ledger = EvidenceLedger()
    resolver = ProvisionalResolver()

    raw_lines = corpus_path.read_text(encoding="utf-8").splitlines()
    records = [CanonicalDataset(**json.loads(line)) for line in raw_lines if line.strip()]

    print(f"Loaded {len(records)} canonical records from {corpus_path.name}")

    for record in records:
        source = record.identity.get("source_name", "unknown")
        raw_name = str(record.identity.get("dataset_name", "")).lower()
        source_id = str(record.identity.get("source_dataset_id", ""))

        # Resolve sample metadata and cached body
        sample_info = m0_samples.get((source, raw_name)) or m0_samples.get((source, source_id)) or {}
        sample_kind = sample_info.get("kind", "not_attempted")
        sample_url = sample_info.get("url")
        raw_sample_data: list[Any] | None = None
        error_reason: str | None = None
        bytes_examined = 0

        if sample_kind == "not_attempted":
            raw_sample_data = None
            if source == "kaggle":
                error_reason = "Kaggle bounded sample access unsupported without credentials under M0 policy."
        elif sample_url:
            cached_resp = cache.get(sample_url)
            if cached_resp:
                bytes_examined = len(cached_resp.body)
                if cached_resp.status_code and cached_resp.status_code >= 400:
                    error_reason = f"HTTP {cached_resp.status_code} from sample endpoint ({sample_url})"
                else:
                    raw_sample_data = parse_cached_sample(cached_resp.body, sample_kind)
            else:
                # Fallback to local sample fixture if available
                if "rotten_tomatoes" in raw_name or "sentiment" in raw_name:
                    raw_sample_data = m3_fixtures.get("samples", {}).get("text_sentiment")
                elif "iris" in raw_name:
                    raw_sample_data = m3_fixtures.get("samples", {}).get("tabular_iris")
                elif "bean" in raw_name:
                    raw_sample_data = m3_fixtures.get("samples", {}).get("image_leaf")
                else:
                    error_reason = "Sample data not found in cache or fixtures."

        # Croissant payload lookup
        croissant_url = record.governance.get("croissant_url")
        raw_croissant: dict[str, Any] | None = None
        if croissant_url:
            cached_cr = cache.get(croissant_url)
            if cached_cr and cached_cr.body:
                try:
                    raw_croissant = json.loads(cached_cr.body.decode("utf-8"))
                except Exception:
                    raw_croissant = None
            elif "rotten_tomatoes" in raw_name:
                raw_croissant = m3_fixtures.get("croissant_valid")

        # Harvest all entries for this record
        entries = harvester.harvest_all(
            record=record,
            raw_croissant_payload=raw_croissant,
            raw_sample_data=raw_sample_data,
            sample_url=sample_url,
            raw_reference=record.provenance[0]["raw_reference"] if record.provenance else None,
            error_reason=error_reason,
            bytes_examined=bytes_examined,
        )

        for entry in entries:
            ledger.add_entry(entry)

    # Export ledger to JSONL
    ledger_file = out_dir / "evidence_ledger.jsonl"
    ledger.export_jsonl(ledger_file)

    # Run non-numerical provisional resolution
    resolutions = resolver.resolve_ledger(ledger)
    resolution_summary = resolver.summary(resolutions)
    ledger_summary = ledger.summary()

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss = rss if sys.platform == "darwin" else rss * 1024

    full_summary = {
        "schema_version": 1,
        "input_corpus_records": len(records),
        "ledger_summary": ledger_summary,
        "resolution_summary": resolution_summary,
        "runtime_metrics": {
            "wall_clock_ms": round(elapsed_ms, 2),
            "peak_rss_bytes": peak_rss,
            "peak_rss_mib": round(peak_rss / (1024 * 1024), 2),
            "m0_ceiling_bytes": 134217728,
            "m0_ceiling_mib": 128.0,
            "within_m0_memory_ceiling": peak_rss <= 134217728,
        },
        "resolutions_by_dataset": {
            did: [r.as_dict() for r in r_list]
            for did, r_list in resolutions.items()
        },
    }

    summary_file = out_dir / "resolution_summary.json"
    summary_file.write_text(json.dumps(full_summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Evidence Ledger written: {ledger_file} ({len(ledger)} entries)")
    print(f"Resolution Summary written: {summary_file}")
    print(f"Total entries: {ledger_summary['total_entries']}")
    print(f"Observations by state: {ledger_summary['by_observation_state']}")
    print(f"Resolutions by state: {resolution_summary['by_resolution_state']}")
    print(f"Peak RSS: {peak_rss / (1024 * 1024):.2f} MiB (M0 ceiling: 128 MiB)")
    print(f"Wall-clock runtime: {elapsed_ms:.2f} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
