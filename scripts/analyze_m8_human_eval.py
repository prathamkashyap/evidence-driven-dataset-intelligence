#!/usr/bin/env python3
"""Milestone 8 Human Evaluation: Descriptive Analysis and Reporting.

Protocol & Design Invariants:
- Independent sampling unit = human participant (N = 3).
- Primary analysis: First exposure only (RATER_1 schedule, 42 card rows, 126 Likert observations).
- Analysis type: DESCRIPTIVE ONLY.
- No inferential tests, no Wilcoxon tests, no p-values, no significance claims.
- Presentation-order limitation: Formats were not counterbalanced across participants in the
  realized sample (Format B shown first in comps 1, 2, 3, 5, 6; Format A shown first in comps 4, 7).
- Supplementary analysis: 6 repeat submissions (84 card rows, 252 Likert observations) analyzed
  only for rating stability/change, explicitly noting R3 linkage uncertainty.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIMARY_CSV_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_primary.csv"
REPEAT_CSV_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_repeat_exposure.csv"
ANALYSIS_MANIFEST_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_analysis_manifest.json"

RESULTS_JSON_PATH = REPO_ROOT / "experiments" / "m8" / "results" / "m8_human_eval_summary.json"
PLOTS_DIR = REPO_ROOT / "experiments" / "m8" / "plots"

DIMENSIONS = ["trust", "understanding", "actionability"]
COMPARISONS = [f"comp_{i}" for i in range(1, 8)]

# Realized presentation order on RATER_1 schedule
RATER1_ORDER = {
    "comp_1": "B_first",
    "comp_2": "B_first",
    "comp_3": "B_first",
    "comp_4": "A_first",
    "comp_5": "B_first",
    "comp_6": "B_first",
    "comp_7": "A_first",
}


def load_primary_data() -> list[dict[str, Any]]:
    with open(PRIMARY_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if len(rows) != 42:
        raise ValueError(f"Expected 42 primary rows, found {len(rows)}")
    return rows


def load_repeat_data() -> list[dict[str, Any]]:
    with open(REPEAT_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if len(rows) != 84:
        raise ValueError(f"Expected 84 repeat rows, found {len(rows)}")
    return rows


def compute_descriptive_stats(values: list[int | float]) -> dict[str, Any]:
    n = len(values)
    mean_val = statistics.mean(values)
    median_val = statistics.median(values)
    min_val = min(values)
    max_val = max(values)
    stdev_val = statistics.stdev(values) if n > 1 else 0.0
    return {
        "count": n,
        "mean": round(mean_val, 4),
        "median": median_val,
        "min": min_val,
        "max": max_val,
        "stdev_descriptive": round(stdev_val, 4),
    }


def analyze_primary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Group by (comparison_id, participant_id)
    comp_part: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for r in rows:
        cid = r["comparison_id"]
        pid = r["participant_id"]
        fmt = r["format_presented"]
        key = (cid, pid)
        if key not in comp_part:
            comp_part[key] = {}
        comp_part[key][fmt] = {
            "trust": int(r["trust_score"]),
            "understanding": int(r["understanding_score"]),
            "actionability": int(r["actionability_score"]),
            "presentation_order": r["presentation_order"],
            "notes": r["notes"],
        }

    # 1. Card-Level Descriptive Aggregation (21 cards per format across 3 participants)
    card_level_summary: dict[str, Any] = {"format_a": {}, "format_b": {}}
    for dim in DIMENSIONS:
        fa_vals = [int(r[f"{dim}_score"]) for r in rows if r["format_presented"] == "format_a_plain"]
        fb_vals = [int(r[f"{dim}_score"]) for r in rows if r["format_presented"] == "format_b_evidence"]
        card_level_summary["format_a"][dim] = compute_descriptive_stats(fa_vals)
        card_level_summary["format_b"][dim] = compute_descriptive_stats(fb_vals)

    # 2. Paired Differences (B - A) across all 21 pairs
    paired_differences: dict[str, Any] = {}
    all_diffs: dict[str, list[int]] = {dim: [] for dim in DIMENSIONS}
    for (cid, pid), pair in comp_part.items():
        for dim in DIMENSIONS:
            diff = pair["format_b_evidence"][dim] - pair["format_a_plain"][dim]
            all_diffs[dim].append(diff)

    for dim in DIMENSIONS:
        paired_differences[dim] = compute_descriptive_stats(all_diffs[dim])

    # 3. Per-Comparison Detailed Breakdown
    per_comparison_breakdown: list[dict[str, Any]] = []
    for cid in COMPARISONS:
        comp_rows = [r for r in rows if r["comparison_id"] == cid]
        tname = comp_rows[0]["task_name"]
        dsname = comp_rows[0]["dataset_id"]

        fa_dim_vals: dict[str, list[int]] = {dim: [] for dim in DIMENSIONS}
        fb_dim_vals: dict[str, list[int]] = {dim: [] for dim in DIMENSIONS}
        diff_dim_vals: dict[str, list[int]] = {dim: [] for dim in DIMENSIONS}

        for pid in ["participant_1", "participant_2", "participant_3"]:
            p_data = comp_part[(cid, pid)]
            for dim in DIMENSIONS:
                fa_v = p_data["format_a_plain"][dim]
                fb_v = p_data["format_b_evidence"][dim]
                fa_dim_vals[dim].append(fa_v)
                fb_dim_vals[dim].append(fb_v)
                diff_dim_vals[dim].append(fb_v - fa_v)

        per_comparison_breakdown.append({
            "comparison_id": cid,
            "task_name": tname,
            "dataset_id": dsname,
            "realized_order": RATER1_ORDER[cid],
            "format_shown_first": "Format B" if RATER1_ORDER[cid] == "B_first" else "Format A",
            "format_a": {dim: compute_descriptive_stats(fa_dim_vals[dim]) for dim in DIMENSIONS},
            "format_b": {dim: compute_descriptive_stats(fb_dim_vals[dim]) for dim in DIMENSIONS},
            "difference_b_minus_a": {dim: compute_descriptive_stats(diff_dim_vals[dim]) for dim in DIMENSIONS},
        })

    # 4. Participant-Level Aggregation (N = 3 independent participants)
    participant_level_summaries: dict[str, Any] = {}
    for pid in ["participant_1", "participant_2", "participant_3"]:
        p_diffs: dict[str, list[int]] = {dim: [] for dim in DIMENSIONS}
        p_fa: dict[str, list[int]] = {dim: [] for dim in DIMENSIONS}
        p_fb: dict[str, list[int]] = {dim: [] for dim in DIMENSIONS}

        for cid in COMPARISONS:
            pair = comp_part[(cid, pid)]
            for dim in DIMENSIONS:
                fa_v = pair["format_a_plain"][dim]
                fb_v = pair["format_b_evidence"][dim]
                p_fa[dim].append(fa_v)
                p_fb[dim].append(fb_v)
                p_diffs[dim].append(fb_v - fa_v)

        participant_level_summaries[pid] = {
            "format_a": {dim: compute_descriptive_stats(p_fa[dim]) for dim in DIMENSIONS},
            "format_b": {dim: compute_descriptive_stats(p_fb[dim]) for dim in DIMENSIONS},
            "difference_b_minus_a": {dim: compute_descriptive_stats(p_diffs[dim]) for dim in DIMENSIONS},
            "raw_paired_differences": p_diffs,
        }

    return {
        "card_level_summary": card_level_summary,
        "paired_differences": paired_differences,
        "per_comparison_breakdown": per_comparison_breakdown,
        "participant_level_summaries": participant_level_summaries,
    }


def analyze_repeat_exposure(
    primary_rows: list[dict[str, Any]],
    repeat_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Descriptive analysis of repeated exposures (exposures 1, 2, 3)."""
    all_rows = primary_rows + repeat_rows

    # Group by (participant_id, comparison_id, format_presented, exposure_number)
    obs: dict[tuple[str, str, str, int], dict[str, int]] = {}
    for r in all_rows:
        pid = r["participant_id"]
        cid = r["comparison_id"]
        fmt = r["format_presented"]
        exp = int(r.get("exposure_number", 1))
        obs[(pid, cid, fmt, exp)] = {
            dim: int(r[f"{dim}_score"]) for dim in DIMENSIONS
        }

    stability_by_participant: dict[str, Any] = {}

    for pid in ["participant_1", "participant_2", "participant_3"]:
        e1_to_e2_unchanged = 0
        e1_to_e2_total = 0
        all_3_unchanged = 0
        all_3_total = 0

        for cid in COMPARISONS:
            for fmt in ["format_a_plain", "format_b_evidence"]:
                e1 = obs[(pid, cid, fmt, 1)]
                e2 = obs[(pid, cid, fmt, 2)]
                e3 = obs[(pid, cid, fmt, 3)]

                for dim in DIMENSIONS:
                    e1_to_e2_total += 1
                    all_3_total += 1
                    if e1[dim] == e2[dim]:
                        e1_to_e2_unchanged += 1
                    if e1[dim] == e2[dim] == e3[dim]:
                        all_3_unchanged += 1

        pct_e1_e2 = round((e1_to_e2_unchanged / e1_to_e2_total) * 100, 2)
        pct_all_3 = round((all_3_unchanged / all_3_total) * 100, 2)

        linkage_note = (
            "Full 3-exposure linkage corroborated with high confidence by exact content agreement across all 7 comparisons and submission timestamps."
            if pid == "participant_2"
            else "E1-E2 linkage moderately corroborated; E3 row assignment relies on timestamp adjacency alone and is not corroborated by rating content. Trajectory must be treated as identity-uncertain."
        )

        stability_by_participant[pid] = {
            "e1_to_e2_identical_count": e1_to_e2_unchanged,
            "e1_to_e2_total_ratings": e1_to_e2_total,
            "e1_to_e2_agreement_percentage": pct_e1_e2,
            "all_3_identical_count": all_3_unchanged,
            "all_3_total_ratings": all_3_total,
            "all_3_agreement_percentage": pct_all_3,
            "provenance_linkage_status": linkage_note,
        }

    return {
        "statement": "Supplementary repeat-exposure stability observations (non-independent; exploratory only).",
        "stability_by_participant": stability_by_participant,
    }


