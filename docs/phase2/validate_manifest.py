#!/usr/bin/env python3
"""Check cross-record integrity for a Phase II benchmark manifest.

Record-shape validation is defined by schemas/benchmark-manifest.schema.json.
This dependency-free check validates references, uniqueness, pair coverage,
annotation coverage, and counts once a manifest is populated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def validate(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def unique_index(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        for position, row in enumerate(rows):
            value = row.get(key)
            if not isinstance(value, str) or not value:
                errors.append(f"{label}[{position}] has no non-empty {key}")
            elif value in index:
                errors.append(f"duplicate {label} {key}: {value}")
            else:
                index[value] = row
        return index

    targets = manifest.get("targets", {})
    tasks = manifest.get("tasks", [])
    candidates = manifest.get("candidates", [])
    pairs = manifest.get("task_candidate_pairs", [])
    annotations = manifest.get("annotations", [])
    provenance = manifest.get("provenance_records", [])

    task_by_id = unique_index(tasks, "task_id", "tasks")
    candidate_by_id = unique_index(candidates, "candidate_id", "candidates")
    pair_by_id = unique_index(pairs, "pair_id", "task_candidate_pairs")
    annotation_by_id = unique_index(annotations, "annotation_id", "annotations")
    provenance_by_id = unique_index(provenance, "provenance_id", "provenance_records")

    pair_keys: set[tuple[str, str]] = set()
    pairs_by_task: dict[str, set[str]] = {}
    pairs_by_id: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        pair_id = pair.get("pair_id")
        task_id = pair.get("task_id")
        candidate_id = pair.get("candidate_id")
        if task_id not in task_by_id:
            errors.append(f"pair {pair_id} references unknown task_id {task_id}")
        if candidate_id not in candidate_by_id:
            errors.append(f"pair {pair_id} references unknown candidate_id {candidate_id}")
        key = (task_id, candidate_id)
        if key in pair_keys:
            errors.append(f"duplicate task-candidate pair {key}")
        pair_keys.add(key)
        if isinstance(task_id, str) and isinstance(candidate_id, str):
            pairs_by_task.setdefault(task_id, set()).add(candidate_id)
        if isinstance(pair_id, str):
            pairs_by_id[pair_id] = pair

    for task_id, task in task_by_id.items():
        listed = task.get("candidate_ids", [])
        if len(listed) != len(set(listed)):
            errors.append(f"task {task_id} repeats candidate_ids")
        missing_candidates = set(listed) - candidate_by_id.keys()
        if missing_candidates:
            errors.append(f"task {task_id} references unknown candidates: {sorted(missing_candidates)}")
        pair_candidates = pairs_by_task.get(task_id, set())
        if pair_candidates != set(listed):
            errors.append(f"task {task_id} candidate_ids do not match its task_candidate_pairs")
        candidate_target = targets.get("candidates_per_task", 0)
        if len(listed) > candidate_target:
            errors.append(f"task {task_id} exceeds candidates_per_task target {candidate_target}")
        elif len(listed) < candidate_target and manifest.get("status") != "proposed":
            documented_shortfall = any(
                row.get("record_type") == "task"
                and row.get("record_id") == task_id
                and row.get("reason_code") == "candidate_pool_shortfall"
                for row in manifest.get("exclusions", [])
            )
            if not documented_shortfall:
                errors.append(f"task {task_id} is below candidates_per_task target without a candidate_pool_shortfall exclusion")

    annotations_by_pair: dict[str, list[dict[str, Any]]] = {}
    for annotation in annotations:
        annotation_id = annotation.get("annotation_id")
        pair_id = annotation.get("pair_id")
        if pair_id not in pair_by_id:
            errors.append(f"annotation {annotation_id} references unknown pair_id {pair_id}")
        else:
            annotations_by_pair.setdefault(pair_id, []).append(annotation)
        resolves = annotation.get("resolves_annotation_ids", [])
        unknown = set(resolves) - annotation_by_id.keys()
        if unknown:
            errors.append(f"annotation {annotation_id} resolves unknown annotation IDs: {sorted(unknown)}")

    for pair_id in pair_by_id:
        rows = annotations_by_pair.get(pair_id, [])
        primary = [row for row in rows if row.get("judgment_role") == "primary"]
        assessor_ids = [row.get("assessor_id") for row in primary]
        if len(assessor_ids) != len(set(assessor_ids)):
            errors.append(f"pair {pair_id} has duplicate primary assessor IDs")
        if manifest.get("status") in {"annotated", "evaluated"} and len(set(assessor_ids)) < 2:
            errors.append(f"pair {pair_id} has fewer than two independent primary assessors")

    referenced_provenance: set[str] = set()
    for record in [*tasks, *candidates, *annotations]:
        referenced_provenance.update(record.get("source_provenance_ids", []))
        referenced_provenance.update(record.get("provenance_ids", []))
    for pair in pairs:
        referenced_provenance.update(pair.get("constraint_evidence_ids", []))
    unknown_provenance = referenced_provenance - provenance_by_id.keys()
    if unknown_provenance:
        errors.append(f"references to missing provenance records: {sorted(unknown_provenance)}")

    for annotation in annotations:
        for assessment in annotation.get("constraint_assessments", []):
            unknown = set(assessment.get("provenance_ids", [])) - provenance_by_id.keys()
            if unknown:
                errors.append(f"annotation {annotation.get('annotation_id')} has missing constraint provenance: {sorted(unknown)}")

    status = manifest.get("status")
    if status == "proposed":
        if any((tasks, candidates, pairs, annotations, provenance, manifest.get("exclusions", []))):
            errors.append("a proposed design template must not contain benchmark records")
        if targets.get("task_count", 0) != sum(targets.get("tasks_per_modality", {}).values()):
            errors.append("proposed task_count does not equal tasks_per_modality total")
        if targets.get("task_count", 0) != sum(targets.get("tasks_per_type", {}).values()):
            errors.append("proposed task_count does not equal tasks_per_type total")
        if targets.get("task_count", 0) != sum(targets.get("split_task_counts", {}).values()):
            errors.append("proposed task_count does not equal split_task_counts total")
        if targets.get("task_count", 0) * targets.get("candidates_per_task", 0) != targets.get("task_candidate_pair_count"):
            errors.append("proposed task_candidate_pair_count is inconsistent with task and candidate targets")
        if targets.get("task_candidate_pair_count", 0) * targets.get("independent_judgments_per_pair", 0) != targets.get("primary_judgment_count"):
            errors.append("proposed primary_judgment_count is inconsistent with pair and judgment targets")
    elif status in {"frozen", "annotated", "evaluated"}:
        if targets.get("task_count") != len(tasks):
            errors.append("frozen target task_count does not match task records")
        if targets.get("task_candidate_pair_count") != len(pairs):
            errors.append("frozen target task_candidate_pair_count does not match pair records")
        expected_pairs = sum(len(task.get("candidate_ids", [])) for task in tasks)
        if expected_pairs != len(pairs):
            errors.append(f"task candidate memberships total {expected_pairs}, but there are {len(pairs)} pair records")
        if targets.get("task_count") != sum(targets.get("tasks_per_modality", {}).values()):
            errors.append("frozen tasks_per_modality does not sum to task_count")
        if targets.get("task_count") != sum(targets.get("tasks_per_type", {}).values()):
            errors.append("frozen tasks_per_type does not sum to task_count")
        if targets.get("task_count") != sum(targets.get("split_task_counts", {}).values()):
            errors.append("frozen split_task_counts does not sum to task_count")
        actual_modality: dict[str, int] = {}
        actual_type: dict[str, int] = {}
        actual_split: dict[str, int] = {}
        for task in tasks:
            actual_modality[task.get("primary_modality")] = actual_modality.get(task.get("primary_modality"), 0) + 1
            actual_type[task.get("task_type")] = actual_type.get(task.get("task_type"), 0) + 1
            actual_split[task.get("split")] = actual_split.get(task.get("split"), 0) + 1
        for label, expected, actual in (
            ("tasks_per_modality", targets.get("tasks_per_modality", {}), actual_modality),
            ("tasks_per_type", targets.get("tasks_per_type", {}), actual_type),
            ("split_task_counts", targets.get("split_task_counts", {}), actual_split),
        ):
            if expected != actual:
                errors.append(f"{label} does not match task records: expected {expected}, got {actual}")
        if status == "frozen":
            for task in tasks:
                task_id = task.get("task_id")
                count = len(task.get("candidate_ids", []))
                if count > targets.get("candidates_per_task", 0):
                    errors.append(f"task {task_id} exceeds candidates_per_task target")
                elif count < targets.get("candidates_per_task", 0):
                    documented_shortfall = any(
                        row.get("record_type") == "task"
                        and row.get("record_id") == task_id
                        and row.get("reason_code") == "candidate_pool_shortfall"
                        for row in manifest.get("exclusions", [])
                    )
                    if not documented_shortfall:
                        errors.append(f"task {task_id} is below candidates_per_task target without a candidate_pool_shortfall exclusion")
        if status in {"annotated", "evaluated"}:
            expected_per_pair = targets.get("independent_judgments_per_pair", 0)
            for pair_id in pair_by_id:
                primary_count = sum(
                    row.get("judgment_role") == "primary"
                    for row in annotations_by_pair.get(pair_id, [])
                )
                if primary_count < expected_per_pair:
                    errors.append(f"pair {pair_id} has {primary_count} primary judgments; expected at least {expected_per_pair}")
            expected_primary = targets.get("task_candidate_pair_count", 0) * expected_per_pair
            actual_primary = sum(row.get("judgment_role") == "primary" for row in annotations)
            if actual_primary < expected_primary:
                errors.append(f"primary annotation count {actual_primary} is below target {expected_primary}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to a Phase II benchmark manifest JSON file")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read manifest: {exc}", file=sys.stderr)
        return 2
    if not isinstance(manifest, dict):
        print("ERROR: manifest root must be a JSON object", file=sys.stderr)
        return 2
    errors = validate(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Cross-record checks passed: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
