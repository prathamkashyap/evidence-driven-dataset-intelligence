"""Run the bounded M0 access and instrumentation experiment."""

from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from time import perf_counter_ns
from typing import Any
from urllib.parse import quote_plus

from .cache import ResponseCache
from .config import load_config
from .http import fetch, fetch_bounded_lines
from .records import MeasurementRecord


ROOT = Path(__file__).resolve().parents[3]


def peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def now() -> str:
    return datetime.now(UTC).isoformat()


def success_from_status(status_code: int | None) -> bool:
    return status_code is not None and 200 <= status_code < 300


def failure_from_response(status_code: int | None, error_kind: str | None) -> str:
    if status_code in {401, 403}:
        return "authentication_or_gating"
    if status_code == 404:
        return "unavailable_endpoint"
    if status_code == 429:
        return "rate_limit"
    if error_kind in {"timeout", "TimeoutError"}:
        return "timeout"
    return "unknown"


def runtime_metadata(config_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp_utc": now(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "rss_unit": "bytes (macOS ru_maxrss)" if sys.platform == "darwin" else "bytes (ru_maxrss KiB normalized)",
        "package_versions": {"runtime_dependencies": []},
        "seed": config["reproducibility"]["seed"],
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
    }


def event(**kwargs: Any) -> MeasurementRecord:
    record = MeasurementRecord(peak_rss_bytes=peak_rss_bytes(), **kwargs)
    record.validate()
    return record


def candidate_events(run_id: str, condition: str, config: dict[str, Any], cache: ResponseCache) -> list[MeasurementRecord]:
    records: list[MeasurementRecord] = []
    for source in config["sources"]:
        discovery = source["candidate_discovery"]
        for query in config["queries"]:
            started = now()
            if "url_template" not in discovery:
                records.append(event(
                    run_id=run_id, phase="candidate_retrieval", source=source["id"], started_at=started,
                    duration_ms=0.0, cache_state="not_applicable", success=False,
                    query_id=query["id"], failure_category="unavailable_endpoint",
                    details={"discovery_mode": discovery["mode"], "policy_url": source["policy_url"]},
                ))
                continue
            term = query.get("source_terms", {}).get(source["id"], "")
            url = discovery["url_template"].format(term=quote_plus(term))
            outcome = fetch(url, cache, 1_048_576)
            ok = success_from_status(outcome.response.status_code)
            records.append(event(
                run_id=run_id, phase="candidate_retrieval", source=source["id"], started_at=started,
                duration_ms=outcome.duration_ms, cache_state=outcome.cache_state if condition == "warm" else "cold",
                success=ok, query_id=query["id"], bytes_acquired=len(outcome.response.body),
                network_requests=outcome.network_requests, status_code=outcome.response.status_code,
                failure_category=None if ok else failure_from_response(outcome.response.status_code, outcome.response.error_kind),
                details={"discovery_mode": discovery["mode"], "policy_url": source["policy_url"], "endpoint": url},
            ))
    return records


def evidence_events(run_id: str, condition: str, config: dict[str, Any], cache: ResponseCache) -> list[MeasurementRecord]:
    sources = {source["id"]: source for source in config["sources"]}
    records: list[MeasurementRecord] = []
    for dataset in config["dataset_records"]:
        started = now()
        outcome = fetch(dataset["metadata_url"], cache, 1_048_576)
        ok = success_from_status(outcome.response.status_code)
        records.append(event(
            run_id=run_id, phase="evidence_collection", source=dataset["source"], started_at=started,
            duration_ms=outcome.duration_ms, cache_state=outcome.cache_state if condition == "warm" else "cold",
            success=ok, dataset_id=dataset["id"], dataset_url=dataset["url"],
            bytes_acquired=len(outcome.response.body), network_requests=outcome.network_requests,
            status_code=outcome.response.status_code,
            failure_category=None if ok else failure_from_response(outcome.response.status_code, outcome.response.error_kind),
            details={"policy_url": sources[dataset["source"]]["policy_url"], "metadata_url": dataset["metadata_url"], "evidence_scope": "source-published metadata or landing page; not verified fact"},
        ))
    return records


