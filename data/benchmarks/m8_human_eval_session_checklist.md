# Milestone 8 Human Evaluation: Operator Session Checklist

> **Target Audience:** Experiment Operator / Study Administrator (Not for Participants)
> **Status:** Operational Guidance for Session Execution
> **Governing Artifact Freeze:** `c5bdc0c1bd458c3d71a5181fa67232c831c3804c`
> **Governing Documents:** `docs/M8_EVALUATION.md` §12, `data/benchmarks/m8_human_eval_protocol.md`, `data/benchmarks/m8_human_eval_instrument.md`, `data/benchmarks/m8_human_eval_session_manifest.json`

---

## 1. Pre-Session Integrity Verification

Before commencing any participant session, the operator must verify:

- [ ] **Repository HEAD & Artifact Freeze:** Confirm `HEAD` contains commit `c5bdc0c` (`feat: freeze M8 human study artifacts`).
- [ ] **Benchmark Inputs & Results Intact:** Confirm `docs/M8_EVALUATION.md`, `data/benchmarks/m8_benchmark_manifest.json`, and `experiments/m8/results/m8_summary.json` are unmodified.
- [ ] **Stimulus Package Integrity:** Verify `data/benchmarks/m8_human_eval_protocol.md` contains the exact 7 stimulus pairs with 4-field Format A (`name`, `source`, `modality`, `size`).
- [ ] **Blank Instrument Verification:** Confirm `data/benchmarks/m8_human_eval_instrument.md` contains no pre-populated ratings, example scores, or illustrative participant rows.
- [ ] **Zero Prior Data:** Verify `data/benchmarks/m8_human_eval_responses.csv` does not exist or contains only the authorized 10-column header.
- [ ] **Rater Cohort Eligibility:**
  - `rater_1`: Project author (disclosed in all reporting as non-blind).
  - `rater_2`: Independent evaluator not involved in building the M1–M7 pipeline (blind).
  - `rater_3` (if target $N=3$): Independent evaluator not involved in building the M1–M7 pipeline (blind).

---

## 2. Per-Rater Setup and Schedule Reference

For each assigned rater, the operator must prepare the stimulus sequence adhering strictly to the deterministic randomization schedule (seed `20260914`):

### Task & Comparison Execution Sequence:
1. **Task 1: `task_sentiment_binary`** (Text Classification — Movie review sentiment)
   - `comp_1`: `fancyzhx/ag_news`
   - `comp_2`: `cornell-movie-review-data/rotten_tomatoes`
2. **Task 2: `task_tabular_titanic`** (Tabular Classification — Demographic attributes)
   - `comp_3`: `Breast Cancer Wisconsin (Diagnostic)`
   - `comp_4`: `Wine`
   - `comp_5`: `Adult`
3. **Task 3: `task_image_cifar`** (Image Classification — Visual object classification)
   - `comp_6`: `uoft-cs/cifar100`
   - `comp_7`: `AI-Lab-Makerere/beans`

### Presentation Order Matrix:

| Comparison ID | Dataset Name | Rater 1 Presentation | Rater 2 Presentation | Rater 3 Presentation |
| :--- | :--- | :---: | :---: | :---: |
| `comp_1` | `fancyzhx/ag_news` | **B first**, then A | **B first**, then A | **A first**, then B |
| `comp_2` | `cornell-movie-review-data/rotten_tomatoes` | **B first**, then A | **A first**, then B | **B first**, then A |
| `comp_3` | `Breast Cancer Wisconsin (Diagnostic)` | **B first**, then A | **B first**, then A | **B first**, then A |
| `comp_4` | `Wine` | **A first**, then B | **A first**, then B | **B first**, then A |
| `comp_5` | `Adult` | **B first**, then A | **B first**, then A | **B first**, then A |
| `comp_6` | `uoft-cs/cifar100` | **B first**, then A | **A first**, then B | **A first**, then B |
| `comp_7` | `AI-Lab-Makerere/beans` | **A first**, then B | **A first**, then B | **B first**, then A |

---

## 3. Participant-Facing Administration Guidelines

The operator must ensure strict experimental neutrality and prevent information leakage:

### Permitted Participant Briefing (from `m8_human_eval_instrument.md` §1):
- Read the task description and technical requirements carefully.
- Examine Card 1 and rate independently across Trust, Understanding, and Actionability.
- Examine Card 2 and rate independently across the same three dimensions.
- Cards represent alternative automated tooling outputs for dataset discovery.
- Order is randomized across comparisons and raters.
- Rate each card strictly on its own merits using the 5-point Likert scale.

### Prohibited Operator Actions (Anti-Bias & Leakage Prevention):
- **DO NOT** inform participants which card is "baseline" (Format A) or "system" (Format B).
- **DO NOT** use evaluative terms like "better", "improved", "richer", "primitive", or "experimental".
- **DO NOT** reveal the underlying ranking algorithm, diversity penalties, or suitability formulas.
- **DO NOT** reveal benchmark evaluation metrics (NDCG, coverage, ECE, Brier score).
- **DO NOT** coach participants on the Understanding item (*"I understand why this dataset was surfaced and how it connects to the specific technical requirements of the task."*). Let participants interpret the item naturally without explaining why Format A lacks explanations.
- **DO NOT** verbally introduce the task using an operator-only domain parenthetical (for example, "Movie review sentiment") unless that exact wording is present in the participant-facing instrument.

---

## 4. Data-Capture Verification Rules

During and immediately following each rating session, verify data logging into `data/benchmarks/m8_human_eval_responses.csv`:

- [ ] **Exact Header Schema:**
  ```csv
  rater_id,task_name,comparison_id,dataset_id,format_presented,presentation_order,trust_score,understanding_score,actionability_score,notes
  ```
- [ ] **Completeness per Comparison:** Exactly two response rows per comparison (one for `first` presented format, one for `second` presented format).
- [ ] **Valid Likert Values:** Every score (`trust_score`, `understanding_score`, `actionability_score`) must be an integer between `1` and `5` inclusive. No missing or NaN scores.
- [ ] **Qualitative Notes:** Notes are strictly optional; blank strings or empty fields are valid.
- [ ] **No Pseudo-Data:** Ensure no placeholder strings, test entries, or simulated rows exist.

---

## 5. Post-Session Completion Checks

- [ ] **Total Observation Count Verification:**
  - If 2 raters completed: Exactly **28 rows** ($2 \times 7 \times 2$), representing **84 individual Likert ratings**.
  - If 3 raters completed: Exactly **42 rows** ($3 \times 7 \times 2$), representing **126 individual Likert ratings**.
- [ ] **Task Coverage:** Verify all 3 tasks and all 7 comparisons are fully present with no duplicates.
- [ ] **Data Immutability:** Immediately lock or mark the completed responses CSV as read-only before running exploratory analyses.
- [ ] **Session Metadata Logging:** Record session execution date, duration, rater anonymization mapping, and environment details separately from response content.
