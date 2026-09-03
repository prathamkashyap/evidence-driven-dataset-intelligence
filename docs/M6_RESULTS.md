# Milestone 6 — Popularity-Bias Audit & Long-Tail Exploration Results

## 1. Experiment Setup

- **Script:** `scripts/run_m6_exploration.py`
- **Inputs:**
  - 10 canonical dataset records from Milestone 1 (`experiments/m1/results/development_corpus.jsonl`)
  - Retrieval run benchmarks from Milestone 2 (`experiments/m2/results/benchmark.json`)
  - Utility estimates from Milestone 5 (`experiments/m5/results/utility_estimates.jsonl`, Baseline C)
  - Task specifications from `tests/fixtures/m5_fixtures.json`
- **Output Artifacts:**
  - `experiments/m6/results/popularity_profiles.jsonl` (10 source-aware `DatasetPopularityProfile` records)
  - `experiments/m6/results/popularity_audit.json` (Guarded exposure disparity metrics across 4 queries)
  - `experiments/m6/results/exploration_pools.jsonl` (Main vs. augmented exploration candidate pools per query)
  - `experiments/m6/results/m6_summary.json` (Summary statistics and runtime measurements)

---

## 2. Resource Measurements vs. M0 Envelope

| Metric | Measured Value | M0 Provision Limit | Status |
|---|---:|---:|---|
| **Peak Process RSS** | **25.08 MiB** (26,296,320 bytes) | 128.00 MiB (134,217,728 bytes) | **Compliant** (19.6% of ceiling) |
| **Wall-clock Runtime** | **12.29 ms** | 20,000 ms per-query budget | **Compliant** |

---

## 3. Popularity Profiling Distribution

Across the 10 canonical datasets:
- **Measured Popularity (`popularity_measurement_state == "measured"`):** **5 datasets** (50.0%)
  - `very_high`: 2 (Rotten Tomatoes: 1200 downloads; Kaggle Iris Species: 1000 downloads)
  - `high`: 1 (AG News: 900 downloads)
  - `low`: 1 (CIFAR-100: 800 downloads)
  - `very_low`: 1 (Beans: 300 downloads)
- **Under-Observed Popularity (`popularity_measurement_state == "under_observed"`):** **5 datasets** (50.0%)
  - `unknown`: 5 (OpenML Iris, OpenML Wine, UCI Iris, UCI Wine, Kaggle Pima)

---

## 4. Exposure Audit & Exploration Simulation Findings

### Quantitative Comparison: Condition A (M2 Top-3) vs. Condition B (Augmented Exploration Pool)

| Query / Task | Condition A Main Pool | Cond A Mean Utility | Condition B Augmented Pool | Cond B Mean Utility | Under-Exposed Found | Under-Observed High-U Found | Hidden Gems Found |
|---|---|---:|---|---:|---:|---:|---:|
| **`q_text_sentiment`** (`task_sentiment_binary`) | RT, AG News, CIFAR-100 | 0.5953 | RT, AG News, CIFAR-100 | 0.5953 | 0 | 0 | 0 |
| **`q_news`** (`task_news_multiclass`) | AG News, RT, CIFAR-100 | 0.5667 | AG News, RT, CIFAR-100 | 0.5667 | 0 | 0 | 0 |
| **`q_tabular_wine`** (`task_tabular_iris`) | UCI Wine, OpenML Wine, CIFAR-100 | 0.5476 | UCI Wine, OpenML Wine, CIFAR-100, **UCI Iris**, **OpenML Iris** | **0.6857** (+25.2%) | 2 | 2 | 0 |
| **`q_image_leaf`** (`task_image_cifar`) | Beans, CIFAR-100, Kaggle Pima | 0.5190 | Beans, CIFAR-100, Kaggle Pima | 0.5190 | 0 | 0 | 0 |

### Key Experimental Insights:
1. **Under-Observed Exploration Value (`q_tabular_wine`):**
   Standard lexical/dense retrieval for tabular wine queries placed Wine datasets and text/image candidates in Top-3. The under-exposed exploration mechanism successfully surfaced **UCI Iris** ($U=0.9143$) and **OpenML Iris** ($U=0.8714$) for the botanical task, raising the mean utility of the candidate pool from $0.5476$ to **$0.6857$**.
2. **Hidden-Gem Strictness:**
   Zero datasets qualified for the strict `hidden_gem` designation because the measured low-popularity datasets (Beans) suffered operational endpoint failures (HTTP 502). The high-utility Iris candidates were correctly designated as **`under_observed_high_utility`** rather than fabricated as hidden gems, honoring the requirement that unmeasured popularity $\neq$ obscure hidden gem.

---

## 5. Development Corpus Limitations

1. **Development Simulation Scope:** The exploration pool was constructed over a 10-dataset local development corpus. It demonstrates the correctness of the multi-pool selection and audit algorithms, but does **not** constitute proof of web-scale dataset discovery.
2. **Platform Opacity:** Because OpenML and UCI API responses do not expose download/star metrics, 50% of the corpus remains `under_observed`.
3. **No Multi-Objective Ranking in M6:** Milestone 7 will consume these augmented candidate pools to perform multi-objective set selection, GIST/submodular diversity optimization, and role assignment.
