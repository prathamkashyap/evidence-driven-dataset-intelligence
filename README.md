# Evidence-Driven Dataset Intelligence and Recommendation System

This repository implements an evidence-driven, local-first dataset intelligence and recommendation system for public machine learning datasets. Rather than treating metadata claims as unquestioned truth or relying on popularity-driven heuristics, the system separates candidate retrieval from empirical evidence verification, explicit uncertainty modeling, task-specific utility estimation, and family-aware recommendation set diversification.

The project adheres to [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md), [docs/RESEARCH_FOUNDATION.md](docs/RESEARCH_FOUNDATION.md), and the repository working agreement in [AGENTS.md](AGENTS.md).

---

## 1. Core Architecture & Pipeline

The pipeline is structured into discrete, isolated stages:

1. **Ingestion & Canonicalization (`src/dataset_intelligence/ingestion/`):**
   - Source adapters ingest metadata from HuggingFace, OpenML, UCI, and Kaggle.
   - Native platform fields are preserved for provenance; canonical records isolate upstream ingestion from downstream ranking interfaces.
2. **Constrained Candidate Retrieval (`src/dataset_intelligence/retrieval/`):**
   - Fast lexical (BM25) retrieval functions as the deployment default, operating in sub-millisecond latency under strict local memory bounds (M0 budget).
   - Dense semantic retrieval (`all-MiniLM-L6-v2`) and Reciprocal Rank Fusion (RRF) hybrid retrieval are benchmarked; dense retrieval is documented as exceeding the 128 MiB constrained budget.
3. **Multi-Source Evidence & Probing (`src/dataset_intelligence/evidence/`, `src/dataset_intelligence/fingerprinting/`):**
   - An immutable evidence ledger models five distinct epistemic states: `unknown`, `single_source_claim`, `observed`, `corroborated`, and `conflicting`.
   - Bounded content probes inspect initial data slices (null rates, slice class distribution, constant column detection) without full-dataset ingestion.
4. **Task-Specific Utility Estimation (`src/dataset_intelligence/utility/`):**
   - Hard gating filters out absolute incompatibilities (e.g., modality clashes, missing target columns) before soft ranking.
   - Soft compatibility terms assess structural constraints, task alignment, and observed quality metrics.
5. **Long-Tail Exploration (`src/dataset_intelligence/exploration/`):**
   - An Exposure Disparity Index audits candidate popularity.
   - Under-observed, high-utility candidates are surfaced to counter catalog popularity bias.
6. **Multi-Objective Ranking & Diversification (`src/dataset_intelligence/ranking/`):**
   - **R1 (Utility-Only Baseline):** Ranks solely by task-compatibility utility.
   - **R2 (Multi-Objective Linear):** Combines task fit, utility, evidence support, and coverage penalties while subtracting risk terms ($S = 0.35 \cdot S_{\text{fit}} + 0.35 \cdot S_{\text{util}} + 0.15 \cdot S_{\text{evid}} + 0.15 \cdot S_{\text{cov}} - 0.15 \cdot S_{\text{risk}}$).
   - **R3 (Diversified Set Selection):** Applies greedy submodular selection with family-aware redundancy penalties to construct non-redundant recommendation sets of target size $k=3$.
7. **Evidence-Augmented Recommendation Cards (`src/dataset_intelligence/ranking/explanation.py`):**
   - Produces structured JSON recommendation cards containing fit rationales, non-fit caveats, evidence support scores, license claim disclosures, and recommendation context.

---

## 2. Milestone Evaluation Matrix (M0–M8)

| Milestone | Scope & Claim | Primary Evaluation Artifacts | Key Result | Boundary / Limitation |
|---|---|---|---|---|
| **M0** | Local compute & access envelope | `configs/m0_compute_budget.json`, `docs/M0_COMPUTE_BUDGET_PLAN.md` | 128 MiB RSS ceiling, 20 s per-task latency; Kaggle metadata-only | Single-machine measurement (macOS arm64); conservative envelope |
| **M1** | Canonical schema & source adapters | `docs/M1_RESULTS.md`, `experiments/m1/` | 10-dataset multi-source development corpus | Metadata-only for Kaggle; no scoring or retrieval |
| **M2** | BM25, dense, hybrid retrieval baselines | `docs/M2_RESULTS.md`, `experiments/m2/` | Recall@1=0.875, Recall@3=1.000; BM25 sub-millisecond | Small dev corpus saturates; dense MiniLM exceeds M0 memory budget |
| **M3** | Multi-facet evidence ledger | `docs/M3_RESULTS.md`, `experiments/m3/` | 107 ledger entries; genuine license URI conflict detected | 84.9% unresolved due to single-source dev records |
| **M4** | Bounded dataset fingerprinting | `docs/M4_RESULTS.md`, `experiments/m4/` | 7 sample-accessible datasets profiled; slice bias flagged | Image binary files not downloaded; sample bounds apply |
| **M5** | Task utility estimation & ablations | `docs/M5_RESULTS.md`, `experiments/m5/` | Baseline C (Meta+M3+M4) Spearman $\rho=0.9667$ vs A=0.9576; 75% hard-gated | Equal-weight baseline; development corpus only |
| **M6** | Popularity audit & long-tail exploration | `docs/M6_RESULTS.md`, `experiments/m6/` | Exploration pool raised mean utility on `q_tabular_wine` (+25.2%) | Dev corpus scope; 3 of 4 queries showed 0 under-exposed additions |
| **M7** | Multi-objective ranking & diversification | `docs/M7_RESULTS.md`, `experiments/m7/` | R3 eliminated duplicate mirror family redundancy (UCI+OpenML Iris) | 10 datasets × 4 dev tasks; H2 reordering not demonstrated on dev corpus |
| **M8 Benchmark** | Frozen offline benchmark (24 datasets × 8 tasks) | `docs/M8_EVALUATION.md`, `experiments/m8/results/m8_summary.json` | 0 crashes / 10 trials; sensitivity Jaccard=1.0 at $\pm 20\%$; peak RSS 33.11 MiB; 327 ms runtime | H1 N/A (no mirror pairs in top-$k$); H4 verified architecturally |
| **M8 Human Pilot** | Exploratory format comparison pilot (N=3) | `docs/M8_RESEARCH_FINDINGS.md`, `experiments/m8/human_eval/` | Format B rated higher on Trust (+1.81), Understanding (+3.19), Actionability (+3.00) | Documented exploratory pilot; N=3; order confound noted; no p-values |

