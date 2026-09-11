# M8 — Research Evaluation Protocol

## Status: DESIGN LOCKED — execution artifacts not yet created or Git-frozen

B1/B2/B3 decisions are recorded (§2) and C4–C9 corrections are incorporated. This
document is preregistration-ready as a **design** artifact. It is not yet
preregistration-**complete**: `configs/m8_evaluation.json`, `scripts/run_m8_benchmark.py`,
the `data/benchmarks/` manifest/exclusion-log/human-eval files, the 15-dataset ingestion,
and the evaluation harness itself do not exist yet. No benchmark run may occur until those
are created and this document is updated to reflect their real, checked-in paths. This document
is currently untracked, so the design is not Git-frozen until it is reviewed and committed.

**Frozen commit:** `7d6172813e78afd15488ea8995b7365be66e215c`
**Frozen at:** M0–M7 complete, 125 tests passing
**Audit date:** 2026-09-11
**Design-lock revision:** 2026-09-11 (B1–B3 recorded, C4–C9 applied, stimulus-fallback and
ECE-framing fixes applied)

---

## 1. Core Invariants

1. M0–M7 are **strictly frozen** at commit `7d61728`. No ranking formulas, retrieval weights,
   evidence ledgers, utility heuristics, family linkage rules, or recommendation role definitions
   may be altered during M8.
2. The benchmark manifest, canonical dataset IDs, the non-independent reference labels used solely
   for the M7 Pipeline Consistency Audit, corruption
   fixtures, and statistical hypotheses must be **committed before** running the evaluation harness.
   No post-hoc tuning of thresholds or metrics is permitted.
3. All M8 evaluation code is isolated under `src/dataset_intelligence/evaluation/` and
   `scripts/run_m8_benchmark.py`. It consumes M1–M7 interfaces as a read-only client.

---

## 2. Blocking Decisions Required Before Preregistration

### B1 — Ground-Truth Independence Method

The proposed M8 compatibility rubric (§3C of design spec) is substantively identical to the M5
Development Reference Compatibility Rubric (docs/M5_UTILITY.md §7). The M5 rubric criteria
operationalize the same modality/task/target dimensions used to compute M5 utility scores.
Using the same rubric to produce M8 binary labels and then computing Brier/ECE against M7 scores
(which contain M5 utility at 0.35 weight) is circular.

**Required decision — choose one:**