def sample_event(run_id: str, condition: str, dataset: dict[str, Any], cache: ResponseCache, cap: dict[str, int]) -> tuple[MeasurementRecord, list[Any]]:
    sample = dataset["sample"]
    started = now()
    if sample["kind"] == "not_attempted":
        return event(
            run_id=run_id, phase="sample_acquisition", source=dataset["source"], started_at=started,
            duration_ms=0.0, cache_state="not_applicable", success=False, dataset_id=dataset["id"],
            dataset_url=dataset["url"], acquisition_method=sample["method"], failure_category="policy_refusal",
            details={"reason": "M0 uses no credentials and no confirmed anonymous bounded file endpoint was configured."},
        ), []
    if sample["kind"] == "json_rows":
        outcome = fetch(sample["url"], cache, cap["max_bytes_per_dataset"])
        try:
            payload = json.loads(outcome.response.body.decode("utf-8")) if success_from_status(outcome.response.status_code) else {}
            items = [row.get("row", row) for row in payload.get("rows", [])][:cap["max_records_per_dataset"]]
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload, items = {}, []
        ok = bool(items)
        return event(
            run_id=run_id, phase="sample_acquisition", source=dataset["source"], started_at=started,
            duration_ms=outcome.duration_ms, cache_state=outcome.cache_state if condition == "warm" else "cold",
            success=ok, dataset_id=dataset["id"], dataset_url=dataset["url"], acquisition_method=sample["method"],
            records_acquired=len(items), bytes_acquired=len(outcome.response.body), network_requests=outcome.network_requests,
            status_code=outcome.response.status_code, failure_category=None if ok else (failure_from_response(outcome.response.status_code, outcome.response.error_kind) if outcome.response.status_code else "incompatible_format"),
            details={"sample_url": sample["url"], "sample_scope": "bounded viewer rows; image/audio URLs, if present, were not fetched."},
        ), items
    outcome = fetch_bounded_lines(
        sample["url"], cache, max_records=cap["max_records_per_dataset"], max_bytes=cap["max_bytes_per_dataset"], arff=sample["kind"] == "arff_lines"
    )
    items = [line.decode("utf-8", errors="replace").rstrip("\r\n") for line in outcome.response.body.splitlines() if line.strip()]
    ok = bool(items) and success_from_status(outcome.response.status_code)
    return event(
        run_id=run_id, phase="sample_acquisition", source=dataset["source"], started_at=started,
        duration_ms=outcome.duration_ms, cache_state=outcome.cache_state if condition == "warm" else "cold",
        success=ok, dataset_id=dataset["id"], dataset_url=dataset["url"], acquisition_method=sample["method"],
        records_acquired=len(items), bytes_acquired=len(outcome.response.body), network_requests=outcome.network_requests,
        status_code=outcome.response.status_code, failure_category=None if ok else failure_from_response(outcome.response.status_code, outcome.response.error_kind),
        details={"sample_url": sample["url"], "sample_scope": "first non-empty records only; no full-file analysis."},
    ), items


def diagnostic_event(run_id: str, condition: str, dataset: dict[str, Any], items: list[Any], diagnostic_id: str) -> MeasurementRecord:
    started_ns = perf_counter_ns()
    started = now()
    canonical = [json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8") for item in items]
    elapsed = (perf_counter_ns() - started_ns) / 1_000_000
    if not canonical:
        return event(
            run_id=run_id, phase="diagnostic", source=dataset["source"], started_at=started, duration_ms=elapsed,
            cache_state="not_applicable", success=False, dataset_id=dataset["id"], dataset_url=dataset["url"],
            failure_category="incompatible_format", details={"diagnostic": diagnostic_id, "reason": "No bounded sample records available."},
        )
    sizes = [len(value) for value in canonical]
    return event(
        run_id=run_id, phase="diagnostic", source=dataset["source"], started_at=started, duration_ms=elapsed,
        cache_state="not_applicable", success=True, dataset_id=dataset["id"], dataset_url=dataset["url"],
        records_acquired=len(canonical), bytes_acquired=sum(sizes), details={
            "diagnostic": diagnostic_id, "serialized_record_bytes": {"min": min(sizes), "max": max(sizes), "mean": sum(sizes) / len(sizes)},
            "sha256": hashlib.sha256(b"\n".join(canonical)).hexdigest(),
            "interpretation": "bounded record-shape diagnostic only; not a quality, utility, or full-dataset claim.",
        },
    )


def summarise(records: list[MeasurementRecord], metadata: dict[str, Any]) -> dict[str, Any]:
    values = [record.as_dict() for record in records]
    summary: dict[str, Any] = {"runtime": metadata, "record_count": len(values), "by_phase": {}, "access": {}}
    for phase in sorted({item["phase"] for item in values}):
        phase_records = [item for item in values if item["phase"] == phase]
        for state in sorted({item["cache_state"] for item in phase_records}):
            group = [item for item in phase_records if item["cache_state"] == state]
            key = f"{phase}:{state}"
            summary["by_phase"][key] = {
                "attempts": len(group), "successes": sum(item["success"] for item in group),
                "median_duration_ms": median([item["duration_ms"] for item in group]),
                "max_peak_rss_bytes": max(item["peak_rss_bytes"] for item in group),
                "network_requests": sum(item["network_requests"] for item in group),
            }
    for source in sorted({item["source"] for item in values}):
        group = [item for item in values if item["source"] == source and item["phase"] in {"evidence_collection", "sample_acquisition"}]
        failures = [item for item in group if not item["success"]]
        summary["access"][source] = {"attempts": len(group), "failures": len(failures), "failure_rate": len(failures) / len(group) if group else None, "failure_categories": sorted({item["failure_category"] for item in failures})}
    return summary


def run(config_path: Path, *, reset_cache: bool) -> Path:
    config = load_config(config_path)
    output = ROOT / config["output_directory"]
    cache = ResponseCache(output / "cache")
    if reset_cache:
        cache.clear()
    run_id = f"m0-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    all_records: list[MeasurementRecord] = []
    for condition in ("cold", "warm"):
        all_records.extend(candidate_events(run_id, condition, config, cache))
        all_records.extend(evidence_events(run_id, condition, config, cache))
        for dataset in config["dataset_records"]:
            sample, items = sample_event(run_id, condition, dataset, cache, config["sample_cap"])
            all_records.append(sample)
            all_records.append(diagnostic_event(run_id, condition, dataset, items, config["diagnostic"]["id"]))
    result_dir = output / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "records.jsonl").write_text("".join(json.dumps(record.as_dict(), sort_keys=True) + "\n" for record in all_records), encoding="utf-8")
    (result_dir / "summary.json").write_text(json.dumps(summarise(all_records, runtime_metadata(config_path, config)), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result_dir
