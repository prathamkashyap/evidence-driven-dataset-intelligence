# Milestone 4 — Content Evidence & Dataset Fingerprinting Results

## 1. Experiment Setup

- **Script:** `scripts/run_m4_fingerprint.py`
- **Input Corpus:** 10 canonical dataset records from Milestone 1 (`experiments/m1/results/development_corpus.jsonl`)
- **Input Ledger:** 107 immutable evidence entries from Milestone 3 (`experiments/m3/results/evidence_ledger.jsonl`)
- **Cache & Fixtures:** `experiments/m0/cache` and `tests/fixtures/m4_fixtures.json`
- **Output Artifacts:**
  - `experiments/m4/results/dataset_fingerprints.jsonl` (10 deterministic fingerprint records)
  - `experiments/m4/results/fingerprint_summary.json` (aggregate diagnostics and resource metrics)
- **Hardware & Environment:** macOS arm64, Python 3.14.6, zero external heavy ML/CV dependencies

---

## 2. Resource Measurements vs. M0 Envelope

| Metric | Measured Value | M0 Provision Limit | Status |
|---|---:|---:|---|
| **Peak Process RSS** | **24.20 MiB** (25,378,816 bytes) | 128.00 MiB (134,217,728 bytes) | **Compliant** (18.9% of ceiling) |
| **Wall-clock Runtime** | **9.31 ms** | 20,000 ms query budget | **Compliant** |
| **Max Records Sampled** | **32 records** | 32 records hard cap | **Compliant** |
| **Max Bytes Sampled** | **5.4 KB** (max single payload) | 64 MiB hard cap | **Compliant** |

The pure-Python fingerprinting extractors operate with minimal memory overhead (24.20 MiB peak RSS), executing all 10 fingerprints in under 10 milliseconds.

---

## 3. Fingerprint Coverage & Modality Breakdown

The pipeline generated **10 deterministic `DatasetFingerprint` records** across all 10 canonical candidates:

| Primary Modality | Count | % of Corpus | Datasets |
|---|---:|---:|---|
| `tabular` | 4 | 40.0% | OpenML Iris (`ds_69f0f69749316e8b5768ef79`), OpenML Wine (`ds_a7472dc830bfc6394941b2f7`), UCI Iris (`ds_773a4c155a583474a0222bdf`), UCI Wine (`ds_9f128b3a604eed483953e7f8`) |
| `text` | 2 | 20.0% | HF Rotten Tomatoes (`ds_c9a42d9bd6268ce4a4cf6061`), HF AG News (`ds_3e424a817c66aab45e96797a`) |
| `image` | 1 | 10.0% | HF CIFAR-100 (`ds_40356f676278cb9903556c6e`) |
| `failed` | 1 | 10.0% | HF Beans (`ds_4e61d125afd0915cf8dcb4c6` — HTTP 502 from Viewer endpoint) |
| `unsupported` | 2 | 20.0% | Kaggle Pima Indians (`ds_c39f4b8a33e1fd6fecbf4bdc`), Kaggle Heart Disease (`ds_3c522d9aa8b9ec84e3b73660` — metadata-only under M0 policy) |

---

## 4. Modality Diagnostic Findings

### A. Tabular Datasets (4 candidates)
- **Iris (OpenML & UCI):** 4 numeric features (`sepal_length`, `sepal_width`, `petal_length`, `petal_width`) with valid extrema (e.g. `sepal_length`: min 4.9, max 7.0, mean 5.825) and 1 categorical target column (`species`).
- **Wine (OpenML & UCI):** 13 numeric features (`alcohol`, `malic_acid`, `ash`, etc.) and 1 categorical target column (`class`).
- **Missingness:** 0.0% null rate across all observed tabular records in development fixtures.

### B. Text Datasets (2 candidates)
- **Rotten Tomatoes:** 32 review records evaluated. Mean character length 97.6 chars (median 90.0, range 15–231 chars). Mean word count 16.5 words (median 15.0, range 2–38 words). 100% ASCII characters. 0.0% empty texts.
- **AG News:** 32 news headline records evaluated. Mean character length 43.2 chars.

### C. Image Datasets (1 candidate + 1 failed)
- **CIFAR-100:** Formats detected: `PNG` / `JPEG` metadata references. `image_bytes_available: false` (metadata-only references in Viewer rows; no unconstrained binary downloads triggered).
- **Beans:** Explicitly recorded as `primary_modality: "failed"` with error reason `"HTTP 502 from sample endpoint"`.

---

## 5. Target / Label Diagnostic Coverage

- **Target Columns Identified:** 6 of 10 datasets (60.0%).
  - Tabular datasets: `species` (Iris, 3 classes observed), `class` (Wine, 3 classes observed).
  - Text datasets: `label` (Rotten Tomatoes), `label` / `topic` (AG News).
- **Observed vs. Full Dataset Cardinality:**
  - In Rotten Tomatoes, the first 32 contiguous sample rows all contained label `1` (positive review).
  - The extractor accurately recorded `observed_sample_class_count: 1`, `observed_majority_class_ratio: 1.0`, and marked `constant_columns: ["label"]` for that specific sample slice.
  - This demonstrates the distinction between *observed sample evidence* and *full dataset ground truth*, preserving evidence fidelity without making false inferences about the complete dataset.

---

## 6. Quality Heuristics Distribution

Across the 7 datasets with accessible sample payloads:
- **Samples Evaluated:** 7
- **Mean Null Cell Rate:** 0.0%
- **Mean Duplicate Record Rate:** 0.0%
- **Constant Columns Detected:** 2 (label columns in slice-biased text samples)
- **Type Inconsistencies Detected:** 0

---

## 7. Unsupported and Failed Cases

Explicitly preserved operational realities:
1. `ds_4e61d125afd0915cf8dcb4c6` (Beans): `failed` (`HTTP 502 from sample endpoint`).
2. `ds_c39f4b8a33e1fd6fecbf4bdc` (Kaggle Pima Indians): `unsupported` (`Kaggle bounded sample access unsupported without credentials under M0 policy`).
3. `ds_3c522d9aa8b9ec84e3b73660` (Kaggle Heart Disease): `unsupported` (`Kaggle bounded sample access unsupported without credentials under M0 policy`).

---

## 8. Limitations to Carry Forward into M5

1. **Development Corpus Size:** Evaluated across 10 canonical datasets. Full-scale corpus evaluation will process larger candidate pools in M8.
2. **Slice Bias in Bounded Samples:** Non-shuffled contiguous samples (e.g. first 32 records of a sorted dataset) may exhibit class imbalance or constant labels. M5 task utility estimation must account for sample scope and sample acquisition method when interpreting label distributions.
3. **No Suitability Interpretation in M4:** M4 output is descriptive evidence only. Determining whether a dataset fits a user's task requirements (e.g. sequence length compatibility, class cardinality match, feature alignment) is the responsibility of M5.
