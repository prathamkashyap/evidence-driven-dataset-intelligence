#!/usr/bin/env python3
"""Materialize Milestone 8 Human Evaluation Primary and Supplementary Datasets and Manifest.

Strict Boundaries:
- Derives data exclusively from data/benchmarks/m8_human_eval_responses_long.csv
- Primary inclusion rule: exposure_number == 1 (42 card rows, N=3 participants)
- Supplementary inclusion rule: exposure_number > 1 (84 card rows, accidental repeat exposures)
- Generates:
    data/benchmarks/m8_human_eval_primary.csv
    data/benchmarks/m8_human_eval_repeat_exposure.csv
    data/benchmarks/m8_human_eval_analysis_manifest.json
- Zero score modification, zero imputation, zero outcome-based filtering.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LONG_CSV_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_responses_long.csv"
RAW_MANIFEST_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_raw_collection_manifest.json"

PRIMARY_CSV_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_primary.csv"
REPEAT_CSV_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_repeat_exposure.csv"
ANALYSIS_MANIFEST_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_analysis_manifest.json"


def materialize_datasets() -> None:
    if not LONG_CSV_PATH.exists():
        raise FileNotFoundError(f"Missing long-format responses: {LONG_CSV_PATH}")

    with open(LONG_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    if len(all_rows) != 126:
        raise ValueError(f"Expected 126 rows in long CSV, got {len(all_rows)}")

    # 1. Primary Dataset (Exposure 1 only)
    primary_fieldnames = [
        "participant_id",
        "submission_id",
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

    primary_rows = []
    for r in all_rows:
        if r["exposure_number"] == "1":
            primary_rows.append({k: r[k] for k in primary_fieldnames})

    if len(primary_rows) != 42:
        raise ValueError(f"Expected 42 primary rows, got {len(primary_rows)}")

    with open(PRIMARY_CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=primary_fieldnames)
        writer.writeheader()
        writer.writerows(primary_rows)
    print(f"Wrote primary dataset: {PRIMARY_CSV_PATH} ({len(primary_rows)} rows)")

    # 2. Supplementary Repeat-Exposure Dataset (Exposure > 1)
    repeat_fieldnames = [
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

    repeat_rows = []
    for r in all_rows:
        if int(r["exposure_number"]) > 1:
            repeat_rows.append({k: r[k] for k in repeat_fieldnames})

    if len(repeat_rows) != 84:
        raise ValueError(f"Expected 84 repeat-exposure rows, got {len(repeat_rows)}")

    with open(REPEAT_CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=repeat_fieldnames)
        writer.writeheader()
        writer.writerows(repeat_rows)
    print(f"Wrote repeat-exposure dataset: {REPEAT_CSV_PATH} ({len(repeat_rows)} rows)")

    # 3. Analysis Manifest
    analysis_manifest = {
        "schema_version": 1,
        "manifest_id": "m8-human-eval-analysis-manifest-v1",
        "study_id": "m8-human-eval-v1",
        "analysis_version": "1.0.0",
        "analysis_timestamp": "2026-09-17T11:20:00+05:30",
        "governing_freeze_commits": {
            "protocol_freeze_commit": "3df1bae455c36e81d266b7c45edfc5465763d281",
            "m8_benchmark_results_commit": "34eeb2b825ba57e518218f2f7fc3fd5f1a813fea",
            "human_study_artifact_freeze_commit": "c5bdc0c1bd458c3d71a5181fa67232c831c3804c",
            "data_capture_freeze_commit": "517e689c73405e9172bd3a6dbdf3fd965095c6b8",
        },
        "raw_collection_manifest_reference": "data/benchmarks/m8_human_eval_raw_collection_manifest.json",
        "sampling_units": {
            "independent_sampling_unit": "human_participant",
            "independent_participant_count": 3,
            "statement_sample_size": "The independent sampling unit is the human participant (N = 3). The 9 submissions reflect 3 sequential completions per participant, NOT N = 9 independent raters.",
        },
        "primary_analysis": {
            "inclusion_rule": "exposure_number == 1",
            "source_dataset": "data/benchmarks/m8_human_eval_primary.csv",
            "participant_count": 3,
            "submission_count": 3,
            "card_evaluation_count": 42,
            "likert_observation_count": 126,
            "form_slot_used": "RATER_1",
            "presentation_order_counterbalancing_status": (
                "Not realized across participants. Because all three primary participants completed the RATER_1 form "
                "schedule, presentation order is confounded with format across the 7 comparisons (Format B shown first for "
                "comps 1, 2, 3, 5, 6; Format A shown first for comps 4, 7)."
            ),
            "methodological_framing": "Descriptive only. No inferential tests, p-values, or causal superiority claims.",
        },
        "supplementary_analysis": {
            "inclusion_rule": "exposure_number > 1",
            "source_dataset": "data/benchmarks/m8_human_eval_repeat_exposure.csv",
            "participant_count": 3,
            "submission_count": 6,
            "card_evaluation_count": 84,
            "likert_observation_count": 252,
            "nature": "Accidental repeated exposures; non-independent observations; exploratory only.",
            "provenance_limitation": (
                "Participant linkage across all three exposures is fully corroborated by content and chronology for participant_2. "
                "For participant_1 and participant_3, the R1-R2 linkage is moderately corroborated, while the assignment of the two "
                "remaining R3 rows relies on timestamp adjacency and is not independently corroborated by rating content. This uncertainty "
                "is explicitly preserved."
            ),
        },
        "methodological_guards": {
            "outcome_based_filtering": False,
            "inferential_tests_conducted": False,
            "p_values_calculated": False,
            "wilcoxon_signed_rank_calculated": False,
            "causal_format_superiority_claimed": False,
            "rationale_for_omitting_wilcoxon": (
                "With only N = 3 independent participants, a Wilcoxon signed-rank test has only 2^3 = 8 sign permutations, "
                "yielding a minimum attainable two-sided exact p-value of 0.25 (p = 2 * (1/8) = 0.25). It cannot reach conventional "
                "significance thresholds under any observed data. Reporting p-values in this regime creates false rigor; descriptive "
                "medians and ranges are methodologically honest."
            ),
        },
    }

    ANALYSIS_MANIFEST_PATH.write_text(
        json.dumps(analysis_manifest, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote analysis manifest: {ANALYSIS_MANIFEST_PATH}")


if __name__ == "__main__":
    materialize_datasets()
