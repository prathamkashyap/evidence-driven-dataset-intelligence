# Final Report Evidence Map: Evidence-Driven Dataset Intelligence and Recommendation System

**Document Role:** Master Evidence Architecture & Source Register for Final Capstone Project 1 Report\
**Authoritative Commit Baseline:** `77120e4` (M9 Consolidated Freeze)\
**Evaluation Baseline:** M0–M8 Complete, 208/208 Tests Passing; M9 Consolidated Freeze Complete (repository is in the research/report-preparation phase; this is not a production system)\
**Date:** 2026-09-23\

---

## 1. Executive Summary & Purpose

This document provides the authoritative, exhaustive evidence mapping for the final Capstone Project 1 report (*Evidence-Driven Dataset Intelligence and Recommendation System*). It anchors every proposed section, qualitative assertion, and quantitative metric directly to verified repository artifacts, test contracts, and experimental logs.

By enforcing strict epistemic discipline, this evidence map is intended to ensure that:
1. No exploratory or preliminary development result is inflated into a generalized research claim.
2. Scope reductions (e.g., structured `TaskSpecification` fixtures instead of an LLM requirement parser, absence of a CLI wrapper, non-learned scoring weights) are stated transparently as engineering boundaries.
3. Crucial experimental distinctions between the 10-record development corpus (M1–M7) and the 24-record frozen offline benchmark (M8) are preserved without conflation.
4. The human evaluation is characterized strictly as a documented exploratory pilot ($N=3$), disclosing all order and linkage caveats without inferential statistical claims.

---

## 2. Master Evidence Matrix

