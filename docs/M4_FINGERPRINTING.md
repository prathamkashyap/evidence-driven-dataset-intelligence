# Milestone 4 — Content Evidence & Dataset Fingerprinting Specification

## 1. Overview and Purpose

Milestone 4 establishes the **content evidence and dataset fingerprinting** subsystem. It converts raw bounded content samples ($\le 32$ records) into structured, deterministic, and content-addressed `DatasetFingerprint` records.

M4 answers:
> *"What measurable structural, statistical, and bounded-sample quality characteristics can be derived from observed dataset content?"*

M4 does **not** evaluate whether a dataset is suitable for a specific user task or project.

---

## 2. Core Epistemic Principles

1. **Sample Scope as Scoped Evidence:** All metrics (row counts, column counts, word lengths, observed class counts) describe strictly the bounded sample ($\le 32$ records), never full-dataset truth.
2. **Deterministic Fingerprint Identity:** Fingerprint IDs (`fingerprint_id = "fp_" + sha256(...)[:24]`) are derived exclusively from stable content fields. Temporal timestamps (`observed_at`) are excluded from identity hashing so that identical replays produce identical IDs.
3. **M3 Evidence Linkage:** Every fingerprint preserves the list of M3 `LedgerEntry` IDs (`source_evidence_entry_ids`) and `raw_reference` pointers that gave rise to the sample.
4. **Explicit Operational States:** Datasets where content sampling is disallowed by platform policy (e.g. Kaggle without credentials) or fails operationally (e.g. Beans HTTP 502) produce explicit `unsupported` or `failed` fingerprints rather than empty or fabricated data.
5. **Zero Heavy ML/CV/NLP Dependencies:** All extraction algorithms use pure Python standard library (`struct`, `json`, `math`, `re`, `hashlib`). No PyTorch, SentenceTransformers, OpenCV, Pillow, or SpaCy.

---

## 3. Fingerprint Data Schema

`DatasetFingerprint` is an immutable, frozen dataclass with schema version `"1.0"`:

```python
@dataclass(frozen=True)
class DatasetFingerprint:
    fingerprint_id: str                      # 'fp_' + sha256(canonical_payload)[:24]
    dataset_id: str                          # Canonical internal ID ('ds_...')
    fingerprint_version: str                 # '1.0'
    primary_modality: str                    # 'tabular' | 'text' | 'image' | 'multimodal' | 'unsupported' | 'failed' | 'unknown'
    sample_scope: dict[str, Any]             # records_observed, bytes_observed, sample_sha256, acquisition_method
    structural_summary: dict[str, Any]       # feature_count, feature_names, feature_types
    modality_details: dict[str, Any]         # Modality-specific extracted metrics
    target_diagnostics: dict[str, Any]       # Target column, observed class frequencies, majority/minority ratios
    quality_heuristics: dict[str, Any]       # Missingness, duplicate rate, constant columns, mixed types
    provenance: dict[str, Any]               # observed_at, source_evidence_entry_ids, raw_reference, extractor_version
```

---

## 4. Modality Extractors

### A. Tabular Extractor (`tabular.py`)
- `observed_sample_row_count`: Number of rows inspected ($\le 32$).
- `observed_sample_column_count`: Total feature columns observed.
- `column_names`: Deterministically sorted feature column names.
- `inferred_column_types`: Mapping of column name to inferred primitive type (`numeric`, `categorical`, `text`, `boolean`, `datetime`, `unknown`).
- `counts_by_type`: Summary counts for each inferred type.
- `per_column_unique_counts`: Unique value cardinality per column in the sample.
- `numeric_feature_extrema`: For numeric features, computes `min`, `max`, and `mean` rounded to 4 decimals.
- `constant_columns`: Features exhibiting zero variance (exactly 1 unique value in sample).
- `per_column_missing_rates`: Cell missingness proportion per column.

### B. Text Extractor (`text.py`)
- `observed_text_records_count`: Number of text records inspected ($\le 32$).
- `empty_text_records_count`: Count of empty or whitespace-only records.
- `character_length_distribution`: `{"min": int, "max": int, "mean": float, "median": float}`.
- `word_count_distribution`: `{"min": int, "max": int, "mean": float, "median": float}` (word tokenized via deterministic regex).
- `duplicate_text_rate`: Proportion of identical text records in sample.
- `ascii_character_ratio`: Proportion of ASCII vs. non-ASCII characters across text.

