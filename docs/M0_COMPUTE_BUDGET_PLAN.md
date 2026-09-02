# M0 Compute-Budget Validation Experiment

## Decision to make

Before implementing expensive candidate analysis, measure a small, reproducible pilot and use its results to choose the candidate-pool size and probe depth. The specification's 50–100 candidates remains a hypothesis until this experiment is complete.

## Fixed pilot design

Use ten real public dataset records: two each from five feasible source/access combinations, deliberately including at least two low-visibility records and at least two expected sample-access failures or restrictions when they can be obtained lawfully. Choose records spanning image, text, and tabular modalities where the source supports them. Record source terms/access route and avoid login-only or bulk downloads.

For three fixed natural-language task descriptions, repeat the following using a cold cache and then a warm cache:

1. Time source-level candidate discovery for the query and retain the first bounded pool (initially 20 candidates/source where available).
2. Time evidence collection for each selected record: native metadata, linked documentation, and structured metadata when available.
3. Attempt the documented least-invasive sample route in this order: viewer/streaming API, small/range request, public preview/sample endpoint. Stop at 32 records or 64 MiB per dataset, whichever comes first.
4. Where a legal and accessible sample is obtained, run one fixed, modality-appropriate lightweight diagnostic only. The exact diagnostic is selected and versioned before the run; no model training or Cleanlab analysis is part of M0.
5. Capture failures without retries that would violate source terms. Categorize each failure as authentication/gating, unavailable endpoint, incompatible format, rate limit, timeout, policy refusal, or unknown.

Run each query twice (cold/warm) on the same machine. Do not extrapolate from one run; report raw per-source/per-dataset observations and medians.

## Metrics and instrumentation

| Measure | Definition | Instrumentation |
|---|---|---|
| Candidate retrieval time | Monotonic elapsed time from request start to normalized candidate list for each source/query. | `time.perf_counter_ns()`; separate cold/warm cache state. |
| Evidence collection time | Elapsed time from selected record to persisted evidence response/claim list. | `time.perf_counter_ns()` per candidate and evidence channel. |
| Sample acquisition feasibility | Successful bounded sample acquisitions divided by attempts, reported with failure categories. | Attempt log with method, byte/record cap, access state. |
| Probe runtime | Elapsed time of the predeclared diagnostic on an acquired bounded sample. | `time.perf_counter_ns()` and sample count. |
| Peak memory | Maximum resident set size for each phase and full query run. | OS RSS sampler at a fixed interval; record platform and sampler method. |
| Repository access failure rate | Failed source operations divided by all source operations, with category and HTTP/status detail when available. | Structured operation log; do not collapse failures into missing metadata. |

Also record Python/package versions, operating-system and CPU description, network/cache state, random seed, source timestamp, source URL, request count, bytes transferred, configuration hash, and dataset identifiers. No credentials or private headers enter experiment artifacts.

## Budget-selection rule

After observing the pilot, set conservative budgets from the slowest stable source/modality, not the median alone. Candidate-pool size must satisfy the measured interactive latency target and peak-memory headroom on the target laptop. Probe depth must remain inside a per-candidate wall-clock cap and memory cap, while preserving a separately budgeted long-tail pool. If any source's access-failure rate is high or unstable, keep its metadata-only path, mark its sample state as `Unknown`, and do not silently remove it from evaluation.

M0 completes only when the protocol configuration, raw logs, summary table, selected budgets, and a rationale are committed. No retrieval engine, evidence resolver, content fingerprinting suite, or ranker is introduced as part of this bootstrap commit.

The committed protocol configuration is [`configs/m0_compute_budget.json`](../configs/m0_compute_budget.json). Its bootstrap validator performs no network activity and does not execute the experiment.