| Report Section | Subsection | Claim | Evidence Artifact | Exact Metric / Key Result | Milestone | Scope & Boundary | Claim Epistemic Classification |
|---|---|---|---|---|---|---|---|
| **1. Abstract** | Overview | System operates locally under strict memory bounds ($<128\text{ MiB}$) | `experiments/m8/results/m8_summary.json` | Peak RSS = 33.11 MiB (34,717,696 B), Wall-clock = 327.49 ms | M8 | Single-machine benchmark (macOS arm64); offline corpus | **Direct observation** |
| **1. Abstract** | Diversification | Family-aware greedy selection eliminates mirror-dataset redundancy | `experiments/m7/results/ranking_comparison.json`, `docs/M7_RESULTS.md` | Redundant pairs: 1 $\to$ 0 (UCI+OpenML Iris) | M7 | Demonstrated on 10-record dev corpus; M8 H1 was N/A | **Supported with limitation** |
| **1. Abstract** | Human Pilot | Format B received higher descriptive ratings across trust, understanding, actionability | `experiments/m8/human_eval/m8_human_eval_results.json`, `docs/M8_RESEARCH_FINDINGS.md` | $\Delta \text{Trust}=+1.81$, $\Delta \text{Und}=+3.19$, $\Delta \text{Act}=+3.00$ | M8 | Exploratory pilot; $N=3$ raters; order confound noted | **Descriptive result** |
| **3. Problem Statement** | Metadata Fallibility | Published catalog metadata contains genuine cross-field and cross-source conflicts | `experiments/m3/results/resolution_summary.json`, `docs/M3_RESULTS.md` | 1 genuine conflict (Rotten Tomatoes license: MIT vs URI); 84.9% unresolved | M3 | Single-source development records; text vs URI string clash | **Direct observation** |
| **3. Problem Statement** | Sample Slice Bias | First-slice record sampling cannot represent full dataset class distributions | `experiments/m4/results/fingerprint_summary.json`, `docs/M4_RESULTS.md` | Rotten Tomatoes: 32/32 rows label 1; majority ratio = 1.0; constant column detected | M4 | Bounded 32-record contiguous sample; slice bias demonstrated | **Direct observation** |
| **4. Motivation** | Popularity Bias | Platform download counts do not reflect downstream task-compatibility utility | `experiments/m6/results/popularity_audit.json`, `docs/M6_RESULTS.md` | 50% under-observed in dev corpus; high popularity uncorrelated with fit | M6 | 10-record development corpus; simulated catalog distribution | **Supported with limitation** |
| **7. Proposed System** | Epistemic Ledger | Models five distinct ledger observation states plus a separate four-state categorical resolution layer, rather than coercing missing data to default | `src/dataset_intelligence/evidence/ledger.py`, `docs/M3_RESULTS.md` | Ledger states: `single_source_claim` (62.6%), `observed` (21.5%), `unknown` (8.4%), `failed` (5.6%), `unsupported` (1.9%) | M3 | Implemented in ledger schema; structural coverage | **Implementation fact** |
| **8. Architecture** | Popularity Neutrality | Popularity metrics are architecturally excluded from candidate scoring formulas | `src/dataset_intelligence/ranking/scoring.py`, `src/dataset_intelligence/ranking/signals.py` | Verified absence of popularity in `score_candidate_r2` and `score_candidate_r3` | M7/M8 | Verified in code; empirical Spearman test was N/A ($n < 3$) | **Architectural property** |
| **8. Architecture** | Gating Order | Hard compatibility constraints precede soft ranking everywhere | `src/dataset_intelligence/ranking/pipeline.py`, `tests/test_utility.py` | 75% hard-gated in M5 dev evaluations; 22/24 gated in M8 CIFAR/Leaf | M5/M8 | Structural pipeline constraint; modality clash gating | **Architectural property** |
| **10. Retrieval** | Baseline Trade-offs | BM25 satisfies M0 memory envelope; dense MiniLM exceeds ceiling by 3.54× | `docs/M2_RESULTS.md`, `experiments/m2/results/benchmark.json` | BM25: 0.06 ms latency, zero external dependencies, documented as running within the M0 envelope (no separate BM25-specific RSS measurement recorded); Dense: 453.22 MiB RSS ($3.54\times$ 128 MiB ceiling) | M2 | Evaluated on 10 records × 4 queries; Recall@3 = 1.00 for all | **Direct observation** |
| **11. Evidence** | Ledger Distribution | Harvester yields 107 immutable entries across 10 canonical datasets | `experiments/m3/results/evidence_ledger.jsonl`, `docs/M3_RESULTS.md` | 54 metadata claims, 20 access probes, 13 Croissant claims, 10 doc claims, 10 observations | M3 | Development corpus coverage; 10.7 entries/candidate | **Direct observation** |
| **12. Fingerprinting** | Quality Extraction | Bounded content probes execute in sub-10ms without downloading binary payloads | `experiments/m4/results/fingerprint_summary.json`, `docs/M4_RESULTS.md` | 9.31 ms runtime, 24.20 MiB peak RSS, 0.0% null rate across tabular records | M4 | Evaluated on 7 sample-accessible records; 1 failed (Beans 502) | **Direct observation** |
| **13. Utility** | Baseline Ablation | Incorporating content fingerprints yielded higher task utility rank correlation | `experiments/m5/results/baseline_ablation.json`, `docs/M5_RESULTS.md` | Baseline C Spearman $\rho=0.9667$ vs Baseline A $\rho=0.9576$ (+0.0091) | M5 | 4 tasks × 10 datasets; Iris $\rho$ raised from 0.8424 to 0.8788 | **Supported with limitation** |
| **14. Exploration** | Long-Tail Surfacing | Exposure Disparity audit surfaces under-observed high-utility candidates | `experiments/m6/results/m6_summary.json`, `docs/M6_RESULTS.md` | `q_tabular_wine`: mean utility raised from 0.5476 to 0.6857 (+25.2%) | M6 | Demonstrated on 1 of 4 dev queries; 0 strict hidden gems found | **Exploratory result** |
| **15. Diversification** | Mirror Deduplication | Greedy family-aware diversification eliminates duplicate repository mirrors | `experiments/m7/results/ranking_comparison.json`, `docs/M7_RESULTS.md` | R1 redundancy = 1 $\to$ R3 redundancy = 0; mean utility raised 0.8506 $\to$ 0.8536 | M7 | Demonstrated on `task_tabular_iris` with UCI and OpenML Iris | **Direct observation** |
| **16. Experimental Setup** | Zero-Egress Benchmark | Benchmark executes entirely offline without live network socket connections | `experiments/m8/results/m8_summary.json`, `src/dataset_intelligence/evaluation/harness.py` | `network_egress: "forbidden"`, `zero_egress_verified: true` | M8 | Enforced via socket mocking and local committed cache | **Architectural property** |
| **17. Results: H1** | Lineage Redundancy | M8 corpus geometrically lacked duplicate mirror pairs in top-k candidate pool | `experiments/m8/results/m8_summary.json` (key `hypotheses.h1_lineage_redundancy`) | Status = `"N/A"`, eligible mirror pairs = 0 | M8 | 24-dataset M8 corpus; H1 demonstrated in M7, not in M8 | **Supported with limitation** |
| **17. Results: H2** | Evidence Reordering | Multi-objective scoring reorders candidates based on evidence and risk penalties | `experiments/m8/results/m8_summary.json` (key `hypotheses.h2_evidence_disambiguation`) | Status = `"exploratory_characterized"`, 3 of 33 divergent pairs reordered, 6/8 tasks divergent | M8 | Reordering observed (e.g. AG News > RT in news); exploratory | **Exploratory result** |
| **17. Results: H3** | Utility Retention | Diversification introduces zero utility loss on the evaluated benchmark | `experiments/m8/results/m8_summary.json` (key `hypotheses.h3_utility_retention`) | Utility delta = 0.000 across all 8 tasks; within $\epsilon=0.03$ tolerance | M8 | Property of corpus geometry (no mirror pairs triggered exclusion) | **Supported with limitation** |
| **17. Results: H4** | Popularity Invariant | Recommendation rankings do not depend on catalog popularity metrics | `experiments/m8/results/m8_summary.json` (key `hypotheses.h4_popularity_neutrality`) | `architectural_invariant_verified: true`; empirical Spearman N/A ($n < 3$) | M8 | Verified by code audit in `scoring.py`; statistical test untestable | **Architectural property** |
| **17. Results: H5** | Role Groundedness | Recommendation explanation cards are strictly grounded in upstream evidence | `experiments/m8/results/m8_summary.json` (key `hypotheses.h5_role_groundedness`) | 20 of 20 assigned roles grounded; 0 provenance violations | M8 | 20 cards evaluated across 8 tasks; 100% compliant | **Direct observation** |
| **18. Ablations** | Consistency Audit | M7 scores exhibit measurable alignment with M5 ground-truth rubric cutoffs | `experiments/m8/results/m8_summary.json` (key `consistency_audit`) | Brier score = 0.259314, descriptive ECE (5 bins) = 0.428503 | M8 | Internal consistency audit against design rubric, NOT calibration | **Direct observation** |
| **19. Robustness** | Fault Tolerance | Pipeline tolerates corrupt metadata, source deletion, and invalid data types | `experiments/m8/results/m8_summary.json` (key `robustness`) | 10 trials across 4 corruption suites $\to$ 0 crashes (crash rate 0.0%) | M8 | Synthetic perturbation suites evaluated on benchmark harness | **Direct observation** |
| **20. Sensitivity** | Weight Robustness | Rankings remain stable under $\pm 20\%$ weight perturbation and diversity sweeps | `experiments/m8/results/m8_summary.json` (key `sensitivity`) | Overall mean Jaccard = 1.0, Overall mean Kendall $\tau = 1.0$ | M8 | Evaluated across positive weight, risk weight, and $\lambda_{\text{div}}$ sweeps | **Direct observation** |
| **21. Human Evaluation** | Format Comparison | Format B cards received higher descriptive ratings across all dimensions | `experiments/m8/human_eval/m8_human_eval_results.json`, `docs/M8_RESEARCH_FINDINGS.md` | Trust: 1.95 $\to$ 3.76; Understanding: 1.62 $\to$ 4.81; Actionability: 1.33 $\to$ 4.33 | M8 | Exploratory pilot ($N=3$); RATER_1 schedule order confound | **Descriptive result** |
| **21. Human Evaluation** | Repeat Stability | Exploratory repeat exposures exhibit individual stability trajectory | `experiments/m8/human_eval/m8_human_eval_results.json`, `docs/M8_RESEARCH_FINDINGS.md` | Participant 2: 100% agreement across 3 exposures; P1/P3 E3 linkage uncorroborated | M8 | 84 repeat rows; non-independent; timestamp-linkage caveat for P1/P3 | **Exploratory result** |

