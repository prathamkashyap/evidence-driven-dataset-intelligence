# M1 Data Foundation Results

M1 implemented canonical schema v1.0, deterministic normalization, identity, provenance, source capability reports, and a fixture-generated development corpus. It is a data foundation only: no retrieval, scoring, evidence resolution, probing, or recommendation behavior exists here.

The corpus contains 10 canonical records: four Hugging Face, two OpenML, two UCI controlled-seed records, and two Kaggle metadata records. It is generated deterministically with `python3 scripts/build_m1_corpus.py` from `tests/fixtures/m1_records.json` and written to `experiments/m1/results/development_corpus.jsonl`.

M0 limits are carried in `configs/m1_ingestion.json`, not adapter business logic. In particular, Kaggle remains metadata-only and UCI discovery remains unavailable. The corpus preserves source claims and explicit null observed-content fields; it does not validate underlying metadata claims or license compatibility.
