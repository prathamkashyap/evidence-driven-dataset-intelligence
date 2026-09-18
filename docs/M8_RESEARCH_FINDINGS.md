# M8 Research Findings: Human Evaluation of Evidence-Card Format

**Study identifier:** `m8_human_evaluation_2026`
**Protocol:** [`data/benchmarks/m8_human_eval_protocol.md`](../data/benchmarks/m8_human_eval_protocol.md)
**Instrument:** [`data/benchmarks/m8_human_eval_instrument.md`](../data/benchmarks/m8_human_eval_instrument.md)
**Analysis source:** [`experiments/m8/results/m8_human_eval_summary.json`](../experiments/m8/results/m8_human_eval_summary.json)
**Machine-readable results:** [`experiments/m8/human_eval/m8_human_eval_results.json`](../experiments/m8/human_eval/m8_human_eval_results.json)
**Analysis date:** 2026-09-18

---

## 1. Study Purpose

This evaluation assessed whether Format B (the evidence-augmented dataset card produced by the M8 pipeline) is perceived as more trustworthy, understandable, and actionable than Format A (a minimal four-field plain card: name, source, modality, size) when a human evaluator is deciding whether a dataset suits a specific ML task.

---

## 2. Study Design Summary

| Design element | Value |
|---|---|
| **Comparison pairs** | 7 (2 sentiment, 3 tabular/Titanic, 2 image/CIFAR-10) |
| **Rating dimensions** | Trust, Understanding, Actionability (5-point Likert each) |
| **Independent sampling unit** | Human participant |
| **Primary N** | 3 participants, first-exposure ratings only |
| **Primary observations** | 42 card-level ratings; 126 individual Likert scores |
| **Inferential statistics** | None performed (see §6) |

### 2.1 Presentation schedule

All three primary participants completed the **RATER_1** form schedule. Cross-participant order counterbalancing **was not realized**: the study pre-registered three distinct schedules (RATER_1, RATER_2, RATER_3), but all participants submitted the RATER_1 schedule first. The realized presentation order is:

| Comparison | Format shown first |
|---|---|
| comp_1, comp_2, comp_3, comp_5, comp_6 | Format B |
| comp_4, comp_7 | Format A |

Results should be interpreted with this order confound in mind. The confound is symmetry-breaking but not design-defeating: the direction of differences is consistent across both A-first and B-first comparisons (see §4).

---

## 3. Format Descriptions

**Format A (minimal):** Four fields — dataset name, source, modality, size. Represents the baseline information widely available in public dataset catalogues.

**Format B (evidence-augmented):** Full evidence card produced by the M8 pipeline. Includes task-suitability fit/non-fit rationale, component evidence scores (completeness, consistency, provenance, benchmark), license claim, access notes, and an explicit recommendation context.

---

## 4. Primary Descriptive Results

### 4.1 Card-level format means (21 observations per format: 3 participants × 7 comparisons)

| Dimension | Format A mean | Format A median | Format B mean | Format B median |
|---|---|---|---|---|
| **Trust** | 1.95 | 2 | 3.76 | 4 |
| **Understanding** | 1.62 | 2 | 4.81 | 5 |
| **Actionability** | 1.33 | 1 | 4.33 | 4 |

### 4.2 Paired difference B − A

| Dimension | Mean diff | Median diff | Min | Max |
|---|---|---|---|---|
| **Trust** | +1.81 | +2 | 0 | +3 |
| **Understanding** | +3.19 | +3 | +2 | +4 |
| **Actionability** | +3.00 | +3 | +2 | +4 |

All paired differences are ≥ 0, with one exception: **comp_7, participant_2, Trust** — both formats rated 2 (tied). Every other comparison–participant–dimension triple produced a positive B − A difference.

### 4.3 Participant-level means of B − A (across 7 comparisons each)

| Participant | Trust B−A | Understanding B−A | Actionability B−A |
|---|---|---|---|
| participant_1 | +2.00 | +3.57 | +3.14 |
| participant_2 | +1.29 | +2.29 | +2.29 |
| participant_3 | +2.14 | +3.71 | +3.57 |

All three participants rated Format B higher than Format A on every dimension (participant_2 shows a single trust tie at comp_7 but is still positive in mean).

### 4.4 Per-comparison breakdown

| Comp | Task | B-first? | Trust B−A (mean) | Und. B−A (mean) | Act. B−A (mean) |
|---|---|---|---|---|---|
| comp_1 | Sentiment | Yes | +2.33 | +3.33 | +3.67 |
| comp_2 | Sentiment | Yes | +2.33 | +3.33 | +2.67 |
| comp_3 | Titanic | Yes | +1.33 | +2.67 | +2.67 |
| comp_4 | Titanic | **No (A-first)** | +1.67 | +3.33 | +2.67 |
| comp_5 | Titanic | Yes | +1.33 | +3.00 | +3.00 |
| comp_6 | CIFAR-10 | Yes | +2.67 | +3.67 | +3.67 |
| comp_7 | CIFAR-10 | **No (A-first)** | +1.00 | +3.00 | +2.67 |