---

## 3. Recommended Final Report Structure

The proposed structure is tailored to the VIT Bhopal Capstone Project 1 format, mapping each section directly to repository evidence and noting required framing boundaries.

```
1. Title Page & Certificate
2. Abstract
3. Chapter 1: Introduction & Motivation
   3.1 Context: The Public Dataset Discovery Bottleneck
   3.2 Metadata Fallibility & The Fallacy of Repository Ground Truth
   3.3 Popularity Bias & The Distortion of Catalog Search
   3.4 Problem Statement & Formal Scope Boundary
   3.5 Key Contributions
4. Chapter 2: Literature Review & Related Work
   4.1 Dataset Search Engines (Google Dataset Search, DataFinder)
   4.2 Data Profiling & Fingerprinting Heuristics
   4.3 Epistemic Trust & Provenance Ledgers
   4.4 Multi-Objective Recommendation & Diversification in Information Retrieval
5. Chapter 3: System Architecture & Design Principles
   5.1 Guiding Principles: Evidence Separation, Local-First, Bounded Operation
   5.2 Pipeline Architecture Overview
   5.3 Canonical Dataset Representation & Preserved Provenance
   5.4 Epistemic State Modeling & Multi-Source Ledger
   5.5 Bounded Sample Fingerprinting
   5.6 Task-Specific Utility & Hard Gating
   5.7 Long-Tail Exploration via Exposure Disparity
   5.8 Multi-Objective Ranking (R1, R2) and Greedy Diversification (R3)
   5.9 Recommendation Cards & Explanation Contract
   5.10 Scope Reductions & Architecture Disclosures (No NL Parser, No CLI)
6. Chapter 4: Experimental Methodology & Setup
   6.1 M0 Resource Envelope & Computing Bounds
   6.2 Development Corpus (M1–M7) vs. Frozen Offline Benchmark (M8)
   6.3 Ground-Truth Formulation (Option C Design Rubric)
   6.4 Offline Zero-Egress Execution Protocol
   6.5 Human Evaluation Pilot Design (Instrument, Stimulus Pairs, Protocol)
7. Chapter 5: Results & Empirical Findings
   7.1 Candidate Retrieval Performance & Memory Trade-offs (M2)
   7.2 Evidence Ledger Yield & Conflict Discovery (M3)
   7.3 Bounded Content Diagnostics & Slice Bias (M4)
   7.4 Utility Ablation Findings (M5: Baselines A, B, C)
   7.5 Popularity Audit & Exploration Simulation (M6)
   7.6 Diversification & Mirror Redundancy Elimination (M7)
   7.7 Milestone 8 Benchmark Evaluation (Hypotheses H1–H5)
   7.8 Pipeline Consistency Audit (Brier Score & ECE Diagnostics)
   7.9 System Robustness Under Data Corruption
   7.10 Scoring Weight Sensitivity Analysis
8. Chapter 6: Human Evaluation Exploratory Pilot
   8.1 Study Design, Stimulus Construction, and Rater Allocation
   8.2 Descriptive Rating Distributions (Trust, Understanding, Actionability)
   8.3 Per-Comparison and Per-Participant Trajectories
   8.4 Realized Methodological Caveats: Order Confound & N=3 Scope
   8.5 Supplementary Repeat-Exposure Observations
9. Chapter 7: Discussion, Limitations & Future Work
   9.1 Discussion of Findings
   9.2 Threats to Validity & Known Limitations
   9.3 Future Engineering & Research Extensions
10. Chapter 8: Conclusion
11. References
12. Appendices:
    A. Canonical Schema Specification
    B. Task Specification Fixtures
    C. Human Study Instrument & Stimulus Pairs
    D. Reproducibility & Environment Guide
```

