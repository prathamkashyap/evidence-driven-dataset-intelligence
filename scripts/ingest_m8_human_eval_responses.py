#!/usr/bin/env python3
"""Milestone 8 Human Evaluation: Post-Collection Data Ingestion & Provenance Generation.

Strict Operational Boundary:
- Ingests all 9 real Google Forms submissions from raw exports without modification.
- Enforces confirmed participant groupings:
    Person A (participant_1): R1 sub 1, R2 sub 1, R3 sub 1
    Person B (participant_2): R1 sub 3, R2 sub 2, R3 sub 2
    Person C (participant_3): R1 sub 2, R2 sub 3, R3 sub 3
- Enforces exposure sequence: R1 (exposure 1) -> R2 (exposure 2) -> R3 (exposure 3)
- Decodes Card 1 / Card 2 formats strictly from frozen per-form presentation schedule (seed 20260914)
- Preserves all responses verbatim: no score recalculation, no imputation, no outcome filtering
- Produces:
    1. data/benchmarks/m8_human_eval_raw_collection_manifest.json (Post-collection provenance manifest)
    2. data/benchmarks/m8_human_eval_responses_long.csv (Traceable long-format analysis dataset)
- Does NOT overwrite data/benchmarks/m8_human_eval_responses.csv.
- Does NOT perform inferential statistical tests or claim n=9.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_session_manifest.json"
RAW_DIR = REPO_ROOT / "data" / "raw" / "m8_initial_collection"

OUTPUT_PROVENANCE_MANIFEST_PATH = (
    REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_raw_collection_manifest.json"
)
OUTPUT_LONG_CSV_PATH = (
    REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_responses_long.csv"
)

RAW_FILES = {
    "RATER_1": RAW_DIR / "rater1_form.csv",
    "RATER_2": RAW_DIR / "rater2_form.csv",
    "RATER_3": RAW_DIR / "rater3_form.csv",
}

# Confirmed grouping from independent signals (chronology, response-content agreement)
# Each entry: (participant_id, person_alias, form_slot, raw_row_index_1_based, exposure_number)
SUBMISSION_REGISTRY = [
    # Person A
    ("participant_1", "Person A", "RATER_1", 1, 1),
    ("participant_1", "Person A", "RATER_2", 1, 2),
    ("participant_1", "Person A", "RATER_3", 1, 3),
    # Person B
    ("participant_2", "Person B", "RATER_1", 3, 1),
    ("participant_2", "Person B", "RATER_2", 2, 2),
    ("participant_2", "Person B", "RATER_3", 2, 3),
    # Person C
    ("participant_3", "Person C", "RATER_1", 2, 1),
    ("participant_3", "Person C", "RATER_2", 3, 2),
    ("participant_3", "Person C", "RATER_3", 3, 3),
]


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    h.update(filepath.read_bytes())
    return h.hexdigest()


def load_raw_submissions() -> dict[str, list[list[str]]]:
    raw_data: dict[str, list[list[str]]] = {}
    for slot, p in RAW_FILES.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing raw export: {p}")
        with open(p, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            if len(header) != 57:
                raise ValueError(f"Expected 57 columns in {p.name}, got {len(header)}")
            rows = list(reader)
            if len(rows) != 3:
                raise ValueError(f"Expected 3 submissions in {p.name}, got {len(rows)}")
            raw_data[slot] = rows
    return raw_data


def decode_presentation_order(
    form_slot: str,
    comp_spec: dict[str, Any],
) -> tuple[str, str]:
    """Return (card_1_format, card_2_format) based strictly on frozen manifest."""
    rater_slot_key = form_slot.lower()  # "rater_1", "rater_2", "rater_3"
    order = comp_spec["presentation_order"][rater_slot_key]
    if order == "B_first":
        return "format_b_evidence", "format_a_plain"
    elif order == "A_first":
        return "format_a_plain", "format_b_evidence"
    else:
        raise ValueError(f"Unknown presentation order '{order}' for {rater_slot_key} in {comp_spec['comparison_id']}")


def process_submissions() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    comparisons = manifest["comparisons"]
    raw_data = load_raw_submissions()

    raw_file_metadata = {}
    for slot, path in RAW_FILES.items():
        raw_file_metadata[slot] = {
            "relative_path": str(path.relative_to(REPO_ROOT)),
            "filename": path.name,
            "byte_size": path.stat().st_size,
            "sha256": compute_sha256(path),
            "submission_count": len(raw_data[slot]),
        }

    provenance_submissions = []
    long_rows = []

    for p_id, alias, slot, raw_row_idx, exp_num in SUBMISSION_REGISTRY:
        row_data = raw_data[slot][raw_row_idx - 1]
        timestamp = row_data[0]
        sub_id = f"sub_{p_id}_{slot.lower()}_exp{exp_num}"
        is_repeat = exp_num > 1

        sub_meta = {
            "submission_id": sub_id,
            "participant_id": p_id,
            "person_alias": alias,
            "form_slot": slot,
            "raw_source_file": str(RAW_FILES[slot].relative_to(REPO_ROOT)),
            "raw_row_index": raw_row_idx,
            "submission_timestamp": timestamp,
            "exposure_number": exp_num,
            "accidental_repeat_exposure": is_repeat,
            "candidate_first_exposure_subset": (exp_num == 1),
        }
        provenance_submissions.append(sub_meta)

        # Extract all 7 comparisons (8 columns per comparison)
        for c_idx, comp_spec in enumerate(comparisons):
            cid = comp_spec["comparison_id"]
            tname = comp_spec["task_name"]
            dsid = comp_spec["dataset_id"]
            offset = 1 + c_idx * 8

            c1_format, c2_format = decode_presentation_order(slot, comp_spec)

            # Card 1 (first presented)
            c1_trust = int(row_data[offset])
            c1_under = int(row_data[offset + 1])
            c1_act = int(row_data[offset + 2])
            c1_notes = row_data[offset + 3]

            # Card 2 (second presented)
            c2_trust = int(row_data[offset + 4])
            c2_under = int(row_data[offset + 5])
            c2_act = int(row_data[offset + 6])
            c2_notes = row_data[offset + 7]

            for score in [c1_trust, c1_under, c1_act, c2_trust, c2_under, c2_act]:
                if score < 1 or score > 5:
                    raise ValueError(f"Score {score} out of bounds in {sub_id} {cid}")

            long_rows.append({
                "participant_id": p_id,
                "submission_id": sub_id,
                "form_slot": slot,
                "exposure_number": exp_num,
                "task_name": tname,
                "comparison_id": cid,
                "dataset_id": dsid,
                "format_presented": c1_format,
                "presentation_order": "first",
                "trust_score": c1_trust,
                "understanding_score": c1_under,
                "actionability_score": c1_act,
                "notes": c1_notes,
            })

            long_rows.append({
                "participant_id": p_id,
                "submission_id": sub_id,
                "form_slot": slot,
                "exposure_number": exp_num,
                "task_name": tname,
                "comparison_id": cid,
                "dataset_id": dsid,
                "format_presented": c2_format,
                "presentation_order": "second",
                "trust_score": c2_trust,
                "understanding_score": c2_under,
                "actionability_score": c2_act,
                "notes": c2_notes,
            })

    provenance_manifest = {
        "schema_version": 1,
        "manifest_id": "m8-human-eval-raw-collection-manifest-v1",
        "study_id": "m8-human-eval-v1",
        "collection_event_status": "completed",
        "collection_summary": {
            "total_raw_submissions": len(provenance_submissions),
            "distinct_human_participants": 3,
            "submissions_per_participant": 3,
            "total_evaluations_per_submission": 14,
            "total_card_observation_rows": len(long_rows),
        },
        "experimental_exposure_structure": {
            "design_intent": "Single-exposure evaluation across independent raters",
            "actual_collection_event": (
                "Accidental repeated exposure: all 3 human participants completed all three "
                "rater-specific forms (RATER_1, RATER_2, RATER_3) sequentially."
            ),
            "exposure_order_chronology": "RATER_1 form (exposure 1) -> RATER_2 form (exposure 2) -> RATER_3 form (exposure 3)",
            "methodological_boundary": (
                "The 9 submissions represent real empirical observations, but MUST NOT be treated "
                "as N=9 independent raters. Repeated submissions are marked as accidental_repeat_exposure=true."
            ),
            "outcome_based_selection": False,
        },
        "participant_grouping": {
            "participant_1": {
                "person_alias": "Person A",
                "submissions": [
                    {"form_slot": "RATER_1", "raw_row_index": 1, "exposure_number": 1, "timestamp": "2026/09/16 6:11:17 pm GMT+5:30"},
                    {"form_slot": "RATER_2", "raw_row_index": 1, "exposure_number": 2, "timestamp": "2026/09/16 6:20:28 pm GMT+5:30"},
                    {"form_slot": "RATER_3", "raw_row_index": 1, "exposure_number": 3, "timestamp": "2026/09/16 6:28:17 pm GMT+5:30"},
                ],
            },
            "participant_2": {
                "person_alias": "Person B",
                "submissions": [
                    {"form_slot": "RATER_1", "raw_row_index": 3, "exposure_number": 1, "timestamp": "2026/09/16 6:45:43 pm GMT+5:30"},
                    {"form_slot": "RATER_2", "raw_row_index": 2, "exposure_number": 2, "timestamp": "2026/09/16 6:52:23 pm GMT+5:30"},
                    {"form_slot": "RATER_3", "raw_row_index": 2, "exposure_number": 3, "timestamp": "2026/09/16 6:58:24 pm GMT+5:30"},
                ],
            },
            "participant_3": {
                "person_alias": "Person C",
                "submissions": [
                    {"form_slot": "RATER_1", "raw_row_index": 2, "exposure_number": 1, "timestamp": "2026/09/16 6:45:25 pm GMT+5:30"},
                    {"form_slot": "RATER_2", "raw_row_index": 3, "exposure_number": 2, "timestamp": "2026/09/16 6:53:15 pm GMT+5:30"},
                    {"form_slot": "RATER_3", "raw_row_index": 3, "exposure_number": 3, "timestamp": "2026/09/16 7:01:16 pm GMT+5:30"},
                ],
            },
        },
        "raw_exports": raw_file_metadata,
        "submissions": provenance_submissions,
        "subsets": {
            "first_exposure_subset": {
                "description": "Candidate protocol-aligned subset comprising strictly the first exposure for each distinct participant",
                "criteria": "exposure_number == 1 (all completed under RATER_1 schedule)",
                "submission_ids": [
                    "sub_participant_1_rater_1_exp1",
                    "sub_participant_2_rater_1_exp1",
                    "sub_participant_3_rater_1_exp1",
                ],
                "distinct_participants": 3,
                "card_observation_count": 42,
            },
            "repeated_exposure_subset": {
                "description": "Submissions completed as repeat exposures (accidental repeat completions)",
                "criteria": "exposure_number > 1 (completed under RATER_2 and RATER_3 schedules)",
                "submission_ids": [
                    "sub_participant_1_rater_2_exp2",
                    "sub_participant_1_rater_3_exp3",
                    "sub_participant_2_rater_2_exp2",
                    "sub_participant_2_rater_3_exp3",
                    "sub_participant_3_rater_2_exp2",
                    "sub_participant_3_rater_3_exp3",
                ],
                "distinct_participants": 3,
                "card_observation_count": 84,
            },
        },
    }

    return provenance_manifest, long_rows


def write_outputs(provenance_manifest: dict[str, Any], long_rows: list[dict[str, Any]]) -> None:
    # 1. Write provenance manifest JSON
    OUTPUT_PROVENANCE_MANIFEST_PATH.write_text(
        json.dumps(provenance_manifest, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote post-collection provenance manifest: {OUTPUT_PROVENANCE_MANIFEST_PATH}")

    # 2. Write long-format CSV
    fieldnames = [
        "participant_id",
        "submission_id",
        "form_slot",
        "exposure_number",
        "task_name",
        "comparison_id",
        "dataset_id",
        "format_presented",
        "presentation_order",
        "trust_score",
        "understanding_score",
        "actionability_score",
        "notes",
    ]

    with open(OUTPUT_LONG_CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(long_rows)
    print(f"Wrote derived long-format dataset: {OUTPUT_LONG_CSV_PATH} ({len(long_rows)} rows)")


def main() -> None:
    manifest, long_rows = process_submissions()
    write_outputs(manifest, long_rows)


if __name__ == "__main__":
    main()
