# M2 Retrieval Baseline — Results

This is a development benchmark on a 10-record canonical corpus with 4 manually curated queries. It establishes a measured retrieval baseline for later milestones. It is not evidence of generalized retrieval superiority.

## Benchmark setup

- **Corpus:** 10 deterministic canonical records from M1 (`experiments/m1/results/development_corpus.jsonl`)
  - 4 Hugging Face, 2 OpenML, 2 UCI, 2 Kaggle (metadata-only)
- **Queries:** 4 development queries (`experiments/m2/benchmark/development_queries.json`)
  - `q_text_sentiment`, `q_image_leaf`, `q_tabular_wine`, `q_news`
- **Relevance judgments:** 5 total relevant dataset–query pairs, manually derived from M1 canonical descriptions and task claims. Not independently validated beyond source metadata.
- **Methods:** BM25, dense (MiniLM), hybrid RRF
- **Platform:** macOS 26.6.2, arm64, Python 3.14.6, `sentence-transformers` 5.7.0, `torch` 2.13.0
- **Reproducibility hash:** `2df2400c4f5787391d170da4af621b51bd93a28e25e4d3cf9aa46b6d508d3aba`

## MiniLM resource measurement vs. M0 budget

| Measurement | Value | M0 ceiling | Status |
|---|---:|---:|---|
| Peak process RSS | 453.22 MiB (475,234,304 bytes) | 128 MiB (134,217,728 bytes) | **Exceeds by 3.54×** |
| Model load + index build | 81,000 ms | 20,000 ms cold budget | **Exceeds** |
| Embedding generation + queries | 5,039 ms | — | Within query budget |

**Decision:** `all-MiniLM-L6-v2` with PyTorch **does not fit** the M0-derived 128 MiB provisional process ceiling. The measured peak RSS of 453 MiB is 3.54× the budget.

The M0 budget is not raised. Instead:

- **Constrained reproducible baseline:** BM25 (`bm25-v1`) runs entirely within the M0 envelope using zero external dependencies, with sub-millisecond query latency and identical Recall@1 on the development queries.
- **Optional higher-capability dense backend:** `all-MiniLM-L6-v2` via `SentenceTransformersEncoder` is available for environments where the 128 MiB ceiling does not apply. Its retrieval quality and latency are measured and documented here, but it is not the constrained-deployment default.

Unit tests use the deterministic `TestDenseEncoder` (64-dimensional token-hash vectors) and never download a model.

## Retrieval metrics

### Per-query results

| Query | Method | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Precision@1 | MRR@10 | nDCG@10 | Latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| q_text_sentiment | BM25 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.12 ms |
| q_text_sentiment | Dense | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 740.49 ms |
| q_text_sentiment | Hybrid RRF | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 12.13 ms |
| q_image_leaf | BM25 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.03 ms |
| q_image_leaf | Dense | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 173.75 ms |
| q_image_leaf | Hybrid RRF | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 16.52 ms |
| q_tabular_wine | BM25 | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.05 ms |
| q_tabular_wine | Dense | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 16.30 ms |
| q_tabular_wine | Hybrid RRF | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 15.92 ms |
| q_news | BM25 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.04 ms |
| q_news | Dense | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1,870.23 ms |
| q_news | Hybrid RRF | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 15.75 ms |

### Averaged across 4 queries

| Method | Recall@1 | Recall@3 | Recall@10 | Precision@1 | MRR@10 | nDCG@10 | Mean latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| BM25 | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.06 ms |
| Dense (MiniLM) | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 700.19 ms |
| Hybrid RRF | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 15.08 ms |

**Observation:** All three methods produce identical Recall@1 (0.875) and perfect Recall@3+. The only Recall@1 miss is `q_tabular_wine`, which has two relevant datasets (UCI Wine and OpenML Wine); all methods rank one at position 1 and the other at position 2, yielding Recall@1 = 0.50 for that query.

## Interpretation and limitations

### What this benchmark shows

- BM25, dense, and hybrid retrieval are functional and deterministic over canonical records.
- On this small corpus with clear keyword overlap between queries and relevant descriptions, all methods retrieve the relevant datasets within the top 3.
- BM25 latency is sub-millisecond; dense latency is 16–1,870 ms per query (dominated by MiniLM encoding); RRF adds negligible overhead.

### What this benchmark does NOT show

- **No method differentiation:** With only 10 documents and strongly overlapping query terms, every method saturates at perfect Recall@3. The corpus is too small to distinguish BM25, dense, or hybrid retrieval quality. This is expected and documented, not a weakness of the implementation.
- **Not generalized evidence:** These results cannot be cited as evidence that hybrid retrieval is superior (or equal) to lexical-only retrieval. That question requires a larger corpus and more diverse queries, which belong to later evaluation milestones.
- **No evidence scoring:** M2 retrieval is candidate generation only. No evidence resolution, utility estimation, or final recommendation logic exists.
- **Metric instability:** With 4 queries and 10 documents, individual metric values are sensitive to single ranking changes. The near-perfect scores reflect corpus size, not system quality.

### Known simplifications

- **RRF constituent pool:** `retrieve_hybrid` passes the same `top_k` to both BM25 and dense before fusion. With 10 documents this has no effect; for larger corpora, retrieving a larger pool before fusion would be standard practice.
- **Dense retrieval returns all documents:** Unlike BM25 which filters `score > 0`, the dense index returns all `top_k` documents regardless of cosine similarity, including potentially negative similarities.
- **Query normalization:** Uses token-set matching for term detection (fixed from substring matching in this milestone).
- **Relevance judgments:** Derived from source metadata descriptions, not independently verified dataset content.

## Artifacts

| Artifact | Path |
|---|---|
| Benchmark results | `experiments/m2/results/benchmark.json` |
| Index metadata | `indexes/retrieval/m2/metadata.json` |
| Development queries | `experiments/m2/benchmark/development_queries.json` |
| Configuration | `configs/m2_retrieval.json` |
| M1 corpus | `experiments/m1/results/development_corpus.jsonl` |
