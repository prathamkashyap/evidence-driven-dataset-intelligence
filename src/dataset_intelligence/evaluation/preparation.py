"""One-time M8 corpus acquisition client for the frozen M1-M5 interfaces.

This module is deliberately separate from the offline M8 evaluation harness.  It permits
only the fixed, cached acquisition plan in ``configs/m8_corpus_preparation.json`` and
does not modify any M0-M7 artifact.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import zipfile
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dataset_intelligence.evidence.harvester import EvidenceHarvester
from dataset_intelligence.evidence.ledger import EvidenceLedger, LedgerEntry
from dataset_intelligence.fingerprinting.pipeline import compute_fingerprint
from dataset_intelligence.fingerprinting.schema import DatasetFingerprint
from dataset_intelligence.ingestion.adapters import ADAPTERS
from dataset_intelligence.ingestion.schema import CanonicalDataset
from dataset_intelligence.m0.cache import CachedResponse, ResponseCache
from dataset_intelligence.utility.estimator import TaskUtilityEstimate, TaskUtilityEstimator
from dataset_intelligence.utility.specification import TaskSpecification


M8_PREPARATION_VERSION = "1.0"
EXPECTED_TARGET_IDS = (
    "hf_imdb", "hf_glue_sst2", "hf_tweet_eval_sentiment", "hf_dbpedia_14",
    "hf_cifar10", "hf_fashion_mnist", "openml_diabetes", "openml_titanic",
    "openml_credit_g", "openml_mnist_784", "uci_heart_disease",
    "uci_breast_cancer_wisconsin", "uci_adult", "kaggle_titanic",
    "kaggle_heart_disease_uci",
)
MAX_HARD_BYTES = 64 * 1024 * 1024


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def canonical_json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("M8 corpus-preparation config schema_version must be 1.")
    targets = config.get("targets", [])
    if tuple(item.get("id") for item in targets) != EXPECTED_TARGET_IDS:
        raise ValueError("M8 target list or its preregistered order differs from the frozen protocol.")
    if [item.get("order") for item in targets] != list(range(11, 26)):
        raise ValueError("M8 target orders must be the fixed range 11 through 25.")
    limits = config.get("sample_limits", {})
    if limits.get("max_records") != 32:
        raise ValueError("M8 must retain at most 32 sample records.")
    if limits.get("hard_cap_bytes") != MAX_HARD_BYTES:
        raise ValueError("M8 hard sample cap must remain the M0 64 MiB limit.")
    if limits.get("soft_target_bytes", 0) > MAX_HARD_BYTES:
        raise ValueError("M8 soft sample target cannot exceed the M0 hard cap.")
    return config


def _bounded_fetch(url: str, cache: ResponseCache, *, max_bytes: int, timeout_seconds: int) -> tuple[CachedResponse, str, int]:
    """Fetch a permitted public URL once, caching successes and terminal HTTP errors."""
    cached = cache.get(url)
    if cached is not None:
        return cached, "warm", 0
    request = Request(url, headers={"User-Agent": "EDDI-M8/1.0 (public no-auth corpus preparation)"})
    try:
        with urlopen(request, timeout=timeout_seconds) as result:  # noqa: S310 -- URLs are fixed in committed config or source metadata.
            response = CachedResponse(result.read(max_bytes), result.status, None, utc_now())
    except HTTPError as error:
        response = CachedResponse(error.read(min(max_bytes, 65536)), error.code, "http_error", utc_now())
    except URLError as error:
        response = CachedResponse(b"", None, type(error.reason).__name__, utc_now())
    cache.put(url, response)
    return response, "cold", 1


def _json_body(response: CachedResponse) -> dict[str, Any]:
    if response.status_code is None or response.status_code >= 400:
        raise ValueError(f"metadata endpoint failed: HTTP {response.status_code or response.error_kind}")
    value = json.loads(response.body.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("metadata endpoint did not return a JSON object")
    return value


def metadata_url(target: dict[str, Any]) -> str:
    source, source_id = target["source"], target["source_dataset_id"]
    if source == "huggingface":
        return f"https://huggingface.co/api/datasets/{source_id}"
    if source == "openml":
        return f"https://www.openml.org/api/v1/json/data/{source_id}"
    if source == "uci":
        return f"https://archive.ics.uci.edu/api/dataset?id={source_id}"
    if source == "kaggle":
        return f"https://www.kaggle.com/api/v1/datasets/view/{source_id}"
    raise ValueError(f"Unsupported source: {source}")


def _uci_raw(payload: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise ValueError("UCI metadata has no usable data object")
    variables = payload.get("variables") or []
    target_count = len([item for item in variables if isinstance(item, dict) and str(item.get("role", "")).lower() == "target"])
    return {
        "id": str(data.get("uci_id") or target["source_dataset_id"]),
        "name": data.get("name"),
        "url": data.get("repository_url") or f"https://archive.ics.uci.edu/dataset/{target['source_dataset_id']}",
        "description": data.get("abstract") or data.get("additional_info"),
        "tasks": data.get("tasks") or [],
        "modalities": ["tabular"],
        "tags": data.get("area") or [],
        "sample_count": data.get("num_instances"),
        "class_count": data.get("num_classes") or target_count or None,
        "license_claim": data.get("license"),
        "formats": ["csv"],
        "version": str(data.get("uci_id") or target["source_dataset_id"]),
    }


def normalize_metadata(target: dict[str, Any], payload: dict[str, Any], observed_at: str, *, raw_reference: str, cache_state: str, response: CachedResponse) -> CanonicalDataset:
    source = target["source"]
    raw = payload
    if source == "uci":
        raw = _uci_raw(payload, target)
    elif source == "kaggle":
        raw = dict(payload)
        raw.setdefault("ref", raw.get("datasetRef") or target["source_dataset_id"])
        raw.setdefault("title", raw.get("title") or raw.get("datasetTitle"))
        raw.setdefault("subtitle", raw.get("subtitle") or raw.get("description"))

    record = ADAPTERS[source]().normalize(raw, observed_at)
    access = dict(record.access)
    access.update({
        "cache_status": cache_state,
        "observed_at": observed_at,
        "source_response_identifiers": {
            "metadata_sha256": hashlib.sha256(response.body).hexdigest(),
            "metadata_status_code": response.status_code,
            "metadata_url": metadata_url(target),
        },
    })
    provenance = [{
        "source_url": metadata_url(target),
        "observed_at": observed_at,
        "adapter_version": record.adapter_version,
        "raw_reference": raw_reference,
        "raw_retained": True,
    }]
    final = replace(record, access=access, provenance=provenance)
    final.validate()
    return final


def _decode_scalar(value: str) -> Any:
    text = value.strip().strip("'\"")
    if text == "?":
        return None
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def parse_arff_rows(body: bytes, *, max_records: int) -> list[dict[str, Any]]:
    attributes: list[str] = []
    rows: list[dict[str, Any]] = []
    in_data = False
    for raw_line in body.decode("utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("%"):
            continue
        if line.lower().startswith("@attribute"):
            pieces = line.split(maxsplit=2)
            if len(pieces) >= 2:
                attributes.append(pieces[1].strip("'\""))
        elif line.lower() == "@data":
            in_data = True
        elif in_data:
            values = [_decode_scalar(value) for value in line.split(",")]
            names = attributes if len(attributes) == len(values) else [f"col_{index}" for index in range(len(values))]
            rows.append(dict(zip(names, values)))
            if len(rows) >= max_records:
                break
    return rows


def parse_hf_rows(body: bytes, *, max_records: int) -> list[Any]:
    payload = json.loads(body.decode("utf-8"))
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    return [item.get("row", item) if isinstance(item, dict) else item for item in rows[:max_records]]


def parse_uci_zip_rows(body: bytes, sample: dict[str, Any], *, max_records: int) -> list[dict[str, Any]]:
    member = sample.get("member")
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = archive.namelist()
        selected = next((name for name in names if name.endswith(member)), None) if member else None
        if not selected:
            raise ValueError(f"configured UCI zip member not found: {member}")
        raw_lines = archive.read(selected).decode("utf-8", errors="replace").splitlines()
    columns_by_target = {
        "num": ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num"],
        "diagnosis": ["id", "diagnosis"] + [f"feature_{index}" for index in range(30)],
        "income": ["age", "workclass", "fnlwgt", "education", "education_num", "marital_status", "occupation", "relationship", "race", "sex", "capital_gain", "capital_loss", "hours_per_week", "native_country", "income"],
    }
    columns = columns_by_target.get(sample.get("target_column"), [])
    records: list[dict[str, Any]] = []
    for line in raw_lines:
        if not line.strip() or line.lstrip().startswith("|"):
            continue
        values = [_decode_scalar(value) for value in line.split(",")]
        names = columns if len(columns) == len(values) else [f"col_{index}" for index in range(len(values))]
        records.append(dict(zip(names, values)))
        if len(records) >= max_records:
            break
    return records


def sample_request(target: dict[str, Any], metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    sample = target["sample"]
    kind = sample.get("kind")
    if kind == "not_attempted":
        return None, None
    if kind == "hf_rows":
        dataset = quote(target["source_dataset_id"], safe="")
        return (f"https://datasets-server.huggingface.co/rows?dataset={dataset}&config={quote(sample['config'])}&split={quote(sample['split'])}&offset=0&length=32", kind)
    if kind == "openml_arff":
        data = metadata.get("data_set_description", metadata)
        url = data.get("url") if isinstance(data, dict) else None
        return (str(url) if url else None, kind)
    if kind == "uci_zip":
        return sample.get("url"), kind
    raise ValueError(f"Unsupported sample kind: {kind}")


def parse_sample(body: bytes, kind: str, sample: dict[str, Any], max_records: int) -> list[Any]:
    if kind == "hf_rows":
        return parse_hf_rows(body, max_records=max_records)
    if kind == "openml_arff":
        return parse_arff_rows(body, max_records=max_records)
    if kind == "uci_zip":
        return parse_uci_zip_rows(body, sample, max_records=max_records)
    raise ValueError(f"Unsupported sample parser: {kind}")


def _primary_modality(record: CanonicalDataset) -> str:
    modalities = record.semantics.get("modality") or []
    if isinstance(modalities, str):
        modalities = [modalities]
    for value in modalities:
        if value in {"tabular", "text", "image", "multimodal"}:
            return value
    return "unknown"


def _append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def _latest_events(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return latest
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            latest[entry["target_id"]] = entry
    return latest


def _write_jsonl(path: Path, objects: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in objects:
            data = item.as_dict() if hasattr(item, "as_dict") else item
            handle.write(json.dumps(data, sort_keys=True) + "\n")


def _read_jsonl(path: Path, constructor: Callable[..., Any]) -> list[Any]:
    if not path.is_file():
        return []
    return [constructor(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_exclusion_log(path: Path, exclusions: list[dict[str, Any]]) -> None:
    """Write the protocol-required, human-inspectable terminal exclusion record."""
    lines = [
        "# M8 Corpus Acquisition Exclusions",
        "",
        "This is the terminal log for the one-time M8 corpus acquisition/preparation phase. "
        "Targets are not substituted or retried with altered parameters.",
        "",
    ]
    if not exclusions:
        lines.append("No targets were excluded.")
    else:
        lines.extend([
            "| Order | Target | Source | Reason |",
            "|---:|---|---|---|",
        ])
        for event in sorted(exclusions, key=lambda item: item["order"]):
            reason = str(event.get("failure_reason", "unknown")).replace("|", "\\|")
            lines.append(f"| {event['order']} | `{event['target_id']}` | {event['source']} | {reason} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_frozen_m1_to_m4(root: Path) -> tuple[list[CanonicalDataset], list[LedgerEntry], list[DatasetFingerprint]]:
    """Load frozen input artifacts as read-only values for a distinct M8 output."""
    records = _read_jsonl(root / "experiments/m1/results/development_corpus.jsonl", CanonicalDataset)
    entries = _read_jsonl(root / "experiments/m3/results/evidence_ledger.jsonl", LedgerEntry)
    fingerprints = _read_jsonl(root / "experiments/m4/results/dataset_fingerprints.jsonl", DatasetFingerprint)
    return records, entries, fingerprints


def prepare_corpus(root: Path, config: dict[str, Any], *, fetcher: Callable[..., tuple[CachedResponse, str, int]] = _bounded_fetch) -> dict[str, Any]:
    """Execute the fixed, one-attempt preparation plan and write M8-scoped artifacts."""
    output = root / config["output_directory"]
    cache = ResponseCache(root / config["cache_directory"])
    log_path = output / "corpus" / "acquisition_attempts.jsonl"
    latest = _latest_events(log_path)
    config_hash = canonical_json_hash(config)
    max_records = config["sample_limits"]["max_records"]
    max_bytes = min(config["sample_limits"]["soft_target_bytes"], config["sample_limits"]["hard_cap_bytes"])
    timeout = config["request_timeout_seconds"]

    additional_corpus_path = output / "corpus" / "additional_corpus.jsonl"
    additional_ledger_path = output / "evidence" / "additional_evidence_ledger.jsonl"
    additional_fingerprints_path = output / "fingerprints" / "additional_fingerprints.jsonl"
    acquired = _read_jsonl(additional_corpus_path, CanonicalDataset)
    ledger = EvidenceLedger(_read_jsonl(additional_ledger_path, LedgerEntry))
    fingerprints = _read_jsonl(additional_fingerprints_path, DatasetFingerprint)
    events: list[dict[str, Any]] = []

    for target in config["targets"]:
        prior = latest.get(target["id"])
        if prior:
            if prior.get("status") == "started":
                event = {**prior, "status": "excluded", "finished_at": utc_now(), "failure_category": "interrupted_attempt_no_retry", "failure_reason": "A prior attempt started without a terminal outcome; the one-attempt rule prohibits a new request."}
                _append_event(log_path, event)
                events.append(event)
            else:
                events.append(prior)
            continue

        started = {"target_id": target["id"], "order": target["order"], "source": target["source"], "source_dataset_id": target["source_dataset_id"], "status": "started", "started_at": utc_now(), "config_hash": config_hash}
        _append_event(log_path, started)
        network_requests = 0
        try:
            meta_url = metadata_url(target)
            meta_response, meta_cache, count = fetcher(meta_url, cache, max_bytes=max_bytes, timeout_seconds=timeout)
            network_requests += count
            payload = _json_body(meta_response)
            observed_at = meta_response.fetched_at
            raw_reference = f"m8:{target['id']}:metadata:sha256:{hashlib.sha256(meta_response.body).hexdigest()}"
            record = normalize_metadata(target, payload, observed_at, raw_reference=raw_reference, cache_state=meta_cache, response=meta_response)

            sample_url, sample_kind = sample_request(target, payload)
            sample_rows: list[Any] | None = None
            sample_error: str | None = None
            bytes_examined = 0
            sample_cache = "not_attempted"
            if sample_url and sample_kind:
                sample_response, sample_cache, count = fetcher(sample_url, cache, max_bytes=max_bytes, timeout_seconds=timeout)
                network_requests += count
                bytes_examined = len(sample_response.body)
                if sample_response.status_code is None or sample_response.status_code >= 400:
                    sample_error = f"HTTP {sample_response.status_code or sample_response.error_kind} from configured sample endpoint"
                else:
                    try:
                        sample_rows = parse_sample(sample_response.body, sample_kind, target["sample"], max_records)
                    except (ValueError, OSError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
                        sample_error = f"sample_parse_error: {type(error).__name__}: {error}"
            elif target["source"] == "kaggle":
                sample_error = "Kaggle bounded sample access is unsupported without credentials under frozen M0 policy."

            entries = EvidenceHarvester().harvest_all(record, raw_sample_data=sample_rows, sample_url=sample_url, raw_reference=raw_reference, error_reason=sample_error, bytes_examined=bytes_examined)
            for entry in entries:
                ledger.add_entry(entry)
            fp = compute_fingerprint(
                dataset_id=record.internal_id,
                primary_modality=("unsupported" if target["source"] == "kaggle" else _primary_modality(record)),
                raw_sample_records=sample_rows,
                observed_at=record.access["observed_at"],
                source_evidence_entry_ids=[entry.entry_id for entry in entries],
                target_column_name=target["sample"].get("target_column"),
                acquisition_method=sample_kind or "policy_limited_no_sample",
                raw_reference=raw_reference,
                error_reason=sample_error,
                bytes_observed=bytes_examined,
            )
            acquired.append(record)
            fingerprints.append(fp)
            event = {**started, "status": "included", "finished_at": utc_now(), "canonical_dataset_id": record.internal_id, "raw_reference": raw_reference, "metadata_cache_state": meta_cache, "sample_cache_state": sample_cache, "network_requests": network_requests, "records_acquired": len(sample_rows or []), "bytes_acquired": bytes_examined, "fingerprint_id": fp.fingerprint_id}
        except (ValueError, KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as error:
            event = {**started, "status": "excluded", "finished_at": utc_now(), "failure_category": "metadata_or_schema_failure", "failure_reason": f"{type(error).__name__}: {error}", "network_requests": network_requests}
        _append_event(log_path, event)
        events.append(event)

    # A prior terminal event is sufficient evidence of one attempt, but the final output is
    # only valid when all current targets have records in this run or a deliberately resumed run.
    _write_jsonl(additional_corpus_path, acquired)
    _write_jsonl(additional_ledger_path, ledger.entries())
    _write_jsonl(additional_fingerprints_path, fingerprints)

    task_specs = {
        name: TaskSpecification.create(
            task_type=value.get("task_type", "unknown"), primary_modality=value.get("primary_modality", "unknown"), domain=value.get("domain"),
            target_requirements=value.get("target_requirements"), input_constraints=value.get("input_constraints"),
            scale_constraints=value.get("scale_constraints"), governance_constraints=value.get("governance_constraints"),
            access_constraints=value.get("access_constraints"), explicit_user_constraints=value.get("explicit_user_constraints"),
            unresolved_requirements=value.get("unresolved_requirements"), raw_query=value.get("raw_query"),
        ) for name, value in config["task_specifications"].items()
    }
    estimator = TaskUtilityEstimator()
    frozen_records, frozen_entries, frozen_fingerprints = _load_frozen_m1_to_m4(root)
    all_records = frozen_records + acquired
    all_ledger_entries = frozen_entries + ledger.entries()
    all_fingerprints = frozen_fingerprints + fingerprints
    estimates: list[TaskUtilityEstimate] = []
    all_ledger = EvidenceLedger(all_ledger_entries)
    entries_by_dataset = {record.internal_id: all_ledger.get_entries_for_dataset(record.internal_id) for record in all_records}
    fp_by_dataset = {fp.dataset_id: fp for fp in all_fingerprints}
    for task in task_specs.values():
        for record in all_records:
            estimates.append(estimator.evaluate(record, task, m3_entries=entries_by_dataset[record.internal_id], fingerprint=fp_by_dataset[record.internal_id], baseline_mode="baseline_c", evaluated_at=utc_now(), config_hash=config_hash))
    _write_jsonl(output / "utility" / "benchmark_utility_estimates.jsonl", estimates)

    latest_after = _latest_events(log_path)
    exclusions = [event for target_id, event in latest_after.items() if event.get("status") == "excluded"]
    _write_exclusion_log(root / "data/benchmarks/m8_corpus_exclusions.md", exclusions)
    _write_jsonl(output / "corpus" / "benchmark_corpus.jsonl", all_records)
    _write_jsonl(output / "evidence" / "benchmark_evidence_ledger.jsonl", all_ledger.entries())
    _write_jsonl(output / "fingerprints" / "benchmark_fingerprints.jsonl", all_fingerprints)
    summary = {
        "schema_version": 1,
        "preparation_version": M8_PREPARATION_VERSION,
        "acquisition_id": config["acquisition_id"],
        "config_hash": config_hash,
        "random_seed": config["seed"],
        "sample_limits": config["sample_limits"],
        "protocol_commit": config["protocol_commit"],
        "frozen_m0_m7_commit": config["frozen_m0_m7_commit"],
        "attempted_target_ids": [target["id"] for target in config["targets"]],
        "included_dataset_ids": [record.internal_id for record in acquired],
        "included_additional_count": len(acquired),
        "final_benchmark_corpus_count": len(all_records),
        "excluded_count": len(exclusions),
        "network_requests_during_single_live_attempt_pass": sum(int(event.get("network_requests", 0)) for event in latest_after.values()),
        "exclusions": exclusions,
        "artifact_counts": {"canonical_records": len(all_records), "ledger_entries": len(all_ledger), "fingerprints": len(all_fingerprints), "utility_estimates": len(estimates)},
        "environment": {"python": sys.version, "platform": platform.platform()},
        "completed_at": utc_now(),
    }
    summary_path = output / "corpus" / "preparation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
