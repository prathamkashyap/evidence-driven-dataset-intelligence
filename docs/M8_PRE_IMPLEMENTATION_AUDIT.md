# M8 Pre-Implementation Methodological and Architectural Audit

**Audit date:** 2026-09-11
**Frozen commit inspected:** `7d6172813e78afd15488ea8995b7365be66e215c`
**Repository working tree:** clean except unstaged PDF modification in `docs/v3/` (non-code, non-blocking)
**Test suite at freeze point:** 125 tests, all passing, 0.106 s

> **Supersession note (added 2026-09-27):** This document is a historical pre-implementation
> audit dated 2026-09-11 and inspected commit `7d61728`. Its "125 tests" figure, planned
> artifact paths, and "not yet created" status statements describe that date's repository state
> only. The current baseline is `9e2ba99`, where M0–M8 are complete and the suite is
> 208/208 passing; the executed result artifacts are listed in `docs/FINAL_REPORT_EVIDENCE_MAP.md`.
> Nothing below has been rewritten.

---

## A. Actual Repository / Freeze-Point Findings

### A1. Pipeline architecture (confirmed from source)

| Module | Location | Status |
|---|---|---|
| Ingestion / schema | `src/dataset_intelligence/ingestion/` | Frozen ✓ |
| Evidence ledger | `src/dataset_intelligence/evidence/` | Frozen ✓ |
| Fingerprinting | `src/dataset_intelligence/fingerprinting/` | Frozen ✓ |
| Utility estimator | `src/dataset_intelligence/utility/` | Frozen ✓ |
| Exploration / family | `src/dataset_intelligence/exploration/` | Frozen ✓ |
| **Ranking / diversification** | `src/dataset_intelligence/ranking/` | Frozen ✓ |
| Retrieval | `src/dataset_intelligence/retrieval/` | Frozen ✓ |
| **`evaluation/`** | **does not exist yet** | M8 must create it |

### A2. Confirmed M7 parameters (hardcoded in `scoring.py` + `configs/m7_ranking.json`)

```
DEFAULT_SCORING_WEIGHTS = {w_fit: 0.35, w_util: 0.35, w_evid: 0.15, w_cov: 0.15, w_risk: 0.15}
lambda_div = 0.20
target_k   = 3
```

Positive weights **do not sum to 1.0** — they sum to 1.00 before the subtracted risk, but the risk term is a separate subtraction. The M7 formula is:
```
Score = 0.35·Sfit + 0.35·Sutil + 0.15·Sevid + 0.15·Scov − 0.15·Srisk
```
The four positive weights sum to **1.00** exactly. The risk weight (0.15) is independently subtractive. This is confirmed in source. The M8 proposal's normalization protocol is therefore correctly designed.

### A3. Rung 7 ablation: what the code actually does

In `diversification.py`, R3's greedy loop does two things jointly:
1. Calls `detect_family_redundancy(cand, selected_records)` → skip if True
2. Computes `marginal_gain = cand_score + lambda_div * marginal_div`

There is **no separate "Rung 7" mode** currently in the pipeline code. Rung 7 must be implemented as M8 evaluation code that runs the greedy loop with step 1 removed and steps 2+ identical. This is implementable in `evaluation/` without touching `diversification.py`.

### A4. Benchmark datasets: what actually exists

10 canonical records exist in `experiments/m1/results/development_corpus.jsonl`:
- `ds_c9a42d9bd6268ce4a4cf6061` rotten_tomatoes (HF)
- `ds_3e424a817c66aab45e96797a` ag_news (HF)
- `ds_40356f676278cb9903556c6e` cifar100 (HF)
- `ds_4e61d125afd0915cf8dcb4c6` beans (HF)
- `ds_69f0f69749316e8b5768ef79` iris (OpenML)
- `ds_a7472dc830bfc6394941b2f7` wine (OpenML)
- `ds_773a4c155a583474a0222bdf` Iris (UCI)
- `ds_9f128b3a604eed483953e7f8` Wine (UCI)
- `ds_c39f4b8a33e1fd6fecbf4bdc` uciml/iris (Kaggle)
- `ds_3c522d9aa8b9ec84e3b73660` uciml/pima-indians-diabetes (Kaggle)

