#!/usr/bin/env python3
"""Minimal, validated, append-only response capture utility for Milestone 8 human evaluation.

Strict operational boundary:
- Validates single response records against data/benchmarks/m8_human_eval_session_manifest.json
- Enforces Likert scale bounds (integers 1-5)
- Enforces deterministic presentation randomization schedule per rater and comparison
- Enforces duplicate rejection per (rater_id, comparison_id, format_presented) and position
- Preserves exact frozen CSV header
- Performs zero data inference, generation, modification, or aggregation.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

REQUIRED_CSV_HEADER = (
    "rater_id,task_name,comparison_id,dataset_id,format_presented,"
    "presentation_order,trust_score,understanding_score,actionability_score,notes"
)

ALLOWED_FORMATS = ("format_a_plain", "format_b_evidence")
ALLOWED_POSITIONS = ("first", "second")


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and return session manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Session manifest not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid session manifest format: {manifest_path}")
    return data


def validate_likert_score(value: Any, dimension_name: str) -> int:
    """Validate that score is an integer between 1 and 5 inclusive."""
    if isinstance(value, bool):
        raise ValueError(f"Invalid {dimension_name}: boolean is not a valid Likert score")
    try:
        score = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {dimension_name}: must be an integer, got {value!r}")
    if isinstance(value, str) and not value.strip().lstrip("-+").isdigit():
        raise ValueError(f"Invalid {dimension_name}: must be an exact integer representation, got {value!r}")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"Invalid {dimension_name}: floating point numbers are not allowed, got {value!r}")
    if score < 1 or score > 5:
        raise ValueError(f"Invalid {dimension_name}: score must be in range [1, 5], got {score}")
    return score


def validate_response_record(
    manifest: dict[str, Any],
    rater_id: str,
    task_name: str,
    comparison_id: str,
    dataset_id: str,
    format_presented: str,
    presentation_order: str,
    trust_score: Any,
    understanding_score: Any,
    actionability_score: Any,
    notes: Any = "",
) -> dict[str, Any]:
    """Validate a single response record against the session manifest."""
    # 1. Validate rater_id
    known_raters = [r["rater_id"] for r in manifest.get("rater_cohort", {}).get("raters", [])]
    if rater_id not in known_raters:
        raise ValueError(f"Unknown rater_id '{rater_id}'. Allowed raters: {known_raters}")

    # 2. Validate comparison_id
    comparisons = {c["comparison_id"]: c for c in manifest.get("comparisons", [])}
    if comparison_id not in comparisons:
        raise ValueError(f"Unknown comparison_id '{comparison_id}'. Allowed: {sorted(comparisons.keys())}")
    comp_spec = comparisons[comparison_id]

    # 3. Validate task_name
    expected_task = comp_spec.get("task_name")
    if task_name != expected_task:
        raise ValueError(
            f"Task mismatch for {comparison_id}: expected '{expected_task}', got '{task_name}'"
        )

    # 4. Validate dataset_id
    expected_dataset = comp_spec.get("dataset_id")
    if dataset_id != expected_dataset:
        raise ValueError(
            f"Dataset ID mismatch for {comparison_id}: expected '{expected_dataset}', got '{dataset_id}'"
        )

    # 5. Validate format_presented
    if format_presented not in ALLOWED_FORMATS:
        raise ValueError(
            f"Invalid format_presented '{format_presented}'. Allowed: {ALLOWED_FORMATS}"
        )

    # 6. Validate presentation_order
    if presentation_order not in ALLOWED_POSITIONS:
        raise ValueError(
            f"Invalid presentation_order '{presentation_order}'. Allowed: {ALLOWED_POSITIONS}"
        )

    # 7. Validate alignment with randomized presentation schedule
    scheduled_order = comp_spec.get("presentation_order", {}).get(rater_id)
    if not scheduled_order:
        raise ValueError(
            f"No scheduled presentation order found in manifest for rater '{rater_id}' on '{comparison_id}'"
        )

    expected_position_format_a = "first" if scheduled_order == "A_first" else "second"
    expected_position_format_b = "first" if scheduled_order == "B_first" else "second"

    if format_presented == "format_a_plain" and presentation_order != expected_position_format_a:
        raise ValueError(
            f"Presentation schedule mismatch: for {rater_id} on {comparison_id}, schedule is '{scheduled_order}', "
            f"so format_a_plain must be presented '{expected_position_format_a}', but got '{presentation_order}'"
        )
    if format_presented == "format_b_evidence" and presentation_order != expected_position_format_b:
        raise ValueError(
            f"Presentation schedule mismatch: for {rater_id} on {comparison_id}, schedule is '{scheduled_order}', "
            f"so format_b_evidence must be presented '{expected_position_format_b}', but got '{presentation_order}'"
        )

    # 8. Validate Likert scores
    v_trust = validate_likert_score(trust_score, "trust_score")
    v_understanding = validate_likert_score(understanding_score, "understanding_score")
    v_actionability = validate_likert_score(actionability_score, "actionability_score")

    # 9. Notes sanitization (preserve raw text, cast None to empty string)
    clean_notes = "" if notes is None else str(notes)

    return {
        "rater_id": rater_id,
        "task_name": task_name,
        "comparison_id": comparison_id,
        "dataset_id": dataset_id,
        "format_presented": format_presented,
        "presentation_order": presentation_order,
        "trust_score": v_trust,
        "understanding_score": v_understanding,
        "actionability_score": v_actionability,
        "notes": clean_notes,
    }


def init_response_csv_if_missing(output_path: Path) -> bool:
    """Ensure response CSV exists with exact required header only. Return True if created."""
    if output_path.exists():
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(REQUIRED_CSV_HEADER + "\n", encoding="utf-8")
    return True


def check_existing_responses(output_path: Path) -> list[dict[str, str]]:
    """Read and validate existing response rows; ensure exact header matches."""
    if not output_path.exists():
        return []

    content = output_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"Response file exists but is completely empty (missing header): {output_path}")

    header_line = lines[0]
    if header_line != REQUIRED_CSV_HEADER:
        raise ValueError(
            f"Corrupted or invalid CSV header in {output_path}.\n"
            f"Expected: {REQUIRED_CSV_HEADER}\n"
            f"Found:    {header_line}"
        )

    existing_records: list[dict[str, str]] = []
    with open(output_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=2):
            existing_records.append(row)

    return existing_records


def append_response_record(
    manifest_path: Path,
    output_path: Path,
    rater_id: str,
    task_name: str,
    comparison_id: str,
    dataset_id: str,
    format_presented: str,
    presentation_order: str,
    trust_score: Any,
    understanding_score: Any,
    actionability_score: Any,
    notes: Any = "",
) -> dict[str, Any]:
    """Validate and append a single response record to the CSV file."""
    manifest = load_manifest(manifest_path)
    validated = validate_response_record(
        manifest=manifest,
        rater_id=rater_id,
        task_name=task_name,
        comparison_id=comparison_id,
        dataset_id=dataset_id,
        format_presented=format_presented,
        presentation_order=presentation_order,
        trust_score=trust_score,
        understanding_score=understanding_score,
        actionability_score=actionability_score,
        notes=notes,
    )

    # Check existing file / initialize if missing
    if not output_path.exists():
        init_response_csv_if_missing(output_path)

    existing = check_existing_responses(output_path)
    for row in existing:
        if row.get("rater_id") == validated["rater_id"] and row.get("comparison_id") == validated["comparison_id"]:
            if row.get("format_presented") == validated["format_presented"]:
                raise ValueError(
                    f"Duplicate entry rejected: response already recorded for rater '{validated['rater_id']}', "
                    f"comparison '{validated['comparison_id']}', format '{validated['format_presented']}'"
                )
            if row.get("presentation_order") == validated["presentation_order"]:
                raise ValueError(
                    f"Duplicate position rejected: response already recorded for rater '{validated['rater_id']}', "
                    f"comparison '{validated['comparison_id']}', position '{validated['presentation_order']}'"
                )

    # Append validated row
    field_order = REQUIRED_CSV_HEADER.split(",")
    row_values = [validated[k] for k in field_order]

    with open(output_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(row_values)

    return validated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append a single validated human evaluation response to the response CSV."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/benchmarks/m8_human_eval_session_manifest.json"),
        help="Path to session manifest JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/benchmarks/m8_human_eval_responses.csv"),
        help="Path to response CSV.",
    )
    parser.add_argument(
        "--init-header-only",
        action="store_true",
        help="Initialize the output CSV with the exact header only if it does not exist.",
    )
    parser.add_argument("--rater-id", type=str, help="Participant/rater identifier (e.g. rater_1).")
    parser.add_argument("--task-name", type=str, help="Task name.")
    parser.add_argument("--comparison-id", type=str, help="Comparison ID (e.g. comp_1).")
    parser.add_argument("--dataset-id", type=str, help="Dataset internal ID (e.g. ds_...).")
    parser.add_argument("--format-presented", type=str, help="format_a_plain or format_b_evidence.")
    parser.add_argument("--presentation-order", type=str, help="first or second.")
    parser.add_argument("--trust-score", type=int, help="Trust Likert score (1-5).")
    parser.add_argument("--understanding-score", type=int, help="Understanding Likert score (1-5).")
    parser.add_argument("--actionability-score", type=int, help="Actionability Likert score (1-5).")
    parser.add_argument("--notes", type=str, default="", help="Optional qualitative notes.")

    args = parser.parse_args()

    if args.init_header_only:
        created = init_response_csv_if_missing(args.output)
        if created:
            print(f"Initialized empty response CSV with required header: {args.output}")
        else:
            print(f"Response CSV already exists: {args.output}")
        return 0

    required_args = [
        args.rater_id,
        args.task_name,
        args.comparison_id,
        args.dataset_id,
        args.format_presented,
        args.presentation_order,
        args.trust_score,
        args.understanding_score,
        args.actionability_score,
    ]
    if any(a is None for a in required_args):
        parser.error(
            "All rating fields (--rater-id, --task-name, --comparison-id, --dataset-id, "
            "--format-presented, --presentation-order, --trust-score, --understanding-score, "
            "--actionability-score) are required to append a response."
        )

    try:
        record = append_response_record(
            manifest_path=args.manifest,
            output_path=args.output,
            rater_id=args.rater_id,
            task_name=args.task_name,
            comparison_id=args.comparison_id,
            dataset_id=args.dataset_id,
            format_presented=args.format_presented,
            presentation_order=args.presentation_order,
            trust_score=args.trust_score,
            understanding_score=args.understanding_score,
            actionability_score=args.actionability_score,
            notes=args.notes,
        )
        print(f"Successfully recorded response for {record['rater_id']} - {record['comparison_id']} ({record['format_presented']})")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
