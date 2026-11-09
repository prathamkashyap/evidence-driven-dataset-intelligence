# Evidence-Driven Dataset Intelligence and Recommendation System

Research prototype for evidence-aware, local-first dataset recommendation, combining provenance tracking, hard compatibility gates, bounded dataset inspection, and diversity-aware selection.

[Explore the interactive research companion](https://evidence-driven-research-companion.vercel.app/) · [Read the approved paper](https://github.com/prathamkashyap/evidence-driven-dataset-intelligence/blob/main/paper/final_submission/main.pdf) · [Explore the frozen M8 results](experiments/m8/results/m8_summary.json) · [Phase I reporting corrections](docs/PHASE1_REPORTING_CORRECTIONS.md)

This repository implements an evidence-driven, local-first dataset intelligence and recommendation system for public machine learning datasets. Rather than treating metadata claims as unquestioned truth or relying on popularity-driven heuristics, the system separates candidate retrieval from empirical evidence verification, explicit uncertainty modeling, task-specific utility estimation, and family-aware recommendation set diversification.

The project adheres to [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md), [docs/RESEARCH_FOUNDATION.md](docs/RESEARCH_FOUNDATION.md), and the repository working agreement in [AGENTS.md](AGENTS.md).

**Current status:** M0–M8 evaluation and M9 documentation consolidation are complete. The M8 human evaluation is an exploratory N=3 pilot, not a confirmatory or generalizable study. The final Phase I report and the six-author-approved final-submission manuscript are committed on `main`. This repository is a research artifact, not a production system.

**Software licensing:** Project-authored software is licensed under the [MIT License](LICENSE). The license scope and exclusions for research documents, data, and third-party material are described in [LICENSES.md](LICENSES.md).

---

## 1. Project Overview

A local-first pipeline ingests public dataset metadata from four sources, checks claims against bounded empirical evidence, estimates task-specific utility under hard compatibility constraints, and emits small, traceable recommendation sets. The recorded M8 evaluation harness took 327.49 ms for the eight-task suite, with a process-lifetime peak RSS of 33.11 MiB. The 20 s per-task design budget and the suite timer measure different scopes. M8 was configured to use frozen local inputs. The socket-blocking test covers input loading, and whole-run network telemetry is unavailable.

M2 is a separate retrieval study using MiniLM. Its shared BM25, dense, and hybrid process reached 453.22 MiB peak RSS, about 3.54× the 128 MiB design ceiling. Individual backend peaks are unavailable. Each query used the fixed BM25 → dense → hybrid sequence with one call per method and query, so the timings do not establish a controlled dense-versus-hybrid speed comparison. M8's dense and hybrid ablations instead use a lightweight test-vector encoder on the fixed candidate pool.

**Phase II design (proposed):** [Independent relevance benchmark and evaluation protocol](docs/phase2/README.md). Collection, annotation, model implementation, and Phase II evaluation have not started.

## 2. Research Problem

Public dataset catalogs mix verifiable measurements with publisher assertions, and ranking systems frequently optimize for popularity rather than task fit. This project asks whether a local, offline pipeline can:

1. Separate metadata **claims** from directly **observed** evidence, and model missing or conflicting information explicitly instead of defaulting to it.
2. Estimate task-specific dataset utility under hard compatibility constraints and report the measured resource scope of each study against the M0 design context (128 MiB process memory, 20 s per task).
3. Produce small, non-redundant, evidence-grounded recommendation sets whose behavior is measured against frozen benchmark hypotheses rather than asserted.

## 3. Key Principles

- **Two-layer evidence states.** Individual observations and cross-evidence resolution are modeled as two related state layers (Section 4), never collapsed into one flat epistemic score.
- **Missing information is explicit.** `unknown`, `unsupported`, and `failed` are first-class states, distinct from negative findings.
- **Claims are not facts.** License and availability metadata are recorded as claims with provenance, not as legal advice or conclusive facts.
- **Popularity is context only.** Popularity counters are excluded from candidate scoring and ranking formulas; this is architecturally enforced and checked as hypothesis H4 in M8.
- **Bounded inspection.** Sampling and probing use explicit limits. Runtime and memory measurements describe the recorded study processes.
- **Frozen local inputs.** M8 records its application seed and structured JSON/JSONL outputs. The test-vector encoder uses Python token hashing, and the historical `PYTHONHASHSEED` was not recorded. Exact replay of hash-dependent dense and hybrid orderings is unestablished.

## 4. Actual Architecture

The implemented pipeline (all modules under `src/dataset_intelligence/`) is:

1. **TaskSpecification fixtures** — structured, versioned task specifications (`utility/specification.py`) instantiated from configuration fixtures (`configs/m8_corpus_preparation.json`, `tests/fixtures/`). There is no natural-language or LLM requirement parser in the current scope.
2. **Canonical ingestion (M1, `ingestion/`)** — source adapters for HuggingFace, OpenML, UCI, and Kaggle. Native platform fields are preserved as provenance; canonical records isolate upstream sources from downstream ranking interfaces.
3. **Evidence ledger (M3, `evidence/`)** — an immutable ledger with two related state layers:
   - **Observation states** (per observation): `observed`, `single_source_claim`, `unsupported`, `failed`, `unknown`
   - **Resolution states** (cross-evidence): `unresolved`, `corroborated`, `conflicting`, `unknown`

     The `ProvisionalResolver` records agreement or disagreement among observations without independently verifying source independence. M8 ranking derives evidence-support features from precomputed utility-component states and fingerprints. `conflicting` is a resolution state.
4. **Bounded fingerprinting (M4, `fingerprinting/`)** — descriptive slice diagnostics (null rates, class distribution, constant columns) over samples capped at 32 records / 64 MiB, without full-dataset ingestion. Fingerprint output is evidence, not a utility score.
5. **Utility estimation & hard gates (M5, `utility/`)** — `check_hard_gates()` implements exactly three hard constraints before any soft scoring:
   - **Modality clash** — task requires a modality the dataset is confirmed not to have.
   - **Prohibited license** — the dataset's license claim matches a prohibited-license constraint from the task specification.
   - **Public access required on a gated source** — task requires anonymous public access but the source (Kaggle) requires credentials and gated access is not allowed.

     Soft compatibility terms then score task, modality, target, structural, quality, governance, and access facets. Hard-gated candidates receive composite utility 0 and are excluded before ranking.
6. **Popularity profiling & exploration analysis (M6, `exploration/`)** — exposure-disparity audits over popularity profiles, plus an offline exploration-pool simulation (`scripts/run_m6_exploration.py`). **Implementation boundary:** exploration pools are produced by the M6 analysis and are *not* automatically routed into M7 ranking. What M6 does feed downstream is consumed where actually used: popularity profiles and the strict hidden-gem predicate are consumed by post-selection recommendation role assignment (`ranking/roles.py`).
7. **RecommendationEngine (M7, `ranking/`)** — orchestrates the recommendation path:
   hard gating → candidate signals → multi-objective scoring → diversification → post-selection roles → `RecommendationCard`s.
   - **R1:** utility-only baseline.
   - **R2:** linear multi-objective score with fixed heuristic weights (fit 0.35, utility 0.35, evidence 0.15, coverage 0.15, risk 0.15).
   - **R3:** family-aware greedy diversification. The selector (`diversification.py`) is a deterministic greedy loop that strictly excludes same-family mirrors of already-accepted datasets (`detect_family_redundancy`) and picks the candidate maximizing `intrinsic score + λ_div × min pairwise attribute distance` (λ_div = 0.20) with deterministic tie-breaking. It is described as **family-aware greedy diversification**; no formal submodularity property is claimed.
8. **Evaluation harness (M8, `evaluation/`)** — fixed-pool benchmark that loads frozen corpus, evidence, fingerprint, and utility records. Its main recommendation path receives the pool directly. Separate ablation rungs compare BM25, dense test-vector ordering, and reciprocal rank fusion (RRF) of the two within that pool.

## 5. Implemented Components & Current Scope

**Implemented:**

- Structured `TaskSpecification` fixtures driven by configuration files
- Canonical multi-source ingestion with provenance preservation (HuggingFace, OpenML, UCI, Kaggle)
- BM25 constrained retrieval (M2 benchmark default; M8 ablation component)
- Deterministic two-layer evidence-state handling with an immutable ledger
- Bounded fingerprint diagnostics (sample-capped, descriptive only)
- Heuristic task-utility estimation with the three hard gates above
- Multi-objective ranking (R1/R2/R3) with family-aware greedy diversification and post-selection roles
- Structured JSON/JSONL output (`RecommendationCard`, `RecommendationSet`)
- Offline evaluation harness with hash-checked frozen inputs and archived outputs

**Current scope exclusions / deferred extensions** (not failures; simply not part of this implementation):

- Natural-language requirement parser / LLM task parser
- Formal Dempster–Shafer evidence fusion
- Cleanlab-style label-error analysis
- Learned learning-to-rank (LTR) models or learned/optimized ranking weights
- A trained bi-encoder (e.g. DataFinder) as the default retrieval backend; dense MiniLM is optional, and the shared M2 retrieval-benchmark process exceeded the 128 MiB ceiling without isolating memory to one backend
- Interactive CLI wrapper

## 6. Repository Structure

```
src/dataset_intelligence/   # ingestion, retrieval, evidence, fingerprinting,
                            # utility, exploration, ranking, evaluation, m0
configs/                    # versioned experiment configurations (M0–M8)
scripts/                    # per-milestone runners and analysis scripts
experiments/                # frozen result artifacts (m0–m8)
data/benchmarks/            # hash-manifested M8 benchmark inputs
docs/                       # specifications, milestone results, evidence maps
final_report/               # committed final Phase I report (PDF + DOCX)
paper/final_submission/     # approved manuscript, source, and build inputs
paper/main.tex              # retained historical manuscript source; not the approved submission
tests/                      # unit + integration tests and fixtures
indexes/                    # build-time retrieval indexes
```

## 7. Installation & Requirements

The project was evaluated on **macOS arm64 (Apple Silicon)** with **Python 3.14.6**. Python 3.10+ is supported (`docs/PROJECT_SPEC.md`).

```bash
# 1. Create and activate a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install exact pinned dependencies
pip install -r requirements.txt
```

## 8. Running Tests

The standard test command discovers all 208 unit and integration tests:

```bash
python3 -m unittest discover -s tests -v
```

With the Python requirements and Node.js installed, a clean clone runs 175 tests and reports 33 tests that need ignored M8 human-evaluation captures, derived datasets, analysis output, or the locally generated Google Forms specification as **skipped with a reason**. Skipped tests are not counted as passing. If Node.js is unavailable, its JavaScript syntax check is also visibly skipped. When the required local files are available, run the research-data-dependent tests directly:

```bash
python3 -m unittest discover -s tests -p 'test_m8_human_eval_*.py' -v
python3 -m unittest discover -s tests -p 'test_m8_google_forms.py' -v
```

Those optional tests require `data/raw/m8_initial_collection/rater*_form.csv`, `data/benchmarks/m8_human_eval_primary.csv`, `data/benchmarks/m8_human_eval_repeat_exposure.csv`, `data/benchmarks/m8_human_eval_responses.csv`, `data/benchmarks/m8_human_eval_responses_long.csv`, `data/benchmarks/m8_human_eval_raw_collection_manifest.json`, `data/benchmarks/m8_human_eval_session_manifest.json`, `experiments/m8/results/m8_human_eval_summary.json`, and `data/benchmarks/m8_google_forms_specification.md`. These ignored inputs and generated files are not included in a fresh clone.

## 9. Checking the Frozen Benchmark

```bash
# Offline input/label integrity check only (no outputs written)
python3 scripts/run_m8_benchmark.py --check-only

# M8 human-evaluation analysis (regenerates derived summary JSON and plots)
python3 scripts/analyze_m8_human_eval.py
```

The human-evaluation analysis command requires the local primary and repeat-exposure CSVs listed in Section 8. It writes a derived summary and plots to ignored paths; it does not modify the frozen, tracked results file.

## 10. M0–M8 Evaluation Summary

The table summarizes the committed experiment artifacts and M0 design limits. See the [Phase I reporting corrections](docs/PHASE1_REPORTING_CORRECTIONS.md) for measurement scope and limits.

| Milestone | Scope | Key measured result | Primary artifacts |
|---|---|---|---|
| **M0** | Local compute & access envelope | 128 MiB process ceiling, 20 s per-task ceiling; Kaggle metadata-only route; 32-record / 64 MiB sample cap | `configs/m0_compute_budget.json`, `docs/M0_COMPUTE_BUDGET_PLAN.md`, `experiments/m0/` |
| **M1** | Canonical schema & source adapters | 10-record multi-source development corpus (HF, OpenML, UCI, Kaggle) | `docs/M1_RESULTS.md`, `experiments/m1/` |
| **M2** | BM25 / MiniLM / hybrid retrieval on four development queries | BM25 Recall@1 = 0.875, Recall@3 = 1.000, mean query call ≈ 0.06 ms. Shared process peak RSS = 453.22 MiB. Each query was measured once in fixed method order. | `docs/M2_RESULTS.md`, `experiments/m2/results/benchmark.json` |
| **M3** | Multi-facet evidence ledger | 107 ledger entries; 67 single-source claims (62.6%); 90/106 unresolved (84.9%); 1 resolver-classified license text/URI mismatch (0 corroborated) | `docs/M3_RESULTS.md`, `experiments/m3/` |
| **M4** | Bounded dataset fingerprinting | 9.31 ms, 24.20 MiB peak RSS; 7 sample-accessible datasets; Rotten Tomatoes 32/32 single-class slice flagged as bounded-sample observation | `docs/M4_RESULTS.md`, `experiments/m4/` |
| **M5** | Task utility estimation on four tasks and ten records | 75% of task–dataset evaluations hard-gated. Historical nDCG used corpus order, and correlation broke ties by dataset identifier. The recorded metrics do not establish comparative ranking effectiveness. | `docs/M5_RESULTS.md`, `experiments/m5/` |
| **M6** | Popularity audit & exploration analysis | `q_tabular_wine` mean pool utility 0.5476 → 0.6857 (+25.2%); 0 strict hidden gems across 4 audited queries | `docs/M6_RESULTS.md`, `experiments/m6/` |
| **M7** | Multi-objective ranking & diversification | Same-family redundancy R1 = 1 → R3 = 0; mean set utility 0.8506 → 0.8536; on `task_tabular_iris` specifically, 0.8809 → 0.8928 | `docs/M7_RESULTS.md`, `experiments/m7/` |
| **M8 benchmark** | Frozen offline benchmark, 24 datasets × 8 tasks = 192 evaluations | 327.49 ms evaluation-harness interval and 33.11 MiB process peak RSS. 0 crashes in 10 fixture trials. H1 N/A under its R1 trigger, H2 exploratory, H3 observed utility delta 0.000, H4 architectural invariant, H5 20/20 roles met grounding preconditions. Brier = 0.259314 and ECE = 0.428503 are internal consistency diagnostics. | [Frozen M8 summary](experiments/m8/results/m8_summary.json), [historical protocol](docs/M8_EVALUATION.md) |
| **M8 human pilot** | Exploratory format comparison, three participants and seven paired comparisons per participant | Descriptive B − A mean ratings: Trust +1.81, Understanding +3.19, Actionability +3.00. Presentation order and author participation limit interpretation. | [Recorded pilot findings](docs/M8_RESEARCH_FINDINGS.md) |

Robustness suites: 4 corruption suites (fixtures: `data/benchmarks/m8_corruption_fixtures.json`), 10 trials total.

## 11. Limitations, Disclosures & Current Scope

- **Input interface:** the evaluated pipeline is driven by structured `TaskSpecification` fixtures. No natural-language requirement parser is implemented.
- **Output interface:** recommendations and explanations are emitted as structured JSON data structures. There is no interactive CLI.
- **Scoring and diversity weights.** R2/R3 use fixed heuristic scoring weights (0.35 / 0.35 / 0.15 / 0.15 / 0.15). The positive-weight (±20%) and risk-weight perturbations did not reach the recommendation scorer, so their unchanged outputs do not establish scoring-weight robustness. The separate diversity-weight sweep varied λ_div at the selector, whose default is 0.20.
- **Popularity neutrality:** popularity metrics are recorded for context and exposure audits, but are excluded from scoring formulas (architecturally enforced; checked as H4).
- **Reference labels and heuristic utility.** M5 and M8 reference judgments were authored within the project. M8 ablations summarize internal heuristic utility. Brier (0.259314) and ECE (0.428503) describe agreement with the project rubric and do not establish independent relevance or probability calibration.
- **Human evaluation pilot.** The primary N = 3 ratings are first-exposure observations. All participants used the same schedule (five B-first and two A-first pairs), one was a project author, and repeat-exposure linkage is uncertain for two participants. The results are descriptive.
- **Development-corpus scope (M1–M7):** milestone results on the 10-dataset development corpus are scoped observations under the tested conditions, not population-level findings.
- **Historical protocol.** The status header in [M8 evaluation](docs/M8_EVALUATION.md) predates execution. Its exact bytes are registered in the [benchmark manifest](data/benchmarks/m8_benchmark_manifest.json). See the [frozen benchmark summary](experiments/m8/results/m8_summary.json) and [recorded pilot findings](docs/M8_RESEARCH_FINDINGS.md) for completed results.
- **Human-evaluation disclosure and reproducibility:** the consent-approved, tracked `experiments/m8/human_eval/m8_human_eval_results.json` contains per-participant summary statistics and repeat-exposure metadata. Raw form exports, row-level response and analysis datasets, the derived `experiments/m8/results/m8_human_eval_summary.json`, and selected pilot plots remain ignored local files. The ordinary test command reports the dependent tests as skipped when their local inputs are absent; it does not count those tests as passed.

## 12. Documentation Index

- **Core specifications:**
  - [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) — comprehensive technical specification
  - [docs/RESEARCH_FOUNDATION.md](docs/RESEARCH_FOUNDATION.md) — research foundation, problem framing, claims
  - [AGENTS.md](AGENTS.md) — repository engineering rules and working agreements
- **Milestone results & protocols:**
  - [Phase I reporting corrections](docs/PHASE1_REPORTING_CORRECTIONS.md) — corrected interpretations and source evidence for the frozen studies
  - [docs/M0_COMPUTE_BUDGET_PLAN.md](docs/M0_COMPUTE_BUDGET_PLAN.md) — M0 compute budget
  - [docs/M1_RESULTS.md](docs/M1_RESULTS.md) — M1 canonical corpus
  - [docs/M2_RESULTS.md](docs/M2_RESULTS.md) — M2 retrieval baselines
  - [docs/M3_RESULTS.md](docs/M3_RESULTS.md) — M3 evidence ledger (protocol: [docs/M3_EVIDENCE.md](docs/M3_EVIDENCE.md))
  - [docs/M4_RESULTS.md](docs/M4_RESULTS.md) — M4 fingerprinting
  - [docs/M5_RESULTS.md](docs/M5_RESULTS.md) — M5 utility estimation
  - [docs/M6_RESULTS.md](docs/M6_RESULTS.md) — M6 popularity & exploration
  - [docs/M7_RESULTS.md](docs/M7_RESULTS.md) — M7 ranking & diversification
  - [docs/M8_EVALUATION.md](docs/M8_EVALUATION.md) — M8 evaluation protocol *(status header preserved for hash-contract integrity; see Section 11)*
  - [docs/M8_RESEARCH_FINDINGS.md](docs/M8_RESEARCH_FINDINGS.md) — M8 benchmark + human-evaluation findings

## 13. Research & Report Artifacts

- **Final Phase I report:** [PDF](final_report/DSN4091_Capstone_Phase-I_Final_Report.pdf) · [DOCX](final_report/DSN4091_Capstone_Phase-I_Final_Report.docx)
- **Approved manuscript:** [package and build guide](paper/final_submission/README.md) · [approved PDF](paper/final_submission/main.pdf) · [LaTeX source](paper/final_submission/main.tex)
- [docs/FINAL_REPORT_EVIDENCE_MAP.md](docs/FINAL_REPORT_EVIDENCE_MAP.md) — claim-to-artifact traceability for the delivered report
- [docs/FINAL_VIVA_EVIDENCE_MAP.md](docs/FINAL_VIVA_EVIDENCE_MAP.md) — viva/defense reference
- [paper/README.md](paper/README.md) — distinguishes the approved manuscript from the retained historical source
- [docs/v1/](docs/v1/), [docs/v2/](docs/v2/), and [docs/v3/](docs/v3/) — versioned proposal history; not current report drafts
- Raw human-study captures and generated analysis datasets are intentionally excluded from Git. The consent-approved machine-readable result summary is tracked at `experiments/m8/human_eval/m8_human_eval_results.json`; see Section 11 and [M8 findings](docs/M8_RESEARCH_FINDINGS.md) for scope and limitations.