The two A-first comparisons (comp_4, comp_7) also show positive B−A differences, in the same direction as the five B-first comparisons. With only two A-first comparisons and no cross-schedule replication, this observation cannot distinguish a genuine format effect from a presentation-order effect.

---

## 5. Supplementary: Repeat-Exposure Stability

> **Status:** Exploratory only. Non-independent (same participants, multiple form completions). Must not be aggregated with primary results.

After the primary submission, all three participants also completed the RATER_2 and RATER_3 form schedules (accidental, not pre-registered). This provides opportunistic stability data.

| Participant | E1→E2 agreement | All-3 agreement | Provenance note |
|---|---|---|---|
| participant_1 | 92.9% (39/42) | 40.5% (17/42) | **E3 identity uncertain** (timestamp only) |
| participant_2 | 100.0% (42/42) | 100.0% (42/42) | Fully corroborated by content |
| participant_3 | 71.4% (30/42) | 33.3% (14/42) | **E3 identity uncertain** (timestamp only) |

participant_2's 100% agreement across all three exposures is the only fully corroborated trajectory. For participant_1 and participant_3, the third-exposure row assignment relies on submission timestamp proximity alone; the drop in all-3 agreement for participant_3 (33.3%) is consistent with the E3 row belonging to a different person.

**Observation (exploratory):** participant_2's complete response stability across all three independent form presentations — different card ordering, different comparison pairing — suggests these ratings reflect a stable evaluative response rather than within-session noise, at least for this participant.

---

## 6. Methodological Constraints

### 6.1 No inferential statistics
With N = 3 independent participants, the minimum attainable two-sided p-value for any rank-based test (e.g., Wilcoxon signed-rank) is 0.25, which cannot reach conventional significance thresholds. No p-values are reported. Results are descriptive observations only.

### 6.2 Presentation order confound
All primary participants used the RATER_1 schedule. The 5:2 B-first:A-first split means most comparisons were B-first. The per-comparison results in §4.4 suggest the order confound does not account for the direction of differences, but this cannot be fully controlled at N = 3.

### 6.3 Non-blind rater
One of the three participants is the study author (rater_1). This is disclosed in the protocol. The other two participants are independent.

### 6.4 Participant linkage uncertainty
The R3 form row assignment for participant_1 and participant_3 relies on timestamp adjacency. Only participant_2's triple linkage is content-corroborated. All supplementary stability claims for participant_1 and participant_3 must be treated as provisionally attributed.

### 6.5 License metadata
All dataset license information in the evidence cards is treated as a claim, not legal advice, per the project boundary defined in `docs/PROJECT_SPEC.md`.

---

## 7. Interpretation

The descriptive pattern is internally consistent:

1. **Direction:** Format B was rated higher than Format A by every participant on every dimension for every comparison, with one tied score (comp_7 trust, participant_2).

2. **Magnitude:** Understanding and Actionability show the largest differences (median +3, range +2 to +4). Trust shows a somewhat smaller but still large difference (median +2, range 0 to +3), though the current data cannot establish why — one plausible but unverified explanation is that raters weighed explicit uncertainty markers (e.g., `license_claim: unknown`) when the card contained them; this was not directly measured.

3. **Consistency across tasks:** The B−A pattern holds across sentiment, tabular, and image classification tasks and across both B-first and A-first presentation orders.

4. **Understanding item note:** The Understanding dimension was designed to capture whether participants could determine suitability from the card alone. Format A's near-floor Understanding scores (mean 1.62, median 2) reflect that a four-field minimal card systematically lacks the information needed to make that determination. This is a design characteristic, not a participant deficit.

These observations are consistent with the hypothesis that evidence-augmented cards convey materially more actionable information than minimal dataset stubs. They cannot be generalized beyond this sample (N = 3) or these specific comparisons without additional data.

---

## 8. Frozen Artifacts Reference

| Artifact | Path | Status |
|---|---|---|
| Protocol | `data/benchmarks/m8_human_eval_protocol.md` | Frozen at commit `c5bdc0c` |
| Instrument | `data/benchmarks/m8_human_eval_instrument.md` | Frozen at commit `c5bdc0c` |
| Session manifest | `data/benchmarks/m8_human_eval_session_manifest.json` | Frozen |
| Raw RATER_1 CSV | `data/raw/m8_initial_collection/rater1_form.csv` | Gitignored; SHA256 `f19fc1fb…` |
| Raw RATER_2 CSV | `data/raw/m8_initial_collection/rater2_form.csv` | Gitignored; SHA256 `0c77480f…` |
| Raw RATER_3 CSV | `data/raw/m8_initial_collection/rater3_form.csv` | Gitignored; SHA256 `a7a988ee…` |
| Primary dataset | `data/benchmarks/m8_human_eval_primary.csv` | 42 rows; gitignored |
| Repeat-exposure dataset | `data/benchmarks/m8_human_eval_repeat_exposure.csv` | 84 rows; gitignored |
| Analysis summary | `experiments/m8/results/m8_human_eval_summary.json` | Untracked |
| This document | `docs/M8_RESEARCH_FINDINGS.md` | — |