---

## 4. Claim Discipline & Epistemic Boundaries

To withstand external academic examination, the final report must strictly observe the following classification and framing rules:

### A. Strict Classification Register

1. **SUPPORTED DIRECTLY:**
   - Operational resource compliance ($<128\text{ MiB}$ peak RSS across all milestones; 33.11 MiB in M8 benchmark).
   - Zero network egress during offline benchmark execution.
   - Robustness under synthetic corruption (0 crashes / 10 trials).
   - Grounded explanation card generation (20/20 roles compliant with upstream evidence).
   - Sensitivity stability at $\pm 20\%$ weight perturbation (mean Jaccard = 1.0, Kendall $\tau = 1.0$).
   - Real-world metadata-vs-Croissant conflict detection (Rotten Tomatoes license URI).

2. **SUPPORTED WITH LIMITATION:**
   - **M7 Family Diversification:** Observed mirror elimination (UCI+OpenML Iris) on the development corpus; must be explicitly distinguished from M8 H1.
   - **M8 H1 (Lineage Redundancy):** Must be reported as **`N/A`** in the M8 benchmark. Do NOT claim H1 was proven on the 24-dataset benchmark; explain that no mirror pairs survived into the R1 top-$k$ candidate pool due to benchmark corpus geometry.
   - **M8 H3 (Utility Retention):** The observed utility delta of $0.000$ satisfies the tolerance criterion ($\le 0.03$), but must be reported as a property of benchmark corpus geometry (no mirror exclusions were triggered), not general proof that diversification is costless.
   - **M5 Utility Correlation:** Baseline C raises Spearman $\rho$ from 0.9576 to 0.9667 (+0.0091) on 4 development tasks; report as directional evidence on a small corpus, not generalized optimality.

3. **ARCHITECTURALLY VERIFIED (Code Inspection):**
   - **M8 H4 (Popularity Neutrality):** Popularity metrics are completely absent from candidate scoring formulas (`score_candidate_r2`, `score_candidate_r3`). The pre-registered empirical statistical criterion ($|\rho| < 0.10$) was **N/A** because no task had $\ge 3$ datasets with measured popularity. The report must state that H4 was verified by architectural invariant in code, not statistical correlation.
   - **Hard Gating Precedence:** Enforced structurally in `pipeline.py` (filters out modality clashes before scoring).

4. **EXPLORATORY / DESCRIPTIVE (No Inferential Generalization):**
   - **M8 Human Evaluation:** Based on $N=3$ independent human participants across 7 comparisons. Primary analysis evaluates first exposure only (42 card rows, 126 ratings). Format B scored higher across all dimensions, with one tie. Report as **descriptive observations only**; do NOT report $p$-values, Wilcoxon tests, or claim statistical generalization. Disclose the RATER_1 presentation order confound and author non-blind status (Rater 1).
   - **M8 Supplementary Repeat Exposures:** 84 repeat rows are exploratory. Participant 2 was 100% stable; Participant 1 and 3 third-exposure attributions rely on timestamp proximity only and must be caveated.
   - **M6 Long-Tail Exploration:** +25.2% utility gain was demonstrated on 1 query (`q_tabular_wine`); 3 queries showed zero additions.

5. **DIAGNOSTIC (Not External Validation):**
   - **Brier Score (0.259) & ECE (0.429):** Must be reported strictly as an *Option C M7 Pipeline Consistency Audit* evaluating alignment between M7 scores and M5 design rubrics. It is **NOT** independent probabilistic calibration.

6. **NOT SUPPORTED / UNIMPLEMENTED (Disclose as Scope Reductions):**
   - Natural language requirement parsing (task inputs are structured `TaskSpecification` fixtures).
   - Interactive CLI wrapper (`cli.py`).
   - Learned scoring weights (weights are fixed heuristics).
   - Cleanlab integration, Dempster-Shafer formal combination, and DataFinder bi-encoder retrieval.

