"""Fresh-instance corruption helpers and robustness evaluation for preregistered M8 robustness suites."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

from dataset_intelligence.evaluation.metrics import mean, set_jaccard


def _remove_path(record: dict[str, Any], dotted_path: str) -> None:
    parent: dict[str, Any] = record
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        next_value = parent.get(part)
        if not isinstance(next_value, dict):
            return
        parent = next_value
    parent.pop(parts[-1], None)


def fresh_corrupted_record(record: Any, suite: dict[str, Any], *, severity_index: int = 0) -> Any:
    """Return a fresh record instance for one declarative M8 fixture suite.

    The source record and all frozen artifact objects remain untouched. The helper
    only interprets fixture operations already committed in the benchmark inputs.
    """
    payload = deepcopy(record.as_dict() if hasattr(record, "as_dict") else record)
    suite_id = suite["suite_id"]
    if suite_id == "metadata_omission_v1":
        paths = list(suite["field_paths"])
        rates = list(suite["omission_rates"])
        rate = rates[min(severity_index, len(rates) - 1)]
        count = max(1, round(len(paths) * rate))
        for path in sorted(paths)[:count]:
            _remove_path(payload, path)
    elif suite_id == "license_conflict_v1":
        governance = payload.setdefault("governance", {})
        existing = governance.get("license_claim")
        injected = suite["injected_claims"][severity_index % len(suite["injected_claims"])]
        governance["license_claim"] = existing or injected
        claims = payload.setdefault("claims", {})
        entries = list(claims.get("license", []))
        entries.append({
            "value": injected,
            "source_url": "m8://corruption/license_conflict",
            "source_field": "injected_license_claim",
            "observed_at": "2026-09-12T00:00:00+00:00",
            "state": "conflicting",
        })
        claims["license"] = entries
    elif suite_id == "modality_corruption_v1":
        replacement = suite["replacement_values"][severity_index % len(suite["replacement_values"])]
        payload.setdefault("semantics", {})["modality"] = [replacement]
    elif suite_id == "endpoint_failure_v1":
        status = suite["http_status_codes"][severity_index % len(suite["http_status_codes"])]
        access = payload.setdefault("access", {})
        access["sample_accessible"] = "unsupported_or_policy_limited" if status == 403 else "failed"
        access["m8_simulated_endpoint_status"] = status
    else:
        raise ValueError(f"Unsupported M8 corruption suite: {suite_id}")

    # CanonicalDataset is imported lazily so this module remains a pure fixture client.
    from dataset_intelligence.ingestion.schema import CanonicalDataset

    fresh = CanonicalDataset(**payload)
    fresh.validate()
    if fresh is record:
        raise AssertionError("M8 corruption must construct a fresh CanonicalDataset instance.")
    return fresh


def fixture_target_records(records_by_id: dict[str, Any], suite: dict[str, Any]) -> list[Any]:
    """Resolve fixture targets deterministically and fail rather than silently drop one."""
    return [records_by_id[dataset_id] for dataset_id in suite["target_dataset_ids"]]


def fresh_corrupted_evidence(entries: list[Any], record: Any, suite: dict[str, Any], *, severity_index: int = 0) -> list[Any]:
    """Return a new evidence list where a fixture explicitly requires one.

    Only the license-conflict case needs an M3-shaped observation for the frozen
    M5 governance client to expose its existing ``conflicting`` state. Existing
    immutable entries are retained by identity and never edited.
    """
    copied = list(entries)
    if suite["suite_id"] != "license_conflict_v1":
        return copied
    from dataset_intelligence.evidence.ledger import LedgerEntry

    claim = suite["injected_claims"][severity_index % len(suite["injected_claims"])]
    copied.append(LedgerEntry.create(
        dataset_id=record.internal_id,
        claim_type="license",
        claim_value=claim,
        evidence_type="metadata_claim",
        source="m8_corruption_fixture",
        source_field="injected_license_claim",
        observation_state="single_source_claim",
        procedure="m8_fresh_license_conflict_fixture",
        observed_at="2026-09-12T00:00:00+00:00",
        source_url="m8://corruption/license_conflict",
        raw_reference="m8_corruption_fixtures.json",
    ))
    return copied


def evaluate_robustness(
    task_specs: dict[str, Any],
    clean_records: list[Any],
    clean_utility_estimates_by_task: dict[str, dict[str, Any]],
    clean_recommendation_sets: dict[str, Any],
    popularity_profiles: dict[str, Any],
    fingerprints: dict[str, Any],
    evidence_entries: dict[str, list[Any]],
    corruption_fixtures: dict[str, Any],
    ground_truth_labels: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute all declarative corruption stress suites and compute degradation metrics."""
    from dataset_intelligence.ranking.pipeline import RecommendationEngine
    from dataset_intelligence.utility.estimator import TaskUtilityEstimator

    estimator = TaskUtilityEstimator()
    engine = RecommendationEngine(config=config)
    target_k = (config or {}).get("target_k", 3)

    clean_records_by_id = {getattr(r, "internal_id", ""): r for r in clean_records}
    manifest_tasks = ground_truth_labels.get("tasks", {})
    manifest_datasets = ground_truth_labels.get("dataset_order", [getattr(r, "internal_id", "") for r in clean_records])

    total_trials = 0
    crash_count = 0
    suite_summaries: list[dict[str, Any]] = []

    for suite in corruption_fixtures.get("suites", []):
        suite_id = suite["suite_id"]
        target_ids = set(suite["target_dataset_ids"])

        # Determine severity levels count
        if "omission_rates" in suite:
            num_severities = len(suite["omission_rates"])
        elif "injected_claims" in suite:
            num_severities = len(suite["injected_claims"])
        elif "replacement_values" in suite:
            num_severities = len(suite["replacement_values"])
        elif "http_status_codes" in suite:
            num_severities = len(suite["http_status_codes"])
        else:
            num_severities = 1

        severity_results: list[dict[str, Any]] = []

        for sev_idx in range(num_severities):
            total_trials += 1
            trial_crashed = False

            try:
                # 1. Build fresh corrupted records and evidence
                corrupted_records: list[Any] = []
                corrupted_evidence_by_id: dict[str, list[Any]] = {}

                for rec in clean_records:
                    did = getattr(rec, "internal_id", "")
                    if did in target_ids:
                        fresh_rec = fresh_corrupted_record(rec, suite, severity_index=sev_idx)
                        corrupted_records.append(fresh_rec)
                        clean_evid = evidence_entries.get(did, [])
                        fresh_evid = fresh_corrupted_evidence(clean_evid, fresh_rec, suite, severity_index=sev_idx)
                        corrupted_evidence_by_id[did] = fresh_evid
                    else:
                        corrupted_records.append(rec)
                        corrupted_evidence_by_id[did] = evidence_entries.get(did, [])

                # 2. Re-evaluate utility estimates with M5 client for corrupted records
                corrupted_estimates_by_task: dict[str, dict[str, Any]] = {}
                state_transitions = 0
                gate_tp = gate_fp = gate_fn = gate_tn = 0

                for task_name, spec in task_specs.items():
                    tid = getattr(spec, "task_id", "")
                    task_estimates: dict[str, Any] = {}
                    for rec in corrupted_records:
                        did = getattr(rec, "internal_id", "")
                        clean_est = clean_utility_estimates_by_task.get(tid, {}).get(did)
                        if did in target_ids:
                            # Re-evaluate with fresh corrupted record and evidence
                            corrupted_est = estimator.evaluate(
                                record=rec,
                                task_spec=spec,
                                m3_entries=corrupted_evidence_by_id[did],
                                fingerprint=fingerprints.get(did),
                                baseline_mode="baseline_c",
                            )
                            task_estimates[did] = corrupted_est

                            # Count transitions to unknown, conflicting, or failed
                            if clean_est:
                                for comp_name, clean_comp in getattr(clean_est, "components", {}).items():
                                    corr_comp = getattr(corrupted_est, "components", {}).get(comp_name)
                                    clean_state = getattr(clean_comp, "epistemic_state", "")
                                    corr_state = getattr(corr_comp, "epistemic_state", "")
                                    if clean_state not in {"unknown", "conflicting", "failed"} and corr_state in {"unknown", "conflicting", "failed"}:
                                        state_transitions += 1

                            # Check hard gating precision/recall for fatal corruptions
                            is_fatally_corrupt = (
                                suite_id == "modality_corruption_v1"
                                and getattr(spec, "primary_modality", "unknown") != "unknown"
                            )
                            if is_fatally_corrupt:
                                if getattr(corrupted_est, "hard_gated", False):
                                    gate_tp += 1
                                else:
                                    gate_fn += 1
                            else:
                                if getattr(corrupted_est, "hard_gated", False) and not getattr(clean_est, "hard_gated", False):
                                    gate_fp += 1
                                else:
                                    gate_tn += 1
                        else:
                            task_estimates[did] = clean_est
                    corrupted_estimates_by_task[tid] = task_estimates

                # 3. Recommend with R3 on corrupted corpus
                jaccard_list: list[float] = []
                utility_delta_list: list[float] = []
                false_positives = 0

                for task_name, spec in task_specs.items():
                    tid = getattr(spec, "task_id", "")
                    rec_set = engine.recommend(
                        task_spec=spec,
                        candidate_records=corrupted_records,
                        utility_estimates=corrupted_estimates_by_task[tid],
                        popularity_profiles=popularity_profiles,
                        fingerprints=fingerprints,
                        evidence_entries=corrupted_evidence_by_id,
                        baseline_mode="r3_diversified_set",
                        target_k=target_k,
                    )
                    clean_set = clean_recommendation_sets.get(task_name)
                    clean_ids = list(getattr(clean_set, "selected_dataset_ids", ()))
                    corr_ids = list(rec_set.selected_dataset_ids)

                    j = set_jaccard(clean_ids, corr_ids)
                    if j is not None:
                        jaccard_list.append(j)

                    clean_u = getattr(clean_set, "mean_set_utility", 0.0)
                    corr_u = rec_set.mean_set_utility
                    utility_delta_list.append(corr_u - clean_u)

                    # Check false-positive recommendations against ground-truth labels
                    t_labels = manifest_tasks.get(task_name, {}).get("binary_suitability", [])
                    for did in corr_ids:
                        if did in target_ids:
                            # If corrupted target was recommended, check if it's incompatible (y=0)
                            if did in manifest_datasets:
                                d_idx = manifest_datasets.index(did)
                                if d_idx < len(t_labels) and t_labels[d_idx] == 0:
                                    false_positives += 1

                precision = (gate_tp / (gate_tp + gate_fp)) if (gate_tp + gate_fp) > 0 else 1.0
                recall = (gate_tp / (gate_tp + gate_fn)) if (gate_tp + gate_fn) > 0 else 1.0

                severity_results.append({
                    "severity_index": sev_idx,
                    "crashed": False,
                    "mean_utility_delta": mean(utility_delta_list),
                    "set_jaccard_overlap": mean(jaccard_list),
                    "hard_gating_precision": round(precision, 4),
                    "hard_gating_recall": round(recall, 4),
                    "epistemic_state_transition_count": state_transitions,
                    "false_positive_recommendation_count": false_positives,
                })

            except Exception as error:
                trial_crashed = True
                crash_count += 1
                severity_results.append({
                    "severity_index": sev_idx,
                    "crashed": True,
                    "error": f"{type(error).__name__}: {error}",
                })

        suite_summaries.append({
            "suite_id": suite_id,
            "target_dataset_ids": suite["target_dataset_ids"],
            "severities_evaluated": len(severity_results),
            "results_by_severity": severity_results,
        })

    crash_rate = crash_count / total_trials if total_trials > 0 else 0.0

    return {
        "status": "robust" if crash_rate == 0.0 else "failed_robustness",
        "total_trials": total_trials,
        "crash_count": crash_count,
        "crash_rate": round(crash_rate, 4),
        "crash_rate_criterion_met": crash_rate == 0.0,
        "suite_summaries": suite_summaries,
    }