The 15 additional proposed datasets (indices 11–25) do **not** exist as canonical records anywhere in the repository. They have placeholder IDs (`ds_hf_imdb_sentiment`, `ds_openml_mnist`, etc.) that are not `ds_` + sha256 hex, violating the canonical ID format defined in `ingestion/schema.py`.

### A5. M5 reference rubric — exact wording from `docs/M5_UTILITY.md` §7

```
Level 3 (High Compatibility):    Modality, task type, target structure, and feature
                                  characteristics match all specified task constraints.
Level 2 (Moderate Compatibility): Modality and task match, but secondary constraints
                                  (licensing uncertainty, operational access limitation,
                                  or feature differences) exist.
Level 1 (Marginal / Domain Incompatible): Modality matches, but task or domain is
                                  substantially mismatched.
Level 0 (Incompatible):          Hard incompatibility (modality clash or prohibited
                                  license/access).
```

### A6. M8 proposed rubric — exact wording from the design proposal §3C

```
Level 3 (Fully Compatible):      Exact alignment with modality, task type, target
                                  structure, and domain; clean data with verified access.
Level 2 (Favorable Compatibility): Compatible modality and task type with minor domain
                                  shift or tolerable format friction.
Level 1 (Weak / Marginal Compatibility): Compatible modality but severe domain/target
                                  mismatch, extensive missing attributes, or access barriers.
Level 0 (Incompatible):          Incompatible modality, hard constraint violation, or
                                  non-functional endpoint.
```

### A7. M5 reference judgments already used in pipeline evaluation

`tests/fixtures/m5_fixtures.json → reference_compatibility_judgments` contains 40 human-authored (level 0–3) annotations covering 10 datasets × 4 tasks. These were used during M5 development to compute Spearman ρ and NDCG against M5 utility scores. They are **inside the test fixture directory**, tightly coupled to the development pipeline evaluation loop.

### A8. Key missing items in the repository right now

- `src/dataset_intelligence/evaluation/` — does not exist
- `tests/fixtures/m8_benchmark_manifest.json` — does not exist
- Any M8 config file — does not exist
- Any canonical record for the 15 new datasets — does not exist
- M4 fingerprints, M3 evidence, M5 utility estimates for the 15 new datasets — do not exist
- Any corruption fixture files — do not exist
- PROJECT_SPEC §20 ablation items 1–4 (LLM zero-shot, DataFinder bi-encoder) — never implemented

### A9. `data/benchmarks/` directory

Exists as `data/benchmarks/.gitkeep`. Empty. The pre-registration specification says the frozen benchmark manifest must be at `tests/fixtures/m8_benchmark_manifest.json`. The `data/benchmarks/` directory is the architecturally correct place for frozen research benchmark artifacts (per `docs/IMPLEMENTATION_PLAN.md` §Storage). This is a minor naming inconsistency to resolve.

---

## B. What the Current M8 Proposal Gets Right

1. **Freeze integrity framing** — correctly states M0–M7 frozen at `7d61728`, no parameter tuning allowed.
2. **Isolation boundary** — correctly places all M8 code under `src/dataset_intelligence/evaluation/`.
3. **Preregistration-first principle** — benchmark manifest and ground-truth labels must be committed before evaluation execution.
4. **H1 denominator qualification** — "tasks containing at least one `same_family` pair" is the correct qualified denominator.
5. **H2 operational definition** — evidence divergence defined as utility neighborhood $|\Delta U| < 0.05$ is pre-registered and measurable.
6. **H3 tolerance value** — $\epsilon_{\text{tol}} = 0.03$ is pre-registered, not post-hoc.
7. **Positive weight normalization** — the normalization step (sum of positive weights to 1.0) is mathematically correct and required.
8. **Risk weight independence** — correctly treats $w_{\text{risk}}$ as an independent subtractive perturbation, not part of the convex sum.
9. **Rung 7 vs Rung 8 design intent** — correctly identifies that only `detect_family_redundancy` should differ.
10. **Calibration framing as exploratory audit** — correctly frames Brier/ECE as characterization, not optimization target.
11. **Platform-aware RSS measurement** — `ru_maxrss` bytes-vs-kibibytes handling is correctly specified.
12. **Offline execution guarantee** — zero network egress requirement is correct.
13. **Crash-rate criterion** — 0.0% crash rate across all corruption trials is the right requirement.
14. **Frozen artifact immutability** — corruption suites must operate on copies, not mutate M1-M7 artifacts.

---

## C. What MUST Be Changed Before Implementation