---

## 3. Scope, Constraints & Interface Disclosures

- **Input Interface:** The evaluated pipeline is driven by structured `TaskSpecification` fixtures (see `tests/fixtures/` and `data/benchmarks/m8_ground_truth_labels.json`). No natural-language requirement parser is implemented in this evaluated release.
- **Output Interface:** Recommendations and explanations are generated as structured JSON data structures (`RecommendationCard` and `RecommendationSet`). There is no interactive CLI wrapper (`cli.py`).
- **Scoring Weights:** Ranking weights ($w_{\text{fit}}=0.35, w_{\text{util}}=0.35, w_{\text{evid}}=0.15, w_{\text{cov}}=0.15, w_{\text{risk}}=0.15$) and $\lambda_{\text{div}}=0.20$ are fixed heuristic weights; sensitivity analysis confirms recommendation stability at $\pm 20\%$ perturbation, but the weights are not learned or asserted as optimal.
- **Popularity Neutrality:** Popularity metrics are recorded for context and exposure audits, but are strictly excluded from candidate scoring formulas.
- **Internal Consistency Diagnostics:** Brier score (0.259) and ECE (0.429) recorded in M8 represent internal consistency audits against task-compatibility reference levels, not independent probabilistic calibration.
- **Human Evaluation Pilot:** The M8 human evaluation was conducted as a documented exploratory pilot with $N=3$ independent human participants across 7 comparison pairs. All primary results reflect first-exposure ratings. No inferential statistics (p-values) or claims of generalizability are made.

---

## 4. Environment & Reproducibility

### Setup

The project was evaluated and verified on **macOS arm64 (Apple Silicon)** with **Python 3.14.6**. Python 3.10+ is supported.

```bash
# 1. Create and activate a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install exact pinned dependencies
pip install -r requirements.txt
```

### Running Tests

The test suite contains 208 unit and integration tests covering all pipeline modules and benchmark contracts:

```bash
python3 -m unittest discover -s tests -v
```

### Executing Evaluation Scripts

```bash
# Run frozen M8 offline benchmark (zero network egress)
python3 scripts/run_m8_benchmark.py

# Run M8 human evaluation analysis (generates summary JSON and plots)
python3 scripts/analyze_m8_human_eval.py
```

---

## 5. Repository Documentation Index

- **Core Specifications:**
  - [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) — Comprehensive technical specification
  - [docs/RESEARCH_FOUNDATION.md](docs/RESEARCH_FOUNDATION.md) — Research foundation, problem framing, and claims
  - [AGENTS.md](AGENTS.md) — Repository engineering rules and working agreements
- **Milestone Results & Protocols:**
  - [docs/M0_COMPUTE_BUDGET_PLAN.md](docs/M0_COMPUTE_BUDGET_PLAN.md) — M0 compute budget
  - [docs/M1_RESULTS.md](docs/M1_RESULTS.md) — M1 canonical corpus
  - [docs/M2_RESULTS.md](docs/M2_RESULTS.md) — M2 retrieval baselines
  - [docs/M3_RESULTS.md](docs/M3_RESULTS.md) — M3 evidence ledger
  - [docs/M4_RESULTS.md](docs/M4_RESULTS.md) — M4 fingerprinting
  - [docs/M5_RESULTS.md](docs/M5_RESULTS.md) — M5 utility estimation
  - [docs/M6_RESULTS.md](docs/M6_RESULTS.md) — M6 popularity & exploration
  - [docs/M7_RESULTS.md](docs/M7_RESULTS.md) — M7 ranking & diversification
  - [docs/M8_EVALUATION.md](docs/M8_EVALUATION.md) — M8 evaluation protocol *(Note: this document's own status header predates execution and is preserved for hash-contract integrity; see M8_RESEARCH_FINDINGS.md for the completed, frozen results)*
  - [docs/M8_RESEARCH_FINDINGS.md](docs/M8_RESEARCH_FINDINGS.md) — M8 human evaluation findings