---

## 5. Architectural Accuracy & Scope Disclosures

When drafting the architecture and methodology chapters, the report must describe the code as implemented in `src/dataset_intelligence/` rather than the broader aspirational vision from early proposals:

| Component | Proposal / Spec Language | Actual Implemented State | Mandatory Report Framing |
|---|---|---|---|
| **Requirement Parser** | "Requirement Analyst: LLM / constrained parser" | Hard-coded `TaskSpecification` fixtures (`fixtures/m5_fixtures.json`, `m8_ground_truth_labels.json`) | State as an evaluated scope boundary: inputs are structured domain specifications; natural-language parsing is deferred to future interactive frontends. |
| **User Interface** | "Interactive CLI demonstration artifact" | Scripted runners (`scripts/run_m7_ranking.py`, `run_m8_benchmark.py`) outputting JSON/JSONL | State that outputs are structured JSON `RecommendationCard` and `RecommendationSet` data structures; no standalone `cli.py` exists. |
| **Scoring Weights** | "Learned multi-objective utility" | Fixed heuristic weights ($w_{\text{fit}}=0.35, w_{\text{util}}=0.35, w_{\text{evid}}=0.15, w_{\text{cov}}=0.15, w_{\text{risk}}=0.15$) | Acknowledge that weights are hand-calibrated heuristics; cite M8 sensitivity analysis to document that recommendations remained unchanged under the tested $\pm 20\%$ perturbations. |
| **Evidence Fusion** | "Formal Dempster–Shafer combination rule" | Categorical rule-based resolver producing four resolution states (corroborated, conflicting, unresolved, unknown) over the five ledger observation states | State that epistemic state resolution is categorical/rule-based, serving as a practical operational proxy for formal evidence fusion. |
| **Label Quality** | "Cleanlab confident learning integration" | Pure-Python sample diagnostics (null rate, duplicate rate, constant columns) | State that data quality is assessed via bounded sample profiling without heavy external dependencies. |
| **Dense Retrieval** | "DataFinder trained bi-encoder" | Baseline BM25 (default) + off-the-shelf `all-MiniLM-L6-v2` | State that dense retrieval was benchmarked and demonstrated to exceed the M0 memory ceiling by $3.54\times$, justifying BM25 as the constrained default. |

---

## 6. Numerical Source Register

This register compiles every major quantitative result in the repository to support numerical consistency across all report chapters:

