# Milestone 3 — Evidence System Results

## 1. Experiment Setup

- **Script:** `scripts/run_m3_ledger.py`
- **Input Corpus:** 10 deterministic canonical records from Milestone 1 (`experiments/m1/results/development_corpus.jsonl`)
  - 4 Hugging Face, 2 OpenML, 2 UCI, 2 Kaggle (metadata-only)
- **Cache / Fixtures:** `experiments/m0/cache` and `tests/fixtures/m3_fixtures.json`
- **Output Artifacts:**
  - `experiments/m3/results/evidence_ledger.jsonl` (107 immutable records)
  - `experiments/m3/results/resolution_summary.json` (106 non-numerical claim resolutions)
- **Hardware & Environment:** macOS arm64, Python 3.14.6, zero external dependencies required for execution

## 2. Resource Measurements vs. M0 Envelope

| Metric | Measured Value | M0 Provision Limit | Status |
|---|---:|---:|---|
| **Peak Process RSS** | **23.47 MiB** (24,608,768 bytes) | 128.00 MiB (134,217,728 bytes) | **Compliant** (18.3% of ceiling) |
| **Wall-clock Runtime** | **23.56 ms** | 20,000 ms query budget | **Compliant** |
| **Max Records Sampled** | **32 records** | 32 records hard cap | **Compliant** |
| **Max Bytes Sampled** | **248.8 KB** (max single payload) | 64 MiB hard cap | **Compliant** |

Unlike M2 dense retrieval with PyTorch/MiniLM (which reached 453 MiB), the M3 evidence system operates entirely within the M0 provisional envelope (23.47 MiB peak RSS).

## 3. Evidence Yield Breakdown

The harvester produced **107 immutable ledger entries** across the 10 canonical dataset records (mean 10.7 entries/dataset):

### By Evidence Type
| Evidence Type | Count | % of Ledger | Description |
|---|---:|---:|---|
| `metadata_claim` | 54 | 50.5% | Source-published fields (name, description, task, modality, counts, license, version) |
| `access_probe` | 20 | 18.7% | Capability report and access policy declarations (2 per dataset) |
| `croissant_claim` | 13 | 12.1% | Croissant metadata status, distribution formats, recordSets, and license claims |
| `documentation_claim` | 10 | 9.3% | External documentation links and citations |
| `content_observation` | 10 | 9.3% | Bounded sample diagnostics or explicit unsupported/failed observations (1 per dataset) |

### By Observation State
| State | Count | % of Ledger | Operational Meaning |
|---|---:|---:|---|
| `single_source_claim` | 67 | 62.6% | Publisher assertions without independent validation |
| `observed` | 23 | 21.5% | Directly measured via bounded sample probes and operational capability checks |
| `unknown` | 9 | 8.4% | Explicit absence (e.g. absent Croissant metadata on 9 datasets) |
| `failed` | 6 | 5.6% | Operational endpoint failures (e.g. Beans HTTP 502 from HF viewer, unreachable sample endpoints) |
| `unsupported` | 2 | 1.9% | Policy-bounded exclusions (Kaggle sample acquisition without credentials) |

### By Source
| Source | Entries Harvested | Sample Path Feasibility |
|---|---:|---|
| `huggingface` | 44 | Supported via Viewer (Beans failed with 502; Rotten Tomatoes, CIFAR, AG News observed) |
| `openml` | 22 | Supported via REST and ARFF streams |
| `uci` | 22 | Supported via direct flat-file streams |
| `kaggle` | 19 | Metadata-only; sample acquisition recorded as `unsupported` |

## 4. Provisional Resolution Findings

The non-numerical resolver evaluated **106 discrete claim types** across the 10 datasets:

| Resolution State | Count | % of Resolutions | Interpretation |
|---|---:|---:|---|
| `unresolved` | 90 | 84.9% | Single substantive observation; uncorroborated by independent sources |
| `unknown` | 15 | 14.2% | Claim property was unstated or all observations failed |
| `conflicting` | 1 | 0.9% | Multiple observations asserted contradictory values |
| `corroborated` | 0 | 0.0% | In this single-source dataset corpus, no cross-repository merging was performed |

### Qualitative Analysis of Conflicting Claim
A real-world conflict was detected on `ds_c9a42d9bd6268ce4a4cf6061` (Rotten Tomatoes):
- **Metadata claim (from `cardData.license`):** `"MIT"`
- **Croissant claim (from `@graph[license]`):** `"https://opensource.org/licenses/MIT"`
- **Resolution:** Marked as `conflicting` with references to both immutable entry IDs.
- **Epistemic significance:** Without domain-specific URI-to-SPDX normalization, string identifiers and URI references conflict textually. M3 surfaces this conflict explicitly rather than silently coercing or discarding claims.

## 5. Limitations and Boundaries

1. **Small development corpus:** Measured over 10 canonical records from M1. This provides structural validation of the ledger and resolver, but does not represent web-scale evidence distributions.
2. **Corroboration requires multi-source ingestion:** Because M1 assigns distinct internal IDs to datasets across repositories (e.g. UCI Iris vs. OpenML Iris vs. Kaggle Iris are treated as separate canonical records), corroboration within a single record is limited to metadata-vs-sample or metadata-vs-Croissant agreement. Multi-source dataset family corroboration will be handled in later deduplication and linkage stages.
3. **No quality inference:** High evidence count does not imply high dataset quality; `failed` or `unsupported` access does not imply low dataset quality.
4. **No ranking or numerical scores:** M3 preserves evidence neutrality and introduces no scoring weights.
