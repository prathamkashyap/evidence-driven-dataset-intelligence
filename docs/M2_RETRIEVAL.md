# M2 Retrieval Baseline

M2 is candidate generation over M1 `CanonicalDataset` JSONL records only. It does not score suitability, resolve evidence, inspect samples, or rank final recommendations.

## Document representation

The lexical document is deliberately limited to dataset name, description, task, domain, modality, target, label type, tags, and intended use. Numeric structure, governance claims, source IDs, and popularity context are excluded: popularity is not a relevance signal.

## BM25

BM25 uses a deterministic in-process implementation (`k1=1.2`, `b=0.75`) with zero external dependencies. Ties are broken deterministically by `dataset_id`. BM25 runs entirely within the M0-derived 128 MiB process envelope and serves as the constrained reproducible baseline.

## Dense retrieval

Apache-2.0 `sentence-transformers/all-MiniLM-L6-v2` is a 384-dimensional sentence embedding model. Its measured peak RSS is **453 MiB**, which exceeds the M0-derived 128 MiB process ceiling by 3.54×. It is therefore classified as an **optional higher-capability dense backend**, not the constrained-deployment default. Model loading takes approximately 81 seconds (cold, including download); query encoding takes 16–1,870 ms per query on the development corpus.

Test runs use a deterministic 64-dimensional local encoder double (`TestDenseEncoder`) and never download a model.

## Hybrid retrieval

Reciprocal Rank Fusion (`k=60`) combines independently generated BM25 and dense lists. Results retain method-specific ranks/scores and deduplicate strictly by canonical `internal_id`; no fuzzy family merging occurs. The current implementation passes the same `top_k` to each constituent retriever before fusion; this is a documented simplification that has no effect on the 10-record development corpus.

## Query normalization

Query normalization extracts coarse task and modality constraints via token-set membership matching against a fixed term dictionary. Multi-word terms require all component words to appear as individual tokens. This avoids false substring matches (e.g., `"text"` inside `"textbook"`).

## Benchmark

`scripts/run_m2_benchmark.py` builds the dense representation from `experiments/m1/results/development_corpus.jsonl`, writes reproducibility metadata under `indexes/retrieval/m2/`, and writes the benchmark artifact to `experiments/m2/results/benchmark.json`. The versioned development gold labels are intentionally small and derived only from M1 canonical descriptions/task claims. See `docs/M2_RESULTS.md` for measured results and resource findings.
