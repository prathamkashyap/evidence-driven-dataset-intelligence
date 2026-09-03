# Milestone 5 — Task Utility Estimation Results

## 1. Experiment Setup

- **Script:** `scripts/run_m5_utility.py`
- **Inputs:**
  - 10 canonical dataset records from Milestone 1 (`experiments/m1/results/development_corpus.jsonl`)
  - 107 immutable evidence entries from Milestone 3 (`experiments/m3/results/evidence_ledger.jsonl`)
  - 10 deterministic fingerprints from Milestone 4 (`experiments/m4/results/dataset_fingerprints.jsonl`)
  - 4 reference task specifications and human-authored reference judgments from `tests/fixtures/m5_fixtures.json`
- **Output Artifacts:**
  - `experiments/m5/results/utility_estimates.jsonl` (120 complete `TaskUtilityEstimate` records)
  - `experiments/m5/results/baseline_ablation.json` (A/B/C quantitative comparative metrics)
  - `experiments/m5/results/utility_summary.json` (state distributions and resource measurements)
- **Evaluations:** 4 tasks $\times$ 10 datasets $\times$ 3 baselines = **120 evaluations**

---

## 2. Resource Measurements vs. M0 Envelope

| Metric | Measured Value | M0 Provision Limit | Status |
|---|---:|---:|---|
| **Peak Process RSS** | **24.67 MiB** (25,866,240 bytes) | 128.00 MiB (134,217,728 bytes) | **Compliant** (19.3% of ceiling) |
| **Total Wall-clock Runtime** | **28.47 ms** (for all 120 evaluations) | 20,000 ms per-query budget | **Compliant** |
| **Per-Evaluation Latency** | **0.237 ms** | N/A | **Sub-millisecond** |

The pure-Python utility estimator executes in under 30 milliseconds with negligible memory overhead (24.67 MiB peak RSS).

---

## 3. Baseline Ablation Findings (A vs. B vs. C)

| Baseline Mode | Description | Mean Spearman $\rho$ | Mean NDCG@3 | Mean NDCG@5 | Mean NDCG@10 |
|---|---|---:|---:|---:|---:|
| **Baseline A** | Metadata-Only Naive Compatibility | 0.9576 | 0.5421 | 0.6094 | 0.6766 |
| **Baseline B** | Metadata + M3 Evidence Ledger | 0.9576 | 0.5421 | 0.6094 | 0.6766 |
| **Baseline C** | Full Evidence (Meta + M3 + M4 Fingerprints) | **0.9667** | **0.5421** | **0.6094** | **0.6766** |

### Per-Task Spearman Rank Correlation ($\rho$):
| Task | Baseline A | Baseline B | Baseline C | Key Distinguishing Factor |
|---|---:|---:|---:|---|
| **`task_sentiment_binary`** | 1.0000 | 0.9879 | 0.9879 | Baseline B/C surface license conflicts; slice-bias rule preserves favorable rating. |
| **`task_news_multiclass`** | 0.9879 | 1.0000 | 1.0000 | Baseline B/C correctly prioritize verified text records over unverified metadata. |
| **`task_tabular_iris`** | 0.8424 | 0.8424 | **0.8788** | Baseline C achieves higher correlation by empirically verifying 4 continuous features and 3-class target structure on Iris vs. Wine (13 features). |
| **`task_image_cifar`** | 1.0000 | 1.0000 | 1.0000 | All baselines successfully identify CIFAR-100; Baseline B/C penalize Beans for HTTP 502 endpoint failure. |

---

## 4. Hard Gating & Epistemic State Distributions

- **Hard-Gated Evaluations:** 90 of 120 evaluations (75.0%) were hard-gated due to confirmed modality clashes across tasks (e.g. tabular datasets evaluated for image tasks).
- **Epistemic State Distribution (across 840 evaluated component dimensions):**
  - `unknown`: 426 (50.7%)
  - `known_favorable`: 285 (33.9%)
  - `known_unfavorable`: 69 (8.2%)
  - `unsupported`: 24 (2.9%)
  - `sample_limited_inference`: 20 (2.4%)
  - `conflicting`: 8 (1.0%)
  - `failed`: 8 (1.0%)

---

## 5. Methodological Limitations to Carry into M6 / M7

1. **Development Corpus Scope:** Evaluated over 10 canonical datasets and 4 development tasks. Full generalization will be tested during M8 frozen benchmark evaluation.
2. **Equal-Weight Baseline:** Baseline weights ($w_k = 1/7$) are an interpretable default baseline, not a learned optimal model.
3. **No Popularity Bias Correction in M5:** M5 estimates intrinsic utility only. Milestone 6 will introduce exposure disparity audits and long-tail exploration.
4. **No Multi-Objective Ranking in M5:** Milestone 7 will combine utility estimates with fit, evidence, novelty, coverage, and risk into the unified $R(D \mid Q)$ ranking term.