| Milestone | Metric | Exact Reported Value | Source Artifact | Exact Key / Location | Interpretation & Meaning | Methodological Limitation |
|---|---|---|---|---|---|---|
| **M0** | Memory Provision Ceiling | 134,217,728 bytes (128.00 MiB) | `experiments/m0/results/budget_decision.json` | `derived_budgets.provisional_m1_process_memory_ceiling_bytes` | M0-measured/derived envelope (plan input: `configs/m0_compute_budget.json`) | Defined on macOS arm64 environment |
| **M0** | Latency Provision Ceiling | 20,000 ms (20.0 s) | `experiments/m0/results/budget_decision.json` | `derived_budgets.cold_per_query_time_budget_ms` | M0-measured/derived cold-start per-query upper bound | Single-process evaluation |
| **M2** | BM25 Mean Recall@1 | 0.875 (87.5%) | `docs/M2_RESULTS.md` | Table: Averaged across 4 queries | Successful lexical retrieval | Dev corpus has 10 records; 4 queries |
| **M2** | BM25 Mean Recall@3 | 1.000 (100.0%) | `docs/M2_RESULTS.md` | Table: Averaged across 4 queries | Perfect candidate recall at $k=3$ | Small corpus saturates recall |
| **M2** | BM25 Mean Latency | 0.06 ms | `docs/M2_RESULTS.md` | Table: Averaged across 4 queries | Sub-millisecond execution | Local in-memory index |
| **M2** | Dense MiniLM Peak RSS | 453.22 MiB (475,234,304 bytes) | `docs/M2_RESULTS.md` | Section 2 Table | Exceeds M0 ceiling by 3.54× | Excludes MiniLM from constrained default |
| **M3** | Harvested Evidence Entries | 107 entries | `experiments/m3/results/resolution_summary.json` | `input_corpus_records` / count | 10.7 entries per dataset average | 10 canonical datasets evaluated |
| **M3** | Single-Source Claims | 67 entries (62.6%) | `experiments/m3/results/resolution_summary.json` | `ledger_summary.by_observation_state` | Majority of metadata is uncorroborated | Publisher assertions |
| **M3** | Unresolved Claims | 90 resolutions (84.9%) | `experiments/m3/results/resolution_summary.json` | `resolution_summary.unresolved` | Claims lacking second source | Single-source corpus nature |
| **M3** | Conflicting Claims | 1 resolution (0.9%) | `experiments/m3/results/resolution_summary.json` | `resolution_summary.conflicting` | Detected Rotten Tomatoes license clash | String vs URI formatting conflict |
| **M4** | Fingerprinting Runtime | 9.31 ms | `docs/M4_RESULTS.md` | Section 2 Table | High-throughput content profiling | 10 datasets evaluated |
| **M4** | Fingerprinting Peak RSS | 24.20 MiB | `docs/M4_RESULTS.md` | Section 2 Table | Well within 128 MiB ceiling | Minimal memory footprint |
| **M4** | Tabular Null Rate | 0.0% | `docs/M4_RESULTS.md` | Section 6 Table | Clean sample records | Evaluated on first 32 rows |
| **M5** | Baseline C Spearman $\rho$ | 0.9667 | `experiments/m5/results/baseline_ablation.json` | `mean_metrics.baseline_c.mean_spearman_rho` | Best rank correlation with rubric | Evaluated on 4 dev tasks |
| **M5** | Baseline A Spearman $\rho$ | 0.9576 | `experiments/m5/results/baseline_ablation.json` | `mean_metrics.baseline_a.mean_spearman_rho` | Naive metadata baseline | $\Delta\rho = +0.0091$ vs Baseline C |
| **M5** | Hard-Gated Ratio | 75.0% (90 / 120 evaluations) | `docs/M5_RESULTS.md` | Section 4 | Modality mismatch filtering | Precedes soft ranking |
| **M6** | Exploration Utility Gain | +25.2% (0.5476 $\to$ 0.6857) | `experiments/m6/results/m6_summary.json` | `exploration_simulation_summary.q_tabular_wine.condition_a_mean_utility` / `condition_b_mean_utility` | Iris surfaced for botanical query | 1 of 4 queries showed gain; `popularity_audit.json` holds EDR/stratum audits, not the A/B pool means |
| **M6** | Strict Hidden Gems Found | 0 datasets | `docs/M6_RESULTS.md` | Section 4 Table | Strict predicate prevents false claims | Unmeasured popularity $\neq$ hidden gem |
| **M7** | R1 Redundant Pairs | 1 pair (UCI + OpenML Iris) | `experiments/m7/results/ranking_comparison.json` | `task_tabular_iris.baselines.r1_utility_only` | Utility-only creates duplicate mirrors | Demonstrated on dev corpus |
| **M7** | R3 Redundant Pairs | 0 pairs | `experiments/m7/results/ranking_comparison.json` | `task_tabular_iris.baselines.r3_diversified_set` | Family-aware greedy elimination | Redundancy eliminated |
| **M7** | R3 Mean Set Utility | 0.8536 (vs R1 0.8506) | `experiments/m7/results/ranking_comparison.json` | Aggregate mean | Replaces mirror with alternative | Aggregate across 4 dev tasks |
| **M8** | Benchmark Candidate Pool | 24 datasets × 8 tasks (192 pairs) | `data/benchmarks/m8_benchmark_manifest.json` | `corpus` / `tasks` counts | Full offline benchmark matrix | 1 Kaggle dataset excluded (HTTP 403) |
| **M8** | Benchmark Peak RSS | 34,717,696 bytes (33.11 MiB) | `experiments/m8/results/m8_summary.json` | `reproducibility.runtime_metrics.peak_rss_mib` | 25.9% of 128 MiB ceiling | Verified within M0 budget |
| **M8** | Benchmark Wall-Clock | 327.49 ms | `experiments/m8/results/m8_summary.json` | `reproducibility.runtime_metrics.wall_clock_ms` | Total time for all 8 tasks | 40.9 ms per task average |
| **M8** | H1 Lineage Redundancy | Status: N/A | `experiments/m8/results/m8_summary.json` | `hypotheses.h1_lineage_redundancy.status` | No mirror pairs in top-k | Corpus geometry constraint |
| **M8** | H2 Disambiguation Reordering | 3 of 33 divergent pairs | `experiments/m8/results/m8_summary.json` | `hypotheses.h2_evidence_disambiguation` | Multi-objective reorders candidates | 6 of 8 tasks divergent; exploratory |
| **M8** | H3 Utility Delta | 0.000 ($\le 0.03$ tolerance) | `experiments/m8/results/m8_summary.json` | `hypotheses.h3_utility_retention.utility_delta` | Zero utility loss from diversification | Corpus geometry property |
| **M8** | H4 Architectural Invariant | Verified: True | `experiments/m8/results/m8_summary.json` | `hypotheses.h4_popularity_neutrality` | Popularity absent from scoring | Empirical Spearman N/A ($n < 3$) |
| **M8** | H5 Role Grounding | 20 of 20 roles (0 violations) | `experiments/m8/results/m8_summary.json` | `hypotheses.h5_role_groundedness` | Cards grounded in evidence | 100% compliance across 8 tasks |
| **M8** | Consistency Brier Score | 0.259314 | `experiments/m8/results/m8_summary.json` | `consistency_audit.brier_score` | Alignment with design rubric | Diagnostic only; not calibration |
| **M8** | Consistency Descriptive ECE | 0.428503 | `experiments/m8/results/m8_summary.json` | `consistency_audit.descriptive_ece_5_bins` | 5-bin calibration error | Diagnostic only; not calibration |
| **M8** | Robustness Crash Rate | 0.0% (0 crashes / 10 trials) | `experiments/m8/results/m8_summary.json` | `robustness.crash_rate` | Zero crashes under corruption | 4 corruption suites; 10 trials total |
| **M8** | Sensitivity Mean Jaccard | 1.0 (criterion $\ge 0.80$) | `experiments/m8/results/m8_summary.json` | `sensitivity.overall_mean_jaccard` | Set membership invariant to weights | $\pm 20\%$ weight perturbation |
| **M8** | Sensitivity Mean Kendall $\tau$ | 1.0 (criterion $\ge 0.75$) | `experiments/m8/results/m8_summary.json` | `sensitivity.overall_mean_kendall_tau` | Rank order invariant to weights | $\pm 20\%$ weight perturbation |
| **M8** | Human Eval Format A Trust | Mean 1.95 (Median 2) | `experiments/m8/human_eval/m8_human_eval_results.json` | `primary_results.card_level_format_means.format_a.trust_mean` | Baseline card perceived as low trust | 21 observations ($N=3 \times 7$ pairs) |
| **M8** | Human Eval Format B Trust | Mean 3.76 (Median 4) | `experiments/m8/human_eval/m8_human_eval_results.json` | `primary_results.card_level_format_means.format_b.trust_mean` | Format B received higher trust ratings | $\Delta = +1.81$ (Median $+2$, range $[0, +3]$) |
| **M8** | Human Eval Format A Und. | Mean 1.62 (Median 2) | `experiments/m8/human_eval/m8_human_eval_results.json` | `primary_results.card_level_format_means.format_a.understanding_mean` | Baseline fails to convey suitability | 21 observations ($N=3 \times 7$ pairs) |
| **M8** | Human Eval Format B Und. | Mean 4.81 (Median 5) | `experiments/m8/human_eval/m8_human_eval_results.json` | `primary_results.card_level_format_means.format_b.understanding_mean` | Near-ceiling understanding | $\Delta = +3.19$ (Median $+3$, range $[+2, +4]$) |
| **M8** | Human Eval Format A Act. | Mean 1.33 (Median 1) | `experiments/m8/human_eval/m8_human_eval_results.json` | `primary_results.card_level_format_means.format_a.actionability_mean` | Minimal stub received lower actionability ratings | 21 observations ($N=3 \times 7$ pairs) |
| **M8** | Human Eval Format B Act. | Mean 4.33 (Median 4) | `experiments/m8/human_eval/m8_human_eval_results.json` | `primary_results.card_level_format_means.format_b.actionability_mean` | High decision utility | $\Delta = +3.00$ (Median $+3$, range $[+2, +4]$) |