**Option A (Dual-Annotator Protocol):**
An annotator who has not seen M5/M7 outputs applies a freshly written rubric based only on raw
dataset metadata and task descriptions. The annotation protocol, annotator identity (pseudonymized),
and inter-annotator agreement (Cohen's κ) are committed as pre-registration artifacts. If Option A
were selected, it would require a distinct independent-annotation protocol; it is not the
Option C `data/benchmarks/m8_annotation_protocol.md` artifact.

**Option B (Downstream-Task Ground Truth):**
For each (dataset, task) pair in a feasible subset, run a standardized lightweight training
experiment and measure a task metric (accuracy, F1). Any dataset achieving metric ≥ defined
threshold is labeled y=1. This is objective and independent of M5/M7.

**Option C (Honest Reframing — Minimum Viable):**
Remove the claim of "independent ground truth." Relabel the calibration analysis as a
"pipeline consistency audit" measuring whether M7 scores are consistent with the M5 design
rubric. Document explicitly that this is not external validation. Retain Brier/ECE only with
this framing. Commit this limitation statement before M8 is frozen.

**Decision recorded here:** **Option C — M7 Pipeline Consistency Audit.**

No independent annotator is available for this capstone. The analysis in §7 is renamed
from "Calibration Protocol" to **"M7 Pipeline Consistency Audit"** and is reframed as
follows:

- This audit measures whether M7 scores are internally consistent with the M5 Development
  Reference Compatibility Rubric that informed M5 utility — **not** external validity, and
  **not** independent calibration.
- Brier score and ECE are retained *only* as descriptive diagnostics of that internal
  consistency. Neither metric may be reported, captioned, or interpreted as evidence that
  M7 scores are calibrated probabilities, well-calibrated, or externally validated.
- Any results table or write-up presenting Brier/ECE under this protocol must carry this
  limitation statement adjacent to the numbers, not only in a separate limitations section.
- If a genuinely independent annotator becomes available before the final benchmark run,
  this decision should be revisited in favor of Option A.

---

### B2 — 15 New Dataset Canonical Records

Datasets 11–25 in the proposed benchmark have no canonical records, no real internal IDs,
no M3 evidence, no M4 fingerprints, and no M5 utility estimates. They must be prepared before
the preregistration manifest can be committed. Results go to `experiments/m8/corpus/` — M1
artifacts are not modified.

**Required decision:**
Is outbound network access available for ingesting these 15 datasets, or must offline fixture
records be hand-authored from public metadata? Ingestion must match M0 policy (cache, no
indiscriminate downloads).

**Decision recorded here:** **Real ingestion only. Hand-authored records are prohibited.**

### One-Time M8 Corpus Acquisition / Preparation

Canonical records, M3 evidence, M4 fingerprints, and M5 utility estimates can only be
produced through a separately logged acquisition/preparation phase that calls frozen M1–M5
module interfaces against permitted real sources. This phase may access permitted external
sources only while obeying M0 access and budget policies, caching every permitted response, and
without modifying frozen M1–M5 code. It produces committed M8 corpus, evidence, fingerprint,
and utility artifacts. A hand-authored record can never legitimately reach
`direct_observation` / `observed` status — it would silently misrepresent an unverified claim as
verified evidence, undermining the distinction the whole evidence ledger exists to preserve.
This is prohibited regardless of time pressure.

**Pre-registered inclusion/exclusion rule (fixed before any ingestion is attempted):**

> The 15 datasets listed in §3A are the target set, attempted in the order listed. Each is
> attempted through the separately logged acquisition/preparation phase exactly once. A dataset is
> **included** in the frozen benchmark only if it produces a valid canonical record plus
> the required M3/M4/M5 artifacts through that path. A dataset that fails — for any reason,
> including network access, licensing, schema incompatibility, or endpoint failure — is
> **excluded** with the specific failure reason recorded in
> `data/benchmarks/m8_corpus_exclusions.md`. Failed datasets are **not** retried with
> altered parameters and are **not** replaced with substitute datasets. The final evaluated
> corpus size (10 + however many of the 15 succeed) is reported as-is, without adjustment,
> in the frozen benchmark manifest and in `docs/M8_RESEARCH_FINDINGS.md`.

This rule is fixed now, before it is known which datasets will succeed, specifically to
prevent post-hoc substitution of easier datasets for ones that fail.

All acquisition attempts and exclusions are recorded. The acquisition/preparation phase is not
the frozen M8 evaluation run.

### Frozen Offline M8 Evaluation

`scripts/run_m8_benchmark.py` operates only on committed or local cached M8 artifacts. It has
zero network egress, performs no live source acquisition, and does not modify M0–M7 artifacts.

---

### B3 — Human Evaluation Compliance

`docs/PROJECT_SPEC.md` §19 and §21 explicitly require human evaluation as a M8 deliverable:

> *Compare plain metadata cards with evidence-backed recommendation cards on trust,
> understanding and actionability.*

The original M8 design contained no human evaluation protocol; §12 now resolves that gap.

**Required decision — choose one:**

**Option A (Implement Minimal Study):**
A within-subjects study comparing plain metadata cards vs. M7 recommendation cards on the tasks
and recommendation sets selected under §12, rated on trust / understanding / actionability
(5-point Likert). Protocol (stimuli, rating instrument, analysis method) committed before
evaluation run.

**Option B (Explicit Documented Scope-Out):**
Commit a statement to this document that:
- Identifies the exact PROJECT_SPEC requirement being waived
- Provides specific justification (resource/time constraint)
- Acknowledges this as a known gap in the research deliverable
- Names any automated proxy metric partially addressing the intent

**Decision recorded here:** **Option A — Minimal Study.** Protocol specified in §12.

No participant data has been collected. This protocol must be committed before any rating
session begins, and no results may be entered into this document until real sessions occur.

---

## 3. Frozen Benchmark Manifest Specification

### 3A. 25 Benchmark Datasets

10 development datasets from M1 (IDs confirmed from `experiments/m1/results/development_corpus.jsonl`):

| Index | Canonical ID | Dataset | Source |
|---|---|---|---|
| 1 | `ds_c9a42d9bd6268ce4a4cf6061` | rotten_tomatoes | Hugging Face |
| 2 | `ds_3e424a817c66aab45e96797a` | ag_news | Hugging Face |
| 3 | `ds_40356f676278cb9903556c6e` | cifar100 | Hugging Face |
| 4 | `ds_4e61d125afd0915cf8dcb4c6` | beans | Hugging Face |
| 5 | `ds_69f0f69749316e8b5768ef79` | iris | OpenML |
| 6 | `ds_a7472dc830bfc6394941b2f7` | wine | OpenML |
| 7 | `ds_773a4c155a583474a0222bdf` | Iris | UCI |
| 8 | `ds_9f128b3a604eed483953e7f8` | Wine | UCI |
| 9 | `ds_c39f4b8a33e1fd6fecbf4bdc` | uciml/iris | Kaggle |
| 10 | `ds_3c522d9aa8b9ec84e3b73660` | uciml/pima-indians-diabetes | Kaggle |

15 additional datasets (indices 11–25 — **IDs TBD after M1 ingestion**):
imdb, glue/sst2, tweet_eval/sentiment, dbpedia_14, cifar10, fashion_mnist,
diabetes (OpenML), titanic (OpenML), credit-g (OpenML), mnist_784 (OpenML),
heart_disease (UCI), breast_cancer_wisconsin (UCI), adult (UCI),
titanic (Kaggle), heart-disease-uci (Kaggle).

### 3B. 8 Evaluation Tasks

| Task ID | Modality | Target | Has Mirrors? |
|---|---|---|---|
| `task_sentiment_binary` | Text | Binary (2 classes) | No |
| `task_news_multiclass` | Text | Multiclass (4 classes) | No |
| `task_tabular_iris` | Tabular | Multiclass (3 classes, 4 features) | Yes |
| `task_image_cifar` | Image | Multiclass (100 classes) | Yes |
| `task_tabular_diabetes` | Tabular | Binary (2 classes, 8 features) | Yes |
| `task_tabular_wine` | Tabular | Multiclass (3 classes, 13 features) | Yes |
| `task_tabular_titanic` | Tabular | Binary (2 classes, demographic) | Yes |
| `task_image_leaf_disease` | Image | Multiclass (3 classes) | No |

Five of the eight tasks are intended mirror-target tasks. Actual membership in the qualified
$\mathcal{T}_{\text{redundant}}$ set is determined from the committed benchmark/candidate pool
using H1's definition.

### 3C. Ground-Truth Annotation

**Method:** Reference Level rubric (unchanged from prior design) applied by the project
author. Per the B1 decision, these labels are **not** an independent ground truth. They
are used exclusively for the M7 Pipeline Consistency Audit in §7, not for any claim of
external validation.

**Binary suitability cutoff:** $y_{d,t} = 1$ if Reference Level $(d,t) \geq 2$, else $0$.

**Annotation artifacts** (committed before evaluation run):
- `data/benchmarks/m8_benchmark_manifest.json`
- `data/benchmarks/m8_ground_truth_labels.json`
- `data/benchmarks/m8_rubric.md`
- `data/benchmarks/m8_annotation_protocol.md` — documents the project-author reference-label
  procedure used solely for the M7 Pipeline Consistency Audit; it is not an independent
  ground-truth annotation protocol.

---

## 4. Pre-Registered Hypotheses

### H1 — Lineage Redundancy Elimination (Engineering Invariant)
- **Denominator:** All tasks $t \in \mathcal{T}_{\text{redundant}}$ containing at least one
  `same_family` pair among top-$k$ R1 candidates.
- **Acceptance criterion:** R3 achieves `same_family_redundancy_count = 0` on **100%** of
  $\mathcal{T}_{\text{redundant}}$ tasks.

### H2 — Evidence Disambiguation (Exploratory)
- **Denominator:** All tasks $t \in \mathcal{T}_{\text{divergent}}$ where eligible candidates
  exist within $|\Delta U| < 0.05$ utility neighborhood with differing evidence states.
- **Acceptance criterion:** *Exploratory* — report direction and frequency of reordering.
  No binary pass/fail criterion.

### H3 — Utility Retention under Diversification (Empirical)
- **Acceptance criterion:** $\bar{U}(\text{R3}) \geq \bar{U}(\text{R1}) - 0.03$ across all
  8 benchmark tasks. (Pre-registered $\epsilon_{\text{tol}} = 0.03$.)
- **Note:** Mean pairwise attribute diversity is a secondary diagnostic, not a strict criterion.

### H4 — Popularity Neutrality (Engineering Invariant)
- **Acceptance criterion:** $|\rho(\text{popularity, rank})| < 0.10$ across all tasks
  when task suitability is held constant.

### H5 — Role Groundedness (Engineering Invariant)
- **Acceptance criterion:** Zero roles assigned without empirical precondition met; zero
  ungrounded claims in recommendation card explanations.

---

## 5. Ablation Ladder (8 Rungs)

| Rung | Name | What changes vs. previous rung |
|---|---|---|
| 0 | Corpus order (random baseline) | No intelligence |
| 1 | BM25-only retrieval | Pure lexical scoring |
| 2 | Dense-only retrieval | Pure semantic scoring |
| 3 | Hybrid RRF (M2 baseline) | Lexical + semantic fusion |
| 4 | Hybrid + Hard Gating | Hard constraint enforcement added |
| 5 | M7 R1 — Utility-Only | Task utility added, no evidence/risk |
| 6 | M7 R2 — Multi-Objective Candidate | Evidence + risk signals added; no set diversification |
| 7 | Farthest-First without Family Check | Greedy marginal gain; `detect_family_redundancy` **removed** |
| 8 | M7 R3 — Proposed Full System | `detect_family_redundancy` **restored**; single-factor isolation |

**Rungs 7 and 8 are strictly controlled:** identical candidate pool, identical scoring weights,
identical distance function, identical $k$, identical tie-breaking. Only the family exclusion
check differs.

**Rung 7 implementation:** Will be implemented entirely within `src/dataset_intelligence/evaluation/ablations.py`
by running the greedy loop without `detect_family_redundancy`. `diversification.py` is NOT modified.

**Excluded from spec (out of scope — documented):**
- PROJECT_SPEC §20 Rung 1 (LLM zero-shot) — excluded; no LLM integration implemented.
- PROJECT_SPEC §20 Rung 4 (DataFinder bi-encoder) — excluded; trained retriever not within
  M0 compute budget. These exclusions are acknowledged as known gaps.

---

## 6. Parameter Sensitivity Protocol

### Positive Weight Perturbation (normalized)
For each of $w_{\text{fit}}=0.35$, $w_{\text{util}}=0.35$, $w_{\text{evid}}=0.15$, $w_{\text{cov}}=0.15$:
1. Perturb by $\pm 20\%$: $w_i' = w_i \cdot (1 \pm 0.20)$
2. Renormalize: $\tilde{w}_i = w_i' / \sum_j w_j'$ (positive weights sum to exactly 1.0)

### Risk Weight Perturbation (independent)
$w_{\text{risk}} \in \{0.12, 0.15, 0.18\}$ (independently, not part of convex sum)

### $\lambda_{\text{div}}$ Sweep
$\lambda_{\text{div}} \in [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]$
where $\lambda_{\text{div}} = 0.00$ is the explicit un-diversified control.

### Stability Criteria (pre-registered)
- Mean Jaccard similarity $J(S^*_{\text{default}}, S^*_{\text{perturbed}}) \geq 0.80$
- Kendall's $\tau \geq 0.75$
across all $\pm 20\%$ normalized perturbations.

---

## 7. M7 Pipeline Consistency Audit (formerly "Calibration Protocol")

**Framing:** This is **not** an independent calibration analysis. Per the B1 decision
(§2), the binary labels used here derive from the same rubric family that informed M5
utility, so this audit measures internal consistency between M7 scores and M5's own
design criteria — not external validity, and not evidence that M7 scores are calibrated
probabilities. Calibration was never an optimization objective of M7.

**Ground truth:** Reference Level labels $y \in \{0,1\}$ per §3C — non-independent,
consistency-audit use only.

**Reporting requirement:** Any table or figure presenting the Brier score or ECE values
below must include this limitation statement in the same view, not only in a separate
limitations appendix.

**Score mapping (corrected — linear normalization, not clipping):**
$$S_{\text{prob}}(d) = \frac{\text{Score}_{\text{cand}}(d) + 0.15}{1.15}$$
This maps the full range $[-0.15, 1.00]$ linearly to $[0.0, 1.0]$.

**Brier Score:**
$$\text{BS} = \frac{1}{N} \sum_{i=1}^N (S_{\text{prob}}(d_i) - y_i)^2$$

**Expected Calibration Error — reported here strictly as a descriptive consistency
diagnostic per the B1/§7 framing above, not as evidence of calibration (M=5 equal-width
bins):**
$$\text{ECE} = \sum_{m=1}^5 \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$$

---

## 8. Robustness Protocol

4 corruption suites, each operating on **fresh copies** of frozen canonical records:

1. **Metadata Omission:** Delete 25%, 50%, 75% of semantic description, tags, structure fields.
2. **License Conflict Injection:** Inject contradictory license declarations across provenance entries.
3. **Modality Corruption:** Mutate declared modality strings to corrupted or unsupported values.
4. **Endpoint Failure Simulation:** Inject HTTP 500, 502, 403 codes into sample access components.

**Isolation mechanism:** Corrupted records are new `CanonicalDataset` instances constructed by
the M8 evaluation harness from scratch, with specified field perturbations. Original
`experiments/m1/results/development_corpus.jsonl` and all M1–M7 artifacts are **never mutated**.

**Degradation metrics (6):**
1. Exception/crash rate — pre-registered acceptance: exactly 0.0%
2. Hard-gating precision and recall under corruption
3. Utility delta $\Delta \bar{U}$
4. Set Jaccard overlap $J(S^*_{\text{clean}}, S^*_{\text{perturbed}})$
5. Epistemic state transition count
6. False-positive recommendation count against ground-truth labels

---

## 9. Resource Acceptance Boundaries

Measured from M0 envelope — these are **empirical acceptance criteria**, not assumed preconditions:

| Metric | Acceptance Criterion |
|---|---|
| Peak Process RSS | $\leq 128.00\ \text{MiB}$ (134,217,728 bytes) |
| Per-task recommendation latency | $\leq 20{,}000\ \text{ms}$ |
| Network egress | Zero (100% offline / cached fixtures) |

Measured via `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` with platform-aware
normalization (bytes on macOS, kibibytes on Linux).

---

## 10. Reproducibility Record

`configs/m8_evaluation.json` must include (committed before evaluation run):
- M7 frozen commit hash: `7d6172813e78afd15488ea8995b7365be66e215c`
- Python version
- Package versions (from `pip freeze`)
- OS / hardware metadata
- Random seed (confirm: current pipeline is fully deterministic; document if any stochastic step exists)
- Cache state / fixture source
- Observation timestamp

---

## 11. Frozen Components — M8 Must NOT Modify

```
src/dataset_intelligence/ranking/          # M7 frozen
src/dataset_intelligence/utility/          # M5 frozen
src/dataset_intelligence/exploration/      # M6 frozen
src/dataset_intelligence/evidence/         # M3 frozen
src/dataset_intelligence/fingerprinting/   # M4 frozen
src/dataset_intelligence/ingestion/        # M1 frozen
src/dataset_intelligence/retrieval/        # M2 frozen
src/dataset_intelligence/m0/               # M0 frozen
experiments/m1/ through experiments/m7/    # Frozen result artifacts (read-only)
configs/m7_ranking.json                    # Frozen M7 config
tests/fixtures/m1_records.json through tests/fixtures/m7_fixtures.json
tests/test_ranking.py through tests/test_utility.py (existing tests must continue passing)
docs/M7_RANKING.md, docs/M7_RESULTS.md
docs/M5_UTILITY.md, docs/M6_LONG_TAIL.md
```

---

## 12. Human Evaluation Protocol (B3)

Satisfies `PROJECT_SPEC.md` §19/§21: compare plain metadata cards against evidence-backed
M7 recommendation cards on trust, understanding, and actionability. This section is the
committed protocol only — no sessions have been run and no results exist yet.

**Participants/raters:** Minimum 2, target 3. The project author may be one rater but is
disclosed as non-blind; at least one additional rater should be someone not involved in
building the pipeline, if available before the study runs.

**Stimuli:** 3 of the 8 benchmark tasks (selected to span text, tabular, and image
modalities). Each selected task contributes up to 3 available datasets from that task's M7
recommendation set. If fewer than 3 recommendations are available for a task (`|S*| < 3`, as
M7's own design permits for constrained tasks), use all available recommendations for that task.
The actual number of comparisons is determined after frozen task/set selection and recorded
before any rating session. For each comparison, two card formats are shown for the same dataset:
(a) a plain metadata card (name, source, modality, size — no evidence/role/explanation
fields) and (b) the corresponding M7 `RecommendationCard`.

**Procedure:** Within-subjects. Each rater sees both formats for all selected comparisons.
Presentation order of format (a) vs (b) is randomized per comparison per rater to
counter order effects. Raters are told which task each comparison is for but not which
baseline (R1/R2/R3) produced the recommendation card.

**Rating instrument:** 5-point Likert scale on three dimensions per card — trust,
understanding, actionability — collected independently for each of the two formats.

**Analysis:** Report descriptive statistics (median, IQR) per dimension per format. Given
the small target n (2–3 raters), no inferential test is pre-registered as confirmatory;
a Wilcoxon signed-rank test may be reported as an exploratory supplement only, clearly
labeled as such.

**Limitations (state explicitly in `docs/M8_RESEARCH_FINDINGS.md`):** small sample size,
no formal power analysis, at least one non-blind rater, single-institution/single-author
context, results are descriptive and exploratory rather than confirmatory of a general
trust/actionability effect.

**Artifacts to commit before any session runs:**
- `data/benchmarks/m8_human_eval_protocol.md` (this section, expanded to a standalone
  document with the exact selected stimulus pairs and recorded comparison count once the frozen
  benchmark/corpus is finalized)
- `data/benchmarks/m8_human_eval_instrument.md` (the rating form as shown to raters)