### C. Image Extractor (`image.py`)
- Pure-Python struct/byte header inspection (PNG, JPEG, GIF, BMP) without Pillow/OpenCV.
- When raw bytes are available:
  - `observed_images_count`: Images inspected ($\le 32$).
  - `image_bytes_available`: `true`.
  - `dimensions_summary`: `min_width`, `max_width`, `min_height`, `max_height`, `aspect_ratio_mean`.
  - `detected_formats`: Formats detected from binary headers (e.g. `PNG`, `JPEG`).
  - `channels_distribution`: Channel counts (`1ch`, `3ch`, `4ch`).
  - `corrupt_images_count`: Images failing header decoding.
- When only metadata/URLs are present (e.g. Viewer rows without binary blobs):
  - `image_bytes_available`: `false`.
  - Captures format/URL presence without triggering large binary downloads.

---

## 5. Target / Label Diagnostics (`target.py`)

- Identifies target column explicitly or through common candidate names (`label`, `target`, `class`, `species`, `disease_label`, `sentiment`, `category`).
- Computes:
  - `target_column_name`: Identified target column.
  - `missing_target_rate`: Fraction of sample records missing target label.
  - `observed_sample_class_count`: Distinct classes observed in the 32-record slice.
  - `observed_class_frequencies`: Class frequency histogram.
  - `observed_majority_class_ratio`: Frequency of dominant class / total labeled records.
  - `observed_minority_class_ratio`: Frequency of rarest class / total labeled records.
- *Caveat:* Clearly labeled as sample observations. For example, Rotten Tomatoes' first 32 records contain only label `1`, yielding `observed_sample_class_count: 1`. M4 reports this factually without confusing it with the full dataset's binary class distribution.

---

## 6. Quality Heuristics (`quality.py`)

Deterministic, model-free data cleanliness diagnostics:
- `overall_null_rate`: Null cell fraction across all cells in sample.
- `columns_with_nulls`: Sorted list of columns containing nulls.
- `constant_columns`: Sorted list of non-informative single-value features.
- `duplicate_record_rate`: Exact duplicate row fraction.
- `degenerate_record_rate`: Fraction of records where all feature values are null.
- `type_inconsistent_columns`: Features containing mixed primitive types across rows.

---

## 7. Resource Strategy vs. M0 Envelope

| Constraint | Provision Limit | Implementation Strategy |
|---|---:|---|
| **Sample Cap** | 32 records | Hard truncation `sample[:32]` at pipeline entry |
| **Byte Cap** | 64 MiB | Verified prior to decoding; soft target 1 MiB |
| **Process Memory** | 128 MiB ceiling | Pure stdlib extractors; peak RSS measured at 24.20 MiB |
| **Execution Time** | $< 50$ ms / dataset | Pure Python parsing executes in $< 10$ ms for 10 datasets |

---

## 8. Explicit M4 vs. M5 Boundary

To prevent premature task reasoning in M4, measurements are strictly partitioned:

| Measurement / Concept | Milestone | Rationale |
|---|---|---|
| Observed sample row count ($\le 32$) | **M4** | Objective measurement of retrieved sample. |
| Dataset size sufficient for fine-tuning | **M5** | Requires model architecture and task sample requirements. |
| Feature counts & primitive types (numeric, categorical) | **M4** | Intrinsic structural property of data payload. |
| Features align with user's input specification | **M5** | Requires mapping user query requirements to schema. |
| Observed label cardinality (e.g. 3 classes in sample) | **M4** | Factual count of distinct values in target column. |
| Class distribution suitability for classification task | **M5** | Evaluates whether classes match user's target problem. |
| Missing-value rate and constant-column count | **M4** | Intrinsic data cleanliness diagnostic of sample. |
| Missingness penalty in suitability estimation | **M5** | Evaluates tolerance of downstream model to missing features. |
| Text character & word length distributions | **M4** | Statistical description of text records in sample. |
| Text length fits context window of target model | **M5** | Requires knowledge of user's LLM/encoder sequence length. |
| Image dimensions and aspect ratio | **M4** | Objective metadata from image header. |
| Image resolution adequate for computer vision task | **M5** | Depends on task resolution requirements (e.g. 224×224 vs 1024×1024). |