def generate_svg_visualizations(primary_analysis: dict[str, Any], repeat_analysis: dict[str, Any]) -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Primary Paired Differences Plot (SVG)
    diffs = primary_analysis["paired_differences"]
    svg_diffs = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 650 380" width="650" height="380" style="background:#ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <rect width="650" height="380" fill="#ffffff" />
  <text x="325" y="30" font-size="16" font-weight="bold" text-anchor="middle" fill="#1f2937">Milestone 8 Human Evaluation: Paired Score Differences (Format B − Format A)</text>
  <text x="325" y="50" font-size="12" fill="#6b7280" text-anchor="middle">Descriptive primary sample: N = 3 independent participants (42 card evaluations, 21 pairs)</text>
  <text x="325" y="68" font-size="11" fill="#dc2626" text-anchor="middle">Note: Presentation order was not counterbalanced across participants; descriptive pilot evidence only</text>

  <!-- Y Axis Grid -->
  <line x1="80" y1="280" x2="600" y2="280" stroke="#e5e7eb" stroke-width="1" />
  <line x1="80" y1="230" x2="600" y2="230" stroke="#e5e7eb" stroke-width="1" />
  <line x1="80" y1="180" x2="600" y2="180" stroke="#e5e7eb" stroke-width="1" />
  <line x1="80" y1="130" x2="600" y2="130" stroke="#e5e7eb" stroke-width="1" />
  <line x1="80" y1="80" x2="600" y2="80" stroke="#e5e7eb" stroke-width="1" />

  <!-- Y Axis Labels -->
  <text x="70" y="284" font-size="12" text-anchor="end" fill="#6b7280">0</text>
  <text x="70" y="234" font-size="12" text-anchor="end" fill="#6b7280">+1</text>
  <text x="70" y="184" font-size="12" text-anchor="end" fill="#6b7280">+2</text>
  <text x="70" y="134" font-size="12" text-anchor="end" fill="#6b7280">+3</text>
  <text x="70" y="84" font-size="12" text-anchor="end" fill="#6b7280">+4</text>
  <text x="25" y="180" font-size="12" font-weight="bold" text-anchor="middle" transform="rotate(-90 25 180)" fill="#374151">Paired Difference (B − A)</text>

  <!-- Dimension 1: Trust -->
  <g transform="translate(140, 0)">
    <!-- Bar Mean: 1.810 -> height = 1.810 * 50 = 90.5 -> y = 280 - 90.5 = 189.5 -->
    <rect x="-35" y="189.5" width="70" height="90.5" fill="#3b82f6" rx="4" opacity="0.85" />
    <line x1="0" y1="130" x2="0" y2="280" stroke="#1d4ed8" stroke-width="2" />
    <!-- Median line at +2.0 (y=180) -->
    <line x1="-30" y1="180" x2="30" y2="180" stroke="#1e3a8a" stroke-width="3" />
    <text x="0" y="305" font-size="13" font-weight="bold" text-anchor="middle" fill="#1f2937">Trust</text>
    <text x="0" y="322" font-size="11" text-anchor="middle" fill="#4b5563">Mean: +{diffs['trust']['mean']:.2f}</text>
    <text x="0" y="337" font-size="11" text-anchor="middle" fill="#4b5563">Median: +{diffs['trust']['median']:.1f} (range 0..3)</text>
  </g>

  <!-- Dimension 2: Understanding -->
  <g transform="translate(340, 0)">
    <!-- Bar Mean: 3.190 -> height = 3.190 * 50 = 159.5 -> y = 280 - 159.5 = 120.5 -->
    <rect x="-35" y="120.5" width="70" height="159.5" fill="#10b981" rx="4" opacity="0.85" />
    <line x1="0" y1="80" x2="0" y2="180" stroke="#047857" stroke-width="2" />
    <!-- Median line at +3.0 (y=130) -->
    <line x1="-30" y1="130" x2="30" y2="130" stroke="#064e3b" stroke-width="3" />
    <text x="0" y="305" font-size="13" font-weight="bold" text-anchor="middle" fill="#1f2937">Understanding</text>
    <text x="0" y="322" font-size="11" text-anchor="middle" fill="#4b5563">Mean: +{diffs['understanding']['mean']:.2f}</text>
    <text x="0" y="337" font-size="11" text-anchor="middle" fill="#4b5563">Median: +{diffs['understanding']['median']:.1f} (range 2..4)</text>
  </g>

  <!-- Dimension 3: Actionability -->
  <g transform="translate(540, 0)">
    <!-- Bar Mean: 3.000 -> height = 3.000 * 50 = 150 -> y = 280 - 150 = 130 -->
    <rect x="-35" y="130" width="70" height="150" fill="#8b5cf6" rx="4" opacity="0.85" />
    <line x1="0" y1="80" x2="0" y2="180" stroke="#6d28d9" stroke-width="2" />
    <!-- Median line at +3.0 (y=130) -->
    <line x1="-30" y1="130" x2="30" y2="130" stroke="#4c1d95" stroke-width="3" />
    <text x="0" y="305" font-size="13" font-weight="bold" text-anchor="middle" fill="#1f2937">Actionability</text>
    <text x="0" y="322" font-size="11" text-anchor="middle" fill="#4b5563">Mean: +{diffs['actionability']['mean']:.2f}</text>
    <text x="0" y="337" font-size="11" text-anchor="middle" fill="#4b5563">Median: +{diffs['actionability']['median']:.1f} (range 2..4)</text>
  </g>
