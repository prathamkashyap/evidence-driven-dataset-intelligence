# M0 Compute-Budget Validation Results

Run date: 2026-09-02 (UTC)
Run ID: `m0-20260902T042719Z`
Configuration SHA-256: `c01a7042ba0007ae35aa66c2bfb4e1e66d79cf4124c9908e3e228e1429b4b854`

This is an instrumentation result, not a dataset recommendation or quality evaluation. Source metadata remains a source claim. The `record_shape_digest_v1` diagnostic only summarizes the bounded records actually obtained; it does not describe an entire dataset or establish task utility.

## Exact protocol and runtime

The committed [M0 configuration](../../configs/m0_compute_budget.json) used ten public records, five source/access combinations, three fixed task descriptions, one cold pass followed by one warm pass, a 32-record / 64 MiB hard acquisition cap, and no model training. The actual process used Python 3.14.6 on macOS 26.6.2 (`arm64`), had no third-party runtime dependencies, and recorded seed `20260902`.

The peak process RSS was **37,994,496 bytes (36.23 MiB)**. The RSS reading is macOS `ru_maxrss`, recorded in bytes. The cold pass made **25** public HTTP requests; the warm pass made **0** public HTTP requests because all permitted response fragments—including failures—were reused from the local cache.

Warm fetch latency is recorded as `0.0 ms` by the harness when it bypasses network transfer. This confirms cache reuse; it is not a microbenchmark of filesystem cache-read latency.

## Sources, access routes, and records

| Source/access combination | Records | Public route used | Result |
|---|---|---|---|
| Hugging Face Dataset Viewer: text rows | Rotten Tomatoes; AG News | Documented `/rows` viewer endpoint, 32 requested rows | Both sampled. |
| Hugging Face Dataset Viewer: image rows | CIFAR-100; Beans | Documented `/rows` viewer endpoint, 32 requested rows; media URLs were not fetched | CIFAR-100 sampled; Beans returned HTTP 502. |
| OpenML: metadata then ARFF stream | OpenML 61 iris; OpenML 187 wine | REST metadata then first 32 ARFF data records | Both sampled. |
| UCI: public flat-file stream | Iris; Wine | Public repository landing page plus first 32 non-empty flat-file records | Both sampled. |
| Kaggle: public metadata, no credentialed sample | uciml/iris; uciml/pima-indians-diabetes-database | Public metadata endpoint only; no token, cookie, or file-download workaround | Iris metadata succeeded; Pima metadata returned HTTP 403; neither file sample was attempted. |

