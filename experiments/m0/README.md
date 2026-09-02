# M0 Measurement Harness

This directory contains the bounded, public-access experiment that informs later implementation budgets. It is instrumentation only: it does not rank datasets, resolve claims, train models, or calculate dataset quality.

## Run

```bash
python3 scripts/run_m0.py --reset-cache
```

`--reset-cache` clears only `experiments/m0/cache`, then runs one cold condition followed immediately by one warm condition. The cache stores permitted response fragments locally and is ignored by Git. No credentials, cookies, tokens, or private headers are read or written.

## Protocol

The fixed inputs live in [`configs/m0_compute_budget.json`](../../configs/m0_compute_budget.json): ten public records, five source/access combinations, three queries, a 32-record / 64 MiB hard cap, and the `record_shape_digest_v1` diagnostic. For direct text/ARFF files, the harness retains only up to 32 data records. For Hugging Face Viewer requests, it asks the documented `/rows` endpoint for 32 rows. Kaggle samples are deliberately not attempted because M0 has no credentials and no configured anonymous bounded-file endpoint.

The only diagnostic reports bounded-record serialized sizes and a SHA-256 digest. It is not a quality, utility, licensing, or full-dataset claim.

## Outputs

- `results/records.jsonl`: one validated measurement record per operation.
- `results/summary.json`: phase/cache aggregates and access failure rates.
- `M0_RESULTS.md`: measured findings and the resulting budgets after a completed run.
- `cache/`: permitted external response fragments, ignored by Git.