</svg>
"""
    (PLOTS_DIR / "primary_paired_ratings_n3.svg").write_text(svg_diffs, encoding="utf-8")

    # 2. Per-Comparison Differences Plot (SVG)
    breakdown = primary_analysis["per_comparison_breakdown"]
    comp_svg_lines = []
    for i, c in enumerate(breakdown):
        x = 90 + i * 72
        # Differences
        dt = c["difference_b_minus_a"]["trust"]["mean"]
        du = c["difference_b_minus_a"]["understanding"]["mean"]
        da = c["difference_b_minus_a"]["actionability"]["mean"]

        # Y mapping: 0 -> 240, +4 -> 80 (40 px per point)
        yt = 240 - dt * 40
        yu = 240 - du * 40
        ya = 240 - da * 40

        order_label = "B 1st" if c["realized_order"] == "B_first" else "A 1st"
        order_color = "#1e40af" if c["realized_order"] == "B_first" else "#b91c1c"

        comp_svg_lines.append(f"""
    <g transform="translate({x}, 0)">
      <!-- Order tag -->
      <rect x="-24" y="270" width="48" height="18" fill="{order_color}" rx="3" opacity="0.15" />
      <text x="0" y="283" font-size="10" font-weight="bold" fill="{order_color}" text-anchor="middle">{order_label}</text>
      <text x="0" y="305" font-size="11" font-weight="bold" fill="#1f2937" text-anchor="middle">C{i+1}</text>
      <!-- Bars or dots -->
      <circle cx="-12" cy="{yt:.1f}" r="5" fill="#3b82f6" />
      <circle cx="0" cy="{yu:.1f}" r="5" fill="#10b981" />
      <circle cx="12" cy="{ya:.1f}" r="5" fill="#8b5cf6" />
    </g>""")

    all_comp_svg = "\n".join(comp_svg_lines)

    svg_comps = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 650 360" width="650" height="360" style="background:#ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <rect width="650" height="360" fill="#ffffff" />
  <text x="325" y="28" font-size="15" font-weight="bold" text-anchor="middle" fill="#1f2937">Per-Comparison Mean Paired Difference (B − A) Across N = 3 Participants</text>
  <text x="325" y="46" font-size="11" fill="#6b7280" text-anchor="middle">Showing mean differences by comparison with realized presentation order (RATER_1 schedule)</text>

  <!-- Legend -->
  <g transform="translate(180, 65)">
    <circle cx="0" cy="0" r="5" fill="#3b82f6" />
    <text x="10" y="4" font-size="11" fill="#374151">Trust</text>
    <circle cx="80" cy="0" r="5" fill="#10b981" />
    <text x="90" y="4" font-size="11" fill="#374151">Understanding</text>
    <circle cx="190" cy="0" r="5" fill="#8b5cf6" />
    <text x="200" y="4" font-size="11" fill="#374151">Actionability</text>
  </g>

  <!-- Grid lines -->
  <line x1="60" y1="240" x2="600" y2="240" stroke="#9ca3af" stroke-width="1.5" />
  <line x1="60" y1="200" x2="600" y2="200" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4,4" />
  <line x1="60" y1="160" x2="600" y2="160" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4,4" />
  <line x1="60" y1="120" x2="600" y2="120" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4,4" />
  <line x1="60" y1="80" x2="600" y2="80" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4,4" />

  <!-- Y Labels -->
  <text x="50" y="244" font-size="11" text-anchor="end" fill="#6b7280">0</text>
  <text x="50" y="204" font-size="11" text-anchor="end" fill="#6b7280">+1</text>
  <text x="50" y="164" font-size="11" text-anchor="end" fill="#6b7280">+2</text>
  <text x="50" y="124" font-size="11" text-anchor="end" fill="#6b7280">+3</text>
  <text x="50" y="84" font-size="11" text-anchor="end" fill="#6b7280">+4</text>
  <text x="20" y="160" font-size="11" font-weight="bold" text-anchor="middle" transform="rotate(-90 20 160)" fill="#374151">Mean Difference (B − A)</text>

  {all_comp_svg}

  <text x="325" y="340" font-size="11" fill="#dc2626" text-anchor="middle">Comparisons 1, 2, 3, 5, 6 had Format B shown first; Comparisons 4, 7 had Format A shown first.</text>
</svg>
"""
    (PLOTS_DIR / "per_comparison_differences_n3.svg").write_text(svg_comps, encoding="utf-8")

    # 3. Participant 2 Trajectory (where linkage is 100% verified)
    svg_p2 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 650 320" width="650" height="320" style="background:#ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <rect width="650" height="320" fill="#ffffff" />
  <text x="325" y="28" font-size="15" font-weight="bold" text-anchor="middle" fill="#1f2937">Exploratory Repeated Exposure: Participant 2 Trajectory Across Exposures 1 → 2 → 3</text>
  <text x="325" y="46" font-size="11" fill="#6b7280" text-anchor="middle">Fully corroborated linkage: 42/42 (100.0%) identical ratings across all three exposures</text>

  <rect x="70" y="70" width="510" height="200" fill="#f9fafb" stroke="#e5e7eb" rx="6" />
  <text x="90" y="105" font-size="13" font-weight="bold" fill="#111827">Verified Observation for Participant 2:</text>
  <text x="90" y="130" font-size="12" fill="#374151">• Form 1 (Exposure 1, 6:45:43 pm): 14 card ratings completed with brief text comments.</text>
  <text x="90" y="155" font-size="12" fill="#374151">• Form 2 (Exposure 2, 6:52:23 pm): Identical ratings (42/42 cells matching); comments left blank.</text>
  <text x="90" y="180" font-size="12" fill="#374151">• Form 3 (Exposure 3, 6:58:24 pm): Identical ratings (42/42 cells matching); comments left blank.</text>
  <text x="90" y="215" font-size="12" font-weight="bold" fill="#b91c1c">Methodological Interpretation:</text>
  <text x="90" y="235" font-size="12" fill="#4b5563">Demonstrates near-instantaneous rating invariance / carry-over across short intervals (~13 min total).</text>
  <text x="90" y="255" font-size="12" fill="#4b5563">Exposures 2 and 3 add zero independent evidence. (Note: R3 linkage is uncertain for other participants).</text>
