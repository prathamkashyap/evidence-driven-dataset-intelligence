# Evidence-Driven Dataset Intelligence and Recommendation System

Research prototype for evidence-aware, local-first dataset recommendation, combining provenance tracking, hard compatibility gates, bounded dataset inspection, and diversity-aware selection.

[Explore the interactive research companion](https://evidence-driven-research-companion.vercel.app/) · [Read the approved paper](https://github.com/prathamkashyap/evidence-driven-dataset-intelligence/blob/main/paper/final_submission/main.pdf) · [Explore the M8 evaluation](https://github.com/prathamkashyap/evidence-driven-dataset-intelligence/blob/main/docs/M8_EVALUATION.md)

This repository implements an evidence-driven, local-first dataset intelligence and recommendation system for public machine learning datasets. Rather than treating metadata claims as unquestioned truth or relying on popularity-driven heuristics, the system separates candidate retrieval from empirical evidence verification, explicit uncertainty modeling, task-specific utility estimation, and family-aware recommendation set diversification.

The project adheres to [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md), [docs/RESEARCH_FOUNDATION.md](docs/RESEARCH_FOUNDATION.md), and the repository working agreement in [AGENTS.md](AGENTS.md).

**Current status:** M0–M8 evaluation and M9 documentation consolidation are complete. The M8 human evaluation is an exploratory N=3 pilot, not a confirmatory or generalizable study. The final Phase I report and the six-author-approved final-submission manuscript are committed on `main`. This repository is a research artifact, not a production system.

---

## 1. Project Overview

A local-first pipeline ingests public dataset metadata from four sources, verifies claims against bounded empirical evidence, estimates task-specific utility under hard compatibility constraints, and emits small, traceable recommendation sets. The frozen M8 offline recommendation path used 33.11 MiB peak RSS and 327.49 ms wall time with verified zero network egress, within the M0 design ceilings of 128 MiB and 20 s per task. Retrieval experiments are separate: the shared M2 benchmark process (BM25, dense MiniLM, and hybrid) reached 453.22 MiB peak RSS (3.54× the memory ceiling), and memory was not isolated to one backend. Optional dense MiniLM is not part of the constrained M8 path. Results are scoped to their recorded experiments. The project is evaluated through frozen milestones M0–M8, including an exploratory N = 3 human pilot.

**Phase II design (proposed):** [Independent relevance benchmark and evaluation protocol](docs/phase2/README.md). Collection, annotation, model implementation, and Phase II evaluation have not started.

## 2. Research Problem

Public dataset catalogs mix verifiable measurements with publisher assertions, and ranking systems frequently optimize for popularity rather than task fit. This project asks whether a local, offline pipeline can:

1. Separate metadata **claims** from directly **observed** evidence, and model missing or conflicting information explicitly instead of defaulting to it.
2. Estimate task-specific dataset utility under hard compatibility constraints and evaluate the frozen M8 offline path against the M0 design ceilings (128 MiB process memory, 20 s per task), while reporting optional components that exceed those limits separately.
3. Produce small, non-redundant, evidence-grounded recommendation sets whose behavior is measured against frozen benchmark hypotheses rather than asserted.

## 3. Key Principles

- **Two-layer evidence states.** Individual observations and cross-evidence resolution are modeled as two related state layers (Section 4), never collapsed into one flat epistemic score.
- **Missing information is explicit.** `unknown`, `unsupported`, and `failed` are first-class states, distinct from negative findings.
- **Claims are not facts.** License and availability metadata are recorded as claims with provenance, not as legal advice or conclusive facts.
- **Popularity is context only.** Popularity counters are excluded from candidate scoring and ranking formulas; this is architecturally enforced and checked as hypothesis H4 in M8.
- **Bounded everything.** Samples, probes, runtimes, and memory are capped; results are scoped observations on the tested corpora, not full-dataset or web-scale facts.
- **Deterministic and offline.** Fixed seeds, cached inputs, no network egress during evaluation, structured JSON/JSONL outputs.

## 4. Actual Architecture

The implemented pipeline (all modules under `src/dataset_intelligence/`) is:

1. **TaskSpecification fixtures** — structured, versioned task specifications (`utility/specification.py`) instantiated from configuration fixtures (`configs/m8_corpus_preparation.json`, `tests/fixtures/`). There is no natural-language or LLM requirement parser in the current scope.
2. **Canonical ingestion (M1, `ingestion/`)** — source adapters for HuggingFace, OpenML, UCI, and Kaggle. Native platform fields are preserved as provenance; canonical records isolate upstream sources from downstream ranking interfaces.
3. **Evidence ledger (M3, `evidence/`)** — an immutable ledger with two related state layers:
   - **Observation states** (per observation): `observed`, `single_source_claim`, `unsupported`, `failed`, `unknown`
   - **Resolution states** (cross-evidence): `unresolved`, `corroborated`, `conflicting`, `unknown`

     The `ProvisionalResolver` computes resolution states for the ledger record itself; downstream utility and ranking consume the underlying ledger observation states (e.g. `conflicting` observations), not a resolver score.
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
8. **Evaluation harness (M8, `evaluation/`)** — frozen offline benchmark that feeds the frozen corpus **directly** to the `RecommendationEngine`. M2 retrieval (BM25, dense MiniLM, hybrid RRF) remains implemented and benchmarked as an evaluation/ablation component (`evaluation/ablations.py`); retrieval methods are not on the main M8 recommendation path.

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
- Reproducible offline evaluation harness with zero network egress

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

## 9. Running the Benchmark

```bash
# Frozen M8 offline benchmark (zero network egress)
python3 scripts/run_m8_benchmark.py

# Offline input/label integrity check only (no outputs written)
python3 scripts/run_m8_benchmark.py --check-only

# M8 human-evaluation analysis (regenerates derived summary JSON and plots)
python3 scripts/analyze_m8_human_eval.py
```

The human-evaluation analysis command requires the local primary and repeat-exposure CSVs listed in Section 8. It writes a derived summary and plots to ignored paths; it does not modify the frozen, tracked results file.

## 10. M0–M8 Evaluation Summary

All values below are measured results from the committed experiment artifacts; full tables and boundaries live in the linked documents.

| Milestone | Scope | Key measured result | Primary artifacts |
|---|---|---|---|
| **M0** | Local compute & access envelope | 128 MiB process ceiling, 20 s per-task ceiling; Kaggle metadata-only route; 32-record / 64 MiB sample cap | `configs/m0_compute_budget.json`, `docs/M0_COMPUTE_BUDGET_PLAN.md`, `experiments/m0/` |
| **M1** | Canonical schema & source adapters | 10-record multi-source development corpus (HF, OpenML, UCI, Kaggle) | `docs/M1_RESULTS.md`, `experiments/m1/` |
| **M2** | BM25 / dense / hybrid retrieval baselines | BM25 Recall@1 = 0.875, Recall@3 = 1.000, latency ≈ 0.06 ms; shared retrieval-benchmark process peak RSS = 453.22 MiB (3.54× the 128 MiB ceiling; not isolated to one backend) | `docs/M2_RESULTS.md`, `experiments/m2/results/benchmark.json` |
| **M3** | Multi-facet evidence ledger | 107 ledger entries; 67 single-source claims (62.6%); 90/106 unresolved (84.9%); 1 resolver-classified license text/URI mismatch (0 corroborated) | `docs/M3_RESULTS.md`, `experiments/m3/` |
| **M4** | Bounded dataset fingerprinting | 9.31 ms, 24.20 MiB peak RSS; 7 sample-accessible datasets; Rotten Tomatoes 32/32 single-class slice flagged as bounded-sample observation | `docs/M4_RESULTS.md`, `experiments/m4/` |
| **M5** | Task utility estimation & ablations | Spearman ρ (A/B/C) = 0.9576 / 0.9576 / 0.9667 (+0.0091 from evidence + fingerprints); 75% of evaluations hard-gated | `docs/M5_RESULTS.md`, `experiments/m5/` |
| **M6** | Popularity audit & exploration analysis | `q_tabular_wine` mean pool utility 0.5476 → 0.6857 (+25.2%); 0 strict hidden gems across 4 audited queries | `docs/M6_RESULTS.md`, `experiments/m6/` |
| **M7** | Multi-objective ranking & diversification | Same-family redundancy R1 = 1 → R3 = 0; mean set utility 0.8506 → 0.8536; on `task_tabular_iris` specifically, 0.8809 → 0.8928 | `docs/M7_RESULTS.md`, `experiments/m7/` |
| **M8 benchmark** | Frozen offline benchmark, 24 datasets × 8 tasks = 192 evaluations | 327.49 ms wall clock, 33.11 MiB peak RSS, zero network egress; 0 crashes / 10 robustness trials; mean Jaccard = 1.0 and mean Kendall τ = 1.0 under ±20% weight perturbation; H1 N/A (no same-family redundancy under R1), H2 exploratory, H3 observed utility delta 0.000, H4 architectural invariant, H5 20/20 roles grounded; Brier = 0.259314, ECE = 0.428503 (internal consistency audit) | `docs/M8_EVALUATION.md`, `experiments/m8/results/m8_summary.json` |
| **M8 human pilot** | Exploratory format-comparison pilot | N = 3 participants, 7 comparisons; Format B − Format A: Trust +1.81, Understanding +3.19, Actionability +3.00 (descriptive, exploratory only) | [`docs/M8_RESEARCH_FINDINGS.md`](docs/M8_RESEARCH_FINDINGS.md); consent-approved participant-level summaries and repeat-exposure metadata in [`experiments/m8/human_eval/m8_human_eval_results.json`](experiments/m8/human_eval/m8_human_eval_results.json); raw captures and derived analysis files are local-only |

Robustness suites: 4 corruption suites (fixtures: `data/benchmarks/m8_corruption_fixtures.json`), 10 trials total.

## 11. Limitations, Disclosures & Current Scope

- **Input interface:** the evaluated pipeline is driven by structured `TaskSpecification` fixtures. No natural-language requirement parser is implemented.
- **Output interface:** recommendations and explanations are emitted as structured JSON data structures. There is no interactive CLI.
- **Scoring weights:** ranking weights (0.35 / 0.35 / 0.15 / 0.15 / 0.15) and λ_div = 0.20 are fixed heuristic values; they are not learned and are not asserted as best-possible. Sensitivity analysis measured recommendation stability at ±20% perturbation (mean Jaccard = 1.0 under the tested conditions).
- **Popularity neutrality:** popularity metrics are recorded for context and exposure audits, but are excluded from scoring formulas (architecturally enforced; checked as H4).
- **Consistency metrics:** Brier (0.259314) and ECE (0.428503) in M8 are internal consistency audits against task-compatibility reference levels — not independent probabilistic calibration, and not claims that the scores are true probabilities.
- **Human evaluation pilot:** conducted as a documented exploratory pilot with N = 3 across 7 comparison pairs; all primary results are first-exposure descriptive ratings; an order confound is documented; no inferential statistics or generalizability claims are made.
- **Development-corpus scope (M1–M7):** milestone results on the 10-dataset development corpus are scoped observations under the tested conditions, not population-level findings.
- **Known documentation exception:** the status header of `docs/M8_EVALUATION.md` predates execution and is intentionally preserved for hash-contract integrity (`data/benchmarks/m8_benchmark_manifest.json`). See `docs/M8_RESEARCH_FINDINGS.md` for the completed, frozen results.
- **Human-evaluation disclosure and reproducibility:** the consent-approved, tracked `experiments/m8/human_eval/m8_human_eval_results.json` contains per-participant summary statistics and repeat-exposure metadata. Raw form exports, row-level response and analysis datasets, the derived `experiments/m8/results/m8_human_eval_summary.json`, and selected pilot plots remain ignored local files. The ordinary test command reports the dependent tests as skipped when their local inputs are absent; it does not count those tests as passed.

## 12. Documentation Index

- **Core specifications:**
  - [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) — comprehensive technical specification
  - [docs/RESEARCH_FOUNDATION.md](docs/RESEARCH_FOUNDATION.md) — research foundation, problem framing, claims
  - [AGENTS.md](AGENTS.md) — repository engineering rules and working agreements
- **Milestone results & protocols:**
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