Relevant platform/API documentation was recorded in the configuration: [Hugging Face Viewer rows](https://huggingface.co/docs/dataset-viewer/rows), [OpenML REST API](https://docs.openml.org/ecosystem/Rest/), [UCI privacy/access notice](https://uci-ics-mlr-prod.aws.uci.edu/privacy), and [Kaggle Public API guide](https://www.kaggle.com/getting-started/524433). These links describe access mechanisms, not dataset reuse permission or legal clearance.

## Fixed queries

1. `q_text_sentiment`: supervised sentiment classification for short review text.
2. `q_image_classification`: small multiclass image classification experiment.
3. `q_tabular_classification`: supervised tabular multiclass classification.

Hugging Face and Kaggle used their public search endpoints. OpenML measured one documented 20-record catalog snapshot because its M0 call was not configured as semantic search. UCI had no configured documented programmatic search endpoint, so its three candidate-discovery measurements are explicitly `unavailable_endpoint`, not failed dataset access.

## Cold-cache measurements

| Stage | Attempts | Successful operations | Median latency | Maximum latency | Network requests |
|---|---:|---:|---:|---:|---:|
| Candidate discovery/catalog requests | 7 | 7 | 536.918 ms | 890.625 ms | 7 |
| Evidence collection | 10 | 9 | 459.779 ms | 2,457.222 ms | 10 |
| Direct sample acquisition | 8 | 7 | 819.661 ms | 1,374.951 ms | 8 |
| Lightweight diagnostic (successful samples only) | 7 | 7 | 0.144 ms | 0.987 ms | 0 |

Candidate requests tied to individual queries took 941.718–1,294.857 ms across the two semantic public APIs. The additional OpenML catalog snapshot took 890.625 ms. Across all cold operations, measured stage time totaled 18,389.626 ms; this is a small serial pilot, not an end-to-end recommendation latency estimate.

Seven successful direct samples each contained exactly 32 retained records. Their retained response sizes ranged from **896 bytes** to **22,898 bytes** (42,809 bytes total). No full image, audio, archive, or complete dataset was retrieved. The largest direct sample latency was OpenML iris at 1,374.951 ms.

## Warm-cache behavior

The warm pass repeated all 40 operation records with the same results: **30 successful operations, 0 network requests**. All fetchable candidate, evidence, and sample records showed `cache_state: warm`; Kaggle policy non-attempts and diagnostics correctly remain `not_applicable`. Caching failures prevents repeated calls to an endpoint that has already returned a deterministic access error during a run.

## Access and failure observations

| Source | Evidence/sample operations per condition | Failures | Failure rate | Observed reason |
|---|---:|---:|---:|---|
| Hugging Face | 8 | 1 | 12.5% | Beans viewer `/rows` returned HTTP 502; retained as `Unknown` access outcome. |
| OpenML | 4 | 0 | 0% | Both metadata and bounded ARFF paths succeeded. |
| UCI | 4 | 0 | 0% | Both landing-page metadata and bounded flat-file paths succeeded. |
| Kaggle | 4 | 3 | 75.0% | Pima metadata HTTP 403; both file samples intentionally not attempted without a documented bounded anonymous path or credentials. |

Direct sample feasibility across the ten fixed records was **7/10 (70%)**. Among the eight network sample attempts, it was **7/8 (87.5%)**. The remaining two Kaggle sample paths are policy-limited non-attempts, not evidence that the datasets are unusable or unsuitable.

## Derived budgets for later milestones

The structured decision is in [`results/budget_decision.json`](results/budget_decision.json).

| Budget | Decision | Basis and limitation |
|---|---:|---|
| Source candidate pool | 20 per programmatic source; 60 combined pre-evidence cap | Matches the measured public endpoint cap. It is not a claim that 60 candidates can undergo analysis. |
| Evidence-analysis pool | 10 candidates/query | The sequential ten-record metadata pass took 7.579 s cold, with UCI landing pages as the slow tail. |
| Direct content-probe pool | 6 candidates/query | Seven of eight direct network sample attempts succeeded; six reserves one failure margin and excludes credential-limited paths. |
| Sample budget | 32 records; 1 MiB soft target; 64 MiB hard cap | Largest retained success was 22,898 bytes. The hard cap remains a safety constraint, not a desired download size. |
| Cold per-query budget | 20 s | The serial pilot consumed 18.390 s across all cold stages; this is intentionally conservative and must be rechecked after M1. |
| Memory ceiling | 128 MiB provisional M1 process ceiling | Provides headroom over the measured 36.23 MiB M0 peak; parsing and cache implementations must revalidate it. |
| Direct-source failure threshold | at most 20% | Hugging Face, OpenML, and UCI met it in this pilot; Kaggle did not and remains metadata-only absent a permitted path. |

## Architectural implications and unresolved questions

- A source adapter must separate metadata retrieval from sample acquisition and preserve failure states; a sample failure cannot silently remove a candidate later.
- Caching is mandatory. Warm replay eliminated all 25 public requests, including repeated HTTP 403/502 outcomes.
- Kaggle should begin as a metadata-only source under this no-credential environment. Adding authentication or a download route requires a separate compliance review; M0 does not authorize it.
- UCI can provide bounded direct samples, but it needs a separate discovery strategy because no programmatic search endpoint was measured here.
- The Hugging Face viewer supports low-cost bounded rows, but the observed 502 requires retry/backoff policy design and later availability measurement; M0 did not retry it.
- M0 does not establish BM25/dense-retrieval cost, canonical-schema memory, utility-probe cost, ranking quality, licensing compatibility, or sample representativeness. Those remain hypotheses for later measured milestones.