---

## 7. Figure & Table Visualization Plan

The report must feature clear, informative figures and tables that illustrate empirical behavior without misrepresenting statistical power:

| Figure / Table | Title & Description | Purpose & Key Finding | Underlying Data Artifact | Status | Recommendation |
|---|---|---|---|---|---|
| **Figure 3.1** | End-to-End System Pipeline | Diagram of the implemented pipeline: fixture/curated corpus $\to$ ingestion $\to$ evidence ledger + bounded fingerprinting $\to$ hard-gated task utility $\to$ multi-objective ranking + family-aware diversification $\to$ JSON recommendation cards (candidate retrieval shown as the M2/M8 benchmarked component feeding ranked pools) | Architecture overview in `PROJECT_SPEC.md` | New | Render as clean vector architecture schematic |
| **Figure 3.2** | Two-Layer Evidence State Model | Block diagram of the five ledger observation states (`observed`, `single_source_claim`, `unsupported`, `failed`, `unknown`) and the four categorical resolution states (`corroborated`, `conflicting`, `unresolved`, `unknown`) | Concept from `docs/M3_EVIDENCE.md` | New | High-clarity block diagram |
| **Table 4.1** | M0 Computing Bounds & Access Envelope | Limits on memory (128 MiB), latency (20s), sample cap (32 records, 64 MiB), Kaggle metadata policy | `experiments/m0/results/budget_decision.json`, `configs/m0_compute_budget.json`, `docs/M0_COMPUTE_BUDGET_PLAN.md` | Existing | Markdown / LaTeX table |
| **Table 4.2** | Benchmark Corpus Specifications | 24 datasets across 4 sources (HF, OpenML, UCI, Kaggle), modalities, task mappings | `data/benchmarks/m8_benchmark_manifest.json` | Existing | Comprehensive summary table |
| **Figure 5.1** | Retrieval Latency vs. Memory Footprint | Scatter / bar plot comparing BM25 ($0.06\text{ ms}$, zero external dependencies; no separate BM25-specific RSS measurement recorded) vs. MiniLM ($700\text{ ms}, 453\text{ MiB}$) vs. Hybrid | `docs/M2_RESULTS.md`, `experiments/m2/results/benchmark.json` | New | Bar chart highlighting 128 MiB ceiling violation |
| **Table 5.2** | Evidence Ledger Yield & Observation States | Counts and percentages across evidence types and epistemic states | `experiments/m3/results/resolution_summary.json` | Existing | Replicate Table 3 from `docs/M3_RESULTS.md` |
| **Table 5.3** | Utility Estimation Baseline Ablation (A vs B vs C) | Comparative Spearman $\rho$ and NDCG metrics across 4 tasks | `experiments/m5/results/baseline_ablation.json` | Existing | Replicate Table 3 from `docs/M5_RESULTS.md` |
| **Figure 5.2** | Long-Tail Utility Expansion (`q_tabular_wine`) | Bar chart showing utility distribution before and after under-observed candidate injection | `experiments/m6/results/m6_summary.json` (`exploration_simulation_summary.q_tabular_wine`) | New | Bar chart showing $+25.2\%$ utility gain |
| **Table 5.4** | Recommendation Set Diversification Comparison (R1 vs R2 vs R3) | Set utility, diversity, and mirror redundancy count on development tasks | `experiments/m7/results/ranking_comparison.json` | Existing | Replicate Table 3 from `docs/M7_RESULTS.md` |
| **Table 5.5** | Milestone 8 Hypothesis Verification Matrix | Summary of H1–H5 acceptance criteria, observed metrics, and statuses | `experiments/m8/results/m8_summary.json` | Existing | Comprehensive summary table |
| **Figure 5.3** | Sensitivity Analysis: Jaccard & Kendall Stability | Plots of set similarity and ranking correlation across $\pm 20\%$ perturbations | `experiments/m8/results/m8_summary.json` | Existing | Show horizontal lines at 1.0 |
| **Figure 6.1** | Human Study Paired Likert Differences ($N=3$) | Paired dot / slope plot showing Format A vs Format B across Trust, Understanding, Actionability | `experiments/m8/plots/primary_paired_ratings_n3.svg` | Existing | Embed SVG from `experiments/m8/plots/` |
| **Figure 6.2** | Per-Comparison B-minus-A Advantage | Grouped bar chart of B-A difference across all 7 stimulus comparisons | `experiments/m8/plots/per_comparison_differences_n3.svg` | Existing | Embed SVG from `experiments/m8/plots/` |
| **Figure 6.3** | Participant 2 Repeat Trajectory Stability | Line plot showing 100% rating stability across 3 successive form completions | `experiments/m8/plots/participant2_repeat_trajectory.svg` | Existing | Embed SVG from `experiments/m8/plots/` |