### C1. 🔴 BLOCKING: Ground-Truth Rubric Independence Is Not Established

**Finding:** The M8 "independent reference ground truth rubric" (§3C) is substantively the same rubric as the M5 "development reference compatibility rubric" (M5_UTILITY.md §7). A side-by-side comparison confirms:

| Level | M5 rubric language | M8 rubric language | Verdict |
|---|---|---|---|
| 3 | "Modality, task type, target structure, and feature characteristics match all specified task constraints" | "Exact alignment with modality, task type, target structure, and domain; clean data with verified access" | **Same criteria, minor rewording** |
| 2 | "Modality and task match, but secondary constraints (licensing uncertainty, operational access, or feature differences) exist" | "Compatible modality and task type with minor domain shift or tolerable format friction" | **Same criteria, partially reworded** |
| 1 | "Modality matches, but task or domain is substantially mismatched" | "Compatible modality but severe domain/target mismatch, extensive missing attributes, or access barriers" | **Same criteria, extended** |
| 0 | "Hard incompatibility (modality clash or prohibited license/access)" | "Incompatible modality, hard constraint violation, or non-functional endpoint" | **Same criteria** |

**Deeper problem:** The 40 existing M5 judgments in `tests/fixtures/m5_fixtures.json` were authored using this same rubric and were used to calibrate and validate M5 utility scores. The M5 utility components (`modality_compatibility`, `task_compatibility`, `target_compatibility`, etc.) are themselves operationalizations of the rubric levels. If M8 uses the same rubric to produce binary labels $y \in \{0,1\}$ that are then used to compute Brier score and ECE against M7 scores (which are downstream aggregates of M5 utility components), the ground truth is **not independent of the pipeline being evaluated**.

**Concrete circularity path:**
```
M5 rubric levels 0-3
    → M5 reference judgments (tests/fixtures/m5_fixtures.json)
        → M5 utility scores calibrated against these judgments (Spearman ρ = 0.97)
            → M7 candidate scores (contain M5 utility as a 0.35-weight term)
                ↑↓ [circular]
M8 rubric levels 0-3 (same criteria)
    → M8 binary labels y (cutoff ≥ 2)
        → Brier score / ECE computed against M7 scores
```

The M7 score was partly optimized (in design, not training) to agree with modality/task/target alignment — exactly what the rubric captures. Brier score and ECE computed this way measure agreement between the rubric and a score that was designed using the rubric. This is not a calibration audit; it is a consistency check.

**Required correction:**

The M8 ground-truth labels must be **procedurally separated** from the M5 rubric and M5 fixture judgments. The minimum viable non-circular design is one of the following:

> **Option A (Recommended — Dual-Annotator Protocol):** Have an independent annotator (someone who has not seen the M5/M7 score outputs and is not the original pipeline developer) apply a freshly written rubric based on the raw dataset metadata and task descriptions only. Annotator must not have access to M5 utility scores, M7 ranking outputs, or the existing `m5_fixtures.json` judgments. Disagreements are resolved by majority or adjudicated. The annotation protocol, annotator identity (pseudonymized), and inter-annotator agreement statistic (Cohen's κ) are committed as part of the pre-registration artifact.

> **Option B (Downstream-Task Ground Truth):** Define ground truth for tasks that have an implementable downstream evaluation: for each (dataset, task) pair, actually run a standardized lightweight training experiment on the dataset and measure a task metric (accuracy, F1). Any dataset achieving metric ≥ threshold is labeled $y=1$. This is measurable, objective, and completely independent of M5/M7 internals.

> **Option C (Scoped Honest Framing — Minimum Viable):** If independent annotation is not feasible before M8 deadline, explicitly reframe the calibration analysis: remove the claim of "independent binary ground truth" and instead label it as a "pipeline consistency audit" — measuring whether M7 scores are consistent with the same task-compatibility criteria used to design M5. State explicitly that this is not an independent external calibration. Drop the Brier/ECE analysis or retain it only with this honest framing. This eliminates the circularity claim but weakens the research contribution.

**Decision required from you before implementation proceeds.**

---

### C2. 🔴 BLOCKING: 15 New Benchmark Datasets Have No Canonical Records or Pipeline Artifacts

**Finding:** The 15 proposed new datasets (indices 11–25 in §3A) do not exist as canonical records in the repository. They have placeholder IDs that violate the canonical schema (IDs must be `ds_` + first 24 hex chars of sha256, as computed by `ingestion/schema.py`). They have no M3 evidence, no M4 fingerprints, and no M5 utility estimates. The pipeline cannot evaluate them.

**Required correction:** Before preregistration, for each of the 15 new datasets:
1. Run the M1 ingestion pipeline to produce a real canonical record with a real `internal_id`.
2. Run M3 evidence harvesting.
3. Run M4 fingerprinting (with offline fixtures where network access is unavailable).
4. Run M5 utility estimation across all 8 M8 tasks.
5. Commit the resulting artifacts to `experiments/m8/corpus/` (not `experiments/m1/` — keep M1 frozen).

These records and their pipeline artifacts must exist and be committed **before** the preregistration contract is finalized and before M8 evaluation runs.

---

### C3. 🔴 BLOCKING: Human Evaluation Requirement in PROJECT_SPEC §19 Is Unaddressed

**Finding:** `docs/PROJECT_SPEC.md` §19 explicitly lists as a required evaluation metric:

> **Human evaluation:** Compare plain metadata cards with evidence-backed recommendation cards on trust, understanding and actionability.

`docs/PROJECT_SPEC.md` §21 (Development Roadmap) explicitly includes **"human evaluation"** as a deliverable of M8.

The current M8 proposal contains **zero human evaluation protocol**. This is a compliance gap against the project's own source-of-truth specification.

**Required correction:** One of the following must be resolved before M8 is frozen:

> **Option A (Implement Minimal Human Evaluation):** Design a minimal study comparing plain metadata cards (dataset name + description only) vs. evidence-backed M7 recommendation cards on 3 dimensions: trust, understanding, actionability. Even a within-subjects study with the researcher(s) as evaluators on 2–3 tasks and 3–5 datasets per task, rated on a 5-point Likert scale, satisfies the specification. The protocol (stimuli, rating instrument, task instructions, analysis method) must be committed before M8 benchmark run.

> **Option B (Explicit Documented Scope-Out):** If human evaluation is out of scope due to resource/time constraints, this exclusion must be **explicitly documented** in `docs/M8_EVALUATION.md` with:
>   - The exact PROJECT_SPEC requirement being waived
>   - The specific justification for the waiver
>   - A statement that this constitutes a known gap in the research deliverable
>   - Any alternative automated proxy that partially addresses the intent (e.g., comparing recommendation card explanation coverage vs. a naive metadata-only baseline)
>
> This document must be committed to the repository before M8 is frozen.

**This cannot be silently omitted.** Either implement it minimally or explicitly document the gap.

---

### C4. 🟡 REQUIRED: Ablation Rungs 0–4 Have Implementation Gaps

**Finding:** PROJECT_SPEC §20 ablation ladder defines 10 rungs. The M8 proposal simplifies this to 8 rungs and omits:
- **Rung 1 (LLM zero-shot recommendation):** Never implemented anywhere in M0–M7.
- **Rung 4 (DataFinder-style trained bi-encoder):** Never implemented.

The M8 proposal maps these to BM25-only and Dense-only instead, but these are also not complete because the M2 dense encoder in the repository uses `TestDenseEncoder` (a stub that returns cosine similarity on random vectors) for offline tests; the real `SentenceTransformersEncoder` was never benchmarked against the M8 25-dataset corpus.

**Required correction:**
- Explicitly document in the M8 spec which PROJECT_SPEC ablation rungs are being **excluded and why**, or implement them.
- Do not silently relabel rungs to make the ladder appear complete.
- The BM25-only and Dense-only rungs are implementable from existing M2 code and should be retained as defined.
- LLM zero-shot and DataFinder bi-encoder are out of scope for resource reasons — this must be explicitly stated.

---

### C5. 🟡 REQUIRED: H2 Acceptance Criterion Is Not Pre-Registered

**Finding:** Hypothesis H2 states that R2/R3 "reorders candidates" to prioritize corroborated evidence. This is stated qualitatively but has **no quantitative acceptance criterion** (unlike H1 which is "0 redundant pairs" and H3 which is $\bar{U}(R3) \geq \bar{U}(R1) - 0.03$).

The M7 development corpus showed that R1 and R2 produced **identical** aggregate outcomes, and the M7 results document explicitly says H2 was "Not Demonstrated." The M8 proposal does not pre-register a specific measurable acceptance criterion for H2.

**Required correction:** Either:
- Pre-register a specific H2 acceptance criterion: e.g., "On at least $X\%$ of $\mathcal{T}_{\text{divergent}}$ tasks, R2 and R3 rank the corroborated-evidence candidate above the utility-tied conflicted/unknown candidate." Specify $X$ before evaluation.
- Or reclassify H2 as an **exploratory analysis** with no pre-registered acceptance criterion, and label it explicitly as such.

---

### C6. 🟡 REQUIRED: Calibration Score-Mapping Has a Math Error

**Finding:** M7 `score_candidate_r2` has raw range $[-0.15, 1.00]$. The M8 calibration protocol maps:
$$S_{\text{prob}}(d) = \max(0.0, \min(1.0, \text{Score}_{\text{cand}}(d)))$$

This **clips** negative scores to 0.0 rather than linearly normalizing them. All candidates with scores in $[-0.15, 0.0]$ get $S_{\text{prob}} = 0.0$, collapsing the resolution in the low-scoring range. The ECE bins in the $[0.0, 0.2]$ range will receive an inflated number of "minimum score" candidates with varying true labels — degrading ECE calibration validity.

**Required correction:** Use a proper linear normalization into $[0,1]$:
$$S_{\text{prob}}(d) = \frac{\text{Score}_{\text{cand}}(d) - (-0.15)}{1.00 - (-0.15)} = \frac{\text{Score}_{\text{cand}}(d) + 0.15}{1.15}$$

Pre-register this formula before evaluation.

---

### C7. 🟡 REQUIRED: Dispersion Direction in H3 Is Poorly Specified

**Finding:** H3 states "while strictly improving set-level attribute dispersion ($\text{Dispersion}(R3) > \text{Dispersion}(R1)$)." But the M7 development corpus result shows `mean_diversity` of R3 (0.5000) is **lower** than R1 (0.5278). The dispersion in R3 decreases because R3 eliminates a mirror pair and ends up with smaller sets (k=2 instead of k=3 in some tasks), not because it reduces diversity per se.

Requiring $\text{Dispersion}(R3) > \text{Dispersion}(R1)$ as a strict invariant would cause H3 to **fail on the development corpus** using the current metric. This cannot be left as-is; it is either a metric definition problem or a wrong acceptance criterion.

**Required correction:** The correct claim is:
> R3 eliminates same-family redundancy (H1 criterion) without reducing mean set utility below $\epsilon_{\text{tol}}$ (H3 criterion). Mean pairwise attribute diversity is a secondary diagnostic, not a strict acceptance criterion for H3.

Revise H3 to remove the strict dispersion inequality, or use a **normalized per-slot** diversity metric that accounts for set size differences.

---

### C8. 🟡 REQUIRED: Robustness Suite Must Specify Isolation Mechanism

**Finding:** The proposal states corruptions must "operate on copies of frozen artifacts." However, it does not specify the concrete mechanism. If the M8 evaluation code imports M1–M7 modules and passes corrupted data objects through them, this is architecturally sound. But if corruptions mutate in-memory objects that are shared across evaluation runs (e.g., by reference semantics), results could bleed between corruption suites.

**Required correction:** The pre-registration document must specify: corrupted records are Python `dataclass(frozen=True)` instances constructed by the M8 evaluation harness from scratch (not by mutating existing canonical records). The M8 harness creates new `CanonicalDataset` instances with specified field perturbations, passes them to the frozen pipeline, and measures outputs. Original `experiments/m1/results/development_corpus.jsonl` is never modified.

---

### C9. 🟡 REQUIRED: `data/benchmarks/` vs `tests/fixtures/` Disambiguation

**Finding:** The M8 proposal places the benchmark manifest at `tests/fixtures/m8_benchmark_manifest.json`. The `docs/IMPLEMENTATION_PLAN.md` §Storage designates `data/benchmarks/` as the location for "frozen inputs/judgments." The `tests/fixtures/` directory is for unit-test fixtures.

A frozen research benchmark manifest is a research artifact, not a unit-test fixture. Placing it in `tests/fixtures/` conflates testing infrastructure with the authoritative evaluation artifact.

**Required correction:** Place the benchmark manifest at `data/benchmarks/m8_benchmark_manifest.json`. The `tests/test_m8_evaluation.py` test should load it from there and verify its integrity (hash, record count, label count). This maintains the correct separation between research artifacts and test infrastructure.

---

## D. Final M8 Hypotheses and Acceptance Criteria

After corrections, the pre-registered hypotheses should be:

### H1 — Set-Level Lineage Redundancy Elimination (Engineering Invariant)
- **Denominator:** All benchmark tasks $t \in \mathcal{T}_{\text{redundant}}$ where at least one `same_family` pair exists among the top-$k$ R1-selected candidates.
- **Dependent variable:** `same_family_redundancy_count` in recommended set $S^*$.
- **Acceptance criterion:** R3 achieves `same_family_redundancy_count = 0` on **100%** of $\mathcal{T}_{\text{redundant}}$ tasks.
- **Classification:** Engineering invariant (already proven by code design and unit tests; M8 confirms it at scale).

### H2 — Evidence Disambiguation under Operational Evidence Divergence (Exploratory)
- **Denominator:** All benchmark tasks $t \in \mathcal{T}_{\text{divergent}}$ where eligible candidates exist in a $|\Delta U| < 0.05$ utility neighborhood with differing evidence states.
- **Dependent variable:** Rank ordering of the corroborated-evidence candidate vs. the utility-equivalent conflicted/unknown candidate under R2 vs. R1.
- **Acceptance criterion:** *(Exploratory — no binary acceptance criterion; report direction and frequency of reordering across all $\mathcal{T}_{\text{divergent}}$ tasks.)*
- **Classification:** Exploratory analysis.

### H3 — Utility Retention under Diversification (Empirical Hypothesis)
- **Denominator:** All 8 benchmark tasks.
- **Dependent variable:** $\bar{U}(R3)$ vs. $\bar{U}(R1)$ (mean set utility across all tasks).
- **Acceptance criterion:** $\bar{U}(R3) \geq \bar{U}(R1) - 0.03$ (pre-registered $\epsilon_{\text{tol}} = 0.03$).
- **Classification:** Empirical hypothesis.

### H4 — Popularity Neutrality (Engineering Invariant)
- **Dependent variable:** Spearman ρ between raw popularity metric (downloads/stars) and final rank position, holding task constant.
- **Acceptance criterion:** $|\rho| < 0.10$ across all tasks (no statistically meaningful correlation when task suitability is fixed).
- **Classification:** Engineering invariant (already tested by unit test `test_popularity_neutrality_in_scoring`; M8 confirms at scale with real popularity variance).

### H5 — Role Instantiation Groundedness (Engineering Invariant)
- **Dependent variable:** Count of roles assigned without empirical precondition met; count of ungrounded claims in explanation text.
- **Acceptance criterion:** Zero roles assigned without empirical criteria; zero hallucinated claims.
- **Classification:** Engineering invariant.

---

## E. Final Preregistration Artifact Checklist

All items marked **[BEFORE RUN]** must exist, be committed, and be hash-verified **before** the first final M8 benchmark execution.

### Protocol
- `[BEFORE RUN]` `docs/M8_EVALUATION.md` — frozen evaluation specification (this document, revised to incorporate all corrections from §C)
- `[BEFORE RUN]` Explicit scope-out note for human evaluation (per §C3) — OR human evaluation protocol

### Benchmark Manifest (Research Artifact)
- `[BEFORE RUN]` `data/benchmarks/m8_benchmark_manifest.json` — authoritative manifest containing: 25 canonical dataset IDs (real IDs, not placeholders), 8 task IDs with full `TaskSpecification` fields, inclusion rationale, version/snapshot identifiers, content hashes, and lineage cluster assignments

### Canonical Records for New Datasets
- `[BEFORE RUN]` `experiments/m8/corpus/m8_extended_corpus.jsonl` — 25 canonical records (10 existing + 15 new), each with a real `internal_id` matching sha256 derivation
- `[BEFORE RUN]` `experiments/m8/evidence/m8_evidence_ledger.jsonl` — M3 evidence for all 25 datasets
- `[BEFORE RUN]` `experiments/m8/fingerprints/m8_fingerprints.jsonl` — M4 fingerprints for all 25 datasets
- `[BEFORE RUN]` `experiments/m8/utility/m8_utility_estimates.jsonl` — M5 utility estimates (Baseline C) for all 200 (25 × 8) dataset-task pairs

### Independent Ground-Truth Labels
- `[BEFORE RUN]` `data/benchmarks/m8_ground_truth_labels.json` — 200 binary labels $y_{d,t} \in \{0,1\}$, authored **independently** of M5/M7 pipeline outputs using the corrected non-circular protocol (per §C1)
- `[BEFORE RUN]` `data/benchmarks/m8_rubric.md` — frozen annotation rubric with procedural separation statement
- `[BEFORE RUN]` `data/benchmarks/m8_annotation_protocol.md` — annotator instructions, conflict resolution procedure, inter-annotator agreement metric (if dual-annotator option is used)

### Corruption Fixtures
- `[BEFORE RUN]` `data/benchmarks/m8_corruption_fixtures.json` — defines all 4 corruption suites with exact field mutations, deletion rates, injected values, and HTTP error codes per suite

### Sensitivity Configuration
- `[BEFORE RUN]` `configs/m8_sensitivity.json` — all perturbation grids: positive weight perturbations (±20%), risk weight perturbations, $\lambda_{\text{div}}$ sweep values, $k$ values
- `[BEFORE RUN]` Pre-registered stability acceptance criteria: $J \geq 0.80$, Kendall's $\tau \geq 0.75$

### Seeds and Reproducibility
- `[BEFORE RUN]` `configs/m8_evaluation.json` — evaluation harness config including: random seed (if any randomness exists — note: current pipeline is fully deterministic, so confirm no stochastic step is introduced in M8), software package versions (from `pip freeze`), Python version, OS/hardware metadata, M7 frozen commit hash

### Evaluation Code
- `[BEFORE RUN]` `src/dataset_intelligence/evaluation/__init__.py`
- `[BEFORE RUN]` `src/dataset_intelligence/evaluation/ablations.py` (Rung 0–8 implementations)
- `[BEFORE RUN]` `src/dataset_intelligence/evaluation/calibration.py` (Brier/ECE with corrected linear normalization)
- `[BEFORE RUN]` `src/dataset_intelligence/evaluation/robustness.py` (corruption suites)
- `[BEFORE RUN]` `src/dataset_intelligence/evaluation/sensitivity.py` (weight perturbation, $\lambda_{\text{div}}$ sweep)
- `[BEFORE RUN]` `src/dataset_intelligence/evaluation/metrics.py` (Kendall's τ, Jaccard, long-tail metrics, diversity metrics)
- `[BEFORE RUN]` `src/dataset_intelligence/evaluation/manifest.py` (manifest integrity verification)
- `[BEFORE RUN]` `scripts/run_m8_benchmark.py`

### Test Fixtures and Tests
- `[BEFORE RUN]` `tests/test_m8_evaluation.py` — offline unit tests covering:
  - Manifest integrity (25 datasets, 8 tasks, 200 labels, valid IDs)
  - Rung 7 vs Rung 8 single-factor isolation (same pool, scores, distance, k, tie-breaking)
  - Normalized weight perturbation logic (sum = 1.0)
  - Corrected linear score-to-probability mapping (not clipping)
  - Corruption fixture isolation (no mutation of original canonical records)
  - Platform-aware RSS measurement

### Result Artifacts (Produced by M8 Execution — NOT Before Run)
- `[AFTER RUN]` `experiments/m8/results/ablation_comparison.json`
- `[AFTER RUN]` `experiments/m8/results/calibration_report.json`
- `[AFTER RUN]` `experiments/m8/results/robustness_report.json`
- `[AFTER RUN]` `experiments/m8/results/sensitivity_report.json`
- `[AFTER RUN]` `experiments/m8/results/m8_summary.json`
- `[AFTER RUN]` `docs/M8_RESULTS.md`

---

## F. Frozen M1-M7 Components That M8 Must NOT Modify

| File / Directory | Reason |
|---|---|
| `src/dataset_intelligence/ranking/` (all files) | M7 frozen ranking, scoring, diversification, roles, explanation |
| `src/dataset_intelligence/utility/` (all files) | M5 frozen utility estimator, components, specification |
| `src/dataset_intelligence/exploration/` (all files) | M6 frozen popularity, family linkage, pool builder |
| `src/dataset_intelligence/evidence/` (all files) | M3 frozen evidence ledger, resolver, statuses |
| `src/dataset_intelligence/fingerprinting/` (all files) | M4 frozen fingerprinting pipeline |
| `src/dataset_intelligence/ingestion/` (all files) | M1 frozen canonical schema and adapters |
| `src/dataset_intelligence/retrieval/` (all files) | M2 frozen BM25, dense, RRF, metrics |
| `src/dataset_intelligence/m0/` (all files) | M0 frozen compute budget config |
| `experiments/m1/` to `experiments/m7/` (all result files) | Frozen experiment artifacts — read-only inputs to M8 |
| `configs/m7_ranking.json` | Frozen M7 parameter configuration |
| `configs/m0_compute_budget.json` through `configs/m6_popularity.json` | Frozen milestone configs |
| `tests/fixtures/m1_records.json` through `tests/fixtures/m7_fixtures.json` | Frozen development test fixtures |
| `tests/test_ranking.py` through `tests/test_retrieval.py` (existing tests) | Must continue passing; must not be modified |
| `docs/M7_RANKING.md`, `docs/M7_RESULTS.md` | Frozen M7 documentation |
| `docs/M5_UTILITY.md`, `docs/M6_LONG_TAIL.md` | Frozen milestone specifications |

---

## G. Recommended M8 Implementation Boundary

M8 must operate as a **read-only client** of all frozen components. The following is the correct dependency direction:

```
M8 Evaluation Layer (NEW)
  src/dataset_intelligence/evaluation/
  scripts/run_m8_benchmark.py
  tests/test_m8_evaluation.py
  data/benchmarks/  (new research artifacts)
  experiments/m8/   (new M8 corpus + results)
  configs/m8_evaluation.json
  configs/m8_sensitivity.json
        ↓ reads from (frozen, read-only)
  src/dataset_intelligence/ranking/pipeline.py   (RecommendationEngine.recommend())
  src/dataset_intelligence/ranking/diversification.py  (select_diversified_set())
  src/dataset_intelligence/ranking/scoring.py
  src/dataset_intelligence/ranking/signals.py
  src/dataset_intelligence/exploration/family.py  (detect_family_redundancy())
  src/dataset_intelligence/utility/estimator.py
  experiments/m1/ through experiments/m7/ (result artifacts as inputs)
```

The Rung 7 ablation is implemented entirely within `src/dataset_intelligence/evaluation/ablations.py` by copying the greedy loop logic with `detect_family_redundancy` removed — **not** by modifying `diversification.py`.

---

## H. Final GO / NO-GO Decision

**DECISION: CONDITIONAL NO-GO**

Implementation may not begin until the following are resolved:

### Hard Blockers (must resolve before any M8 code is written):

**1. Ground-truth independence (§C1):** The M8 rubric is substantively the same as the M5 rubric and cannot serve as independent external validation. The circularity path from M5 rubric → M5 fixtures → M5 utility scores → M7 scores → M8 Brier/ECE is concrete and methodologically disqualifying. You must choose Option A (dual-annotator), Option B (downstream-task labels), or Option C (honest reframing with explicit downscoping) before any evaluation code is written.

**2. Canonical records for 15 new datasets (§C2):** The M8 benchmark cannot be preregistered until the 15 new datasets have real canonical IDs and pipeline artifacts. Placeholder IDs with wrong formats cannot be committed as a preregistration artifact.

**3. Human evaluation decision (§C3):** PROJECT_SPEC §19 and §21 require human evaluation as a M8 deliverable. This cannot be silently absent. Either implement a minimal protocol or commit a documented scope-out before M8 implementation starts.

### Required-Before-Preregistration-Commit items (§C4–C9):

- Pre-register H2 as exploratory or provide a quantitative acceptance criterion.
- Fix calibration score-mapping to linear normalization (not clipping).
- Remove or correct the H3 strict dispersion inequality.
- Explicitly document which PROJECT_SPEC ablation rungs are out of scope.
- Specify the corruption isolation mechanism using frozen `dataclass` instances.
- Move benchmark manifest to `data/benchmarks/` per IMPLEMENTATION_PLAN.md architecture.

### What is allowed immediately:
- Creating the `src/dataset_intelligence/evaluation/` package skeleton (empty modules only).
- Running M1 ingestion for the 15 new datasets to generate real canonical IDs.
- Drafting the annotation rubric and ground-truth annotation protocol.
- Writing `tests/test_m8_evaluation.py` structural scaffolding.
- Committing `docs/M8_EVALUATION.md` (this document, revised) as the protocol record.

**A full GO decision is issued when items 1–3 above are resolved and confirmed.**