</svg>
"""
    (PLOTS_DIR / "participant2_repeat_trajectory.svg").write_text(svg_p2, encoding="utf-8")
    print(f"Generated 3 descriptive SVG plots in {PLOTS_DIR}")


def main() -> None:
    primary_rows = load_primary_data()
    repeat_rows = load_repeat_data()

    primary_analysis = analyze_primary(primary_rows)
    repeat_analysis = analyze_repeat_exposure(primary_rows, repeat_rows)

    full_summary = {
        "analysis_version": "1.0.0",
        "study_identifier": "m8-human-eval-v1",
        "sample_size_statement": "N = 3 independent human participants (42 primary card evaluations, 126 Likert observations).",
        "primary_analysis": primary_analysis,
        "supplementary_repeat_exposure": repeat_analysis,
    }

    RESULTS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON_PATH.write_text(json.dumps(full_summary, indent=2), encoding="utf-8")
    print(f"Wrote descriptive summary JSON: {RESULTS_JSON_PATH}")

    # Also generate SVG plots
    generate_svg_visualizations(primary_analysis, repeat_analysis)

    # Print summary table to console
    print("\n" + "=" * 65)
    print("M8 HUMAN EVALUATION: PRIMARY DESCRIPTIVE SUMMARY (N = 3 PARTICIPANTS)")
    print("=" * 65)
    print(f"{'Dimension':<16} | {'Format A (Mean / Med)':<22} | {'Format B (Mean / Med)':<22} | {'Diff B - A (Mean / Med)'}")
    print("-" * 65)
    for dim in DIMENSIONS:
        fa = primary_analysis["card_level_summary"]["format_a"][dim]
        fb = primary_analysis["card_level_summary"]["format_b"][dim]
        diff = primary_analysis["paired_differences"][dim]
        print(f"{dim.capitalize():<16} | {fa['mean']:.2f} / {fa['median']:<17} | {fb['mean']:.2f} / {fb['median']:<17} | +{diff['mean']:.2f} / +{diff['median']}")
    print("=" * 65)
    print("Note: Primary sample used RATER_1 schedule exclusively; order was not counterbalanced across participants.")
    print("=" * 65)


if __name__ == "__main__":
    main()