---

## 8. Report Conclusion Outline

The conclusion must synthesize the completed research grounded strictly in empirical findings:

1. **What was built:**
   - A fully local, evidence-driven public dataset recommendation pipeline operating within a 128 MiB process ceiling.
   - Core modules covering multi-source ingestion, fast lexical retrieval, multi-facet evidence ledgers, bounded sample fingerprinting, hard-gated task utility, long-tail exploration, multi-objective ranking, and family-aware set diversification.

2. **What was empirically evaluated:**
   - M0–M7 development evaluation on a 10-record multi-source corpus.
   - M8 offline benchmark across 24 datasets and 8 tasks under zero network egress.
   - Robustness across 10 corruption trials and sensitivity across $\pm 20\%$ parameter perturbations.
   - M8 human evaluation pilot with $N=3$ participants across 7 comparison pairs.

3. **What the evaluation demonstrated:**
   - Bounded evidence and fingerprinting identify cross-source metadata conflicts and slice bias without downloading full datasets.
   - Family-aware diversification eliminates mirror-dataset redundancy (M7) while retaining set utility.
   - Hard gating filters out 75% of modality-clashing candidates prior to soft scoring.
   - Format B recommendation cards received higher descriptive ratings across trust (+1.81), understanding (+3.19), and actionability (+3.00) compared to minimal baseline metadata stubs.
   - Strict resource compliance: 33.11 MiB peak RSS and 327 ms wall-clock execution for the complete 8-task benchmark.

4. **What remains uncertain / limited:**
   - Corpus scale: Evaluated on 24 curated datasets; web-scale behavior remains unobserved.
   - H1 mirror redundancy in M8: Corpus lacked mirror pairs in top-$k$, resulting in an `N/A` benchmark status.
   - Popularity neutrality: Verified architecturally via scoring formulas; empirical correlation testing was prevented by small sample sizes ($n < 3$).
   - Scoring weights: Hand-calibrated fixed heuristics rather than learned parameters.
   - Human study: Small exploratory sample ($N=3$), realized RATER_1 order confound, and author non-blind participation preclude statistical generalizability.

5. **Primary research contribution:**
   - Demonstrating that dataset recommendation must separate candidate retrieval from empirical verification, explicitly model missing/conflicting claims, and evaluate recommendation sets as diversified bundles rather than independent ranking lists.
