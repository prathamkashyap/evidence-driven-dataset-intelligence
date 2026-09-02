# Implementation Architecture and Roadmap

## Architecture boundary

The system is a local, reproducible decision pipeline. It separates source-specific acquisition from downstream reasoning so a repository's field names, popularity metrics, or API quirks never become ranking logic.

```text
task description -> requirement contract -> hybrid candidate pool
                                             |
                          source adapters -> canonical records
                                             |
             documentation / metadata / samples -> evidence ledger
                                             |
                        resolver + bounded observations -> utility estimate
                                             |
                  long-tail exploration -> family-aware diversified set
                                             |
                                  evidence-backed CLI/report + evaluation
```

## Module contracts

| Module | Responsibility | Boundary |
|---|---|---|
| `ingestion` | One adapter per public source; obey access terms; cache raw responses. | Emits native payload plus source/time/provenance, never ranking scores. |
| `normalization` | Produce canonical IDs, task/structure/governance/community/operational fields. | Retains raw claims and source links; unknown stays explicit. |
| `retrieval` | BM25, compact dense retrieval, fusion, hard-constraint policy, family pre-deduplication. | Produces a recall-oriented candidate pool; no claim verification. |
| `evidence` | Ledger of source claims, observations, timestamps, procedure, scope and reliability. | Stores claims independently from resolved fields and final scores. |
| `probing` | Legal/technical bounded sample acquisition, fingerprints, diagnostics and lightweight task probes. | All observations include sample size, acquisition method and uncertainty. |
| `utility` | Direct-probe estimates and clearly weaker transferred estimates for inaccessible datasets. | Does not claim whole-dataset or guaranteed downstream performance. |
| `exploration` | Same-constraint long-tail pool and exposure-bias audit. | Popularity is context/audit data, not core suitability. |
| `ranking` / `diversification` | Multi-objective fit, utility, evidence, coverage, novelty, risk; family-aware set selection. | Hard filters precede scoring; final output is a set with roles. |
| `reporting` | CLI/recommendation cards explaining measured, claimed, conflicting and unknown evidence. | No unsupported LLM-generated facts. |
| `evaluation` | Frozen benchmarks, ablations, robustness, calibration, diversity, efficiency and reproducibility logs. | No component is credited until experimentally compared. |

## Storage and reproducibility

`data/raw` stores cached source responses; `data/normalized` canonical records; `data/evidence` ledger exports; `data/fingerprints` bounded observations; `data/benchmarks` frozen inputs/judgments. `indexes` stores retrieval indexes. `experiments` stores configurations and immutable result artifacts. Each run will record config, source snapshot timestamps, package versions, seed, hardware/runtime context, cache keys, and failure states.

## Roadmap

| Milestone | Deliverable | Gate |
|---|---|---|
| M0 | Bootstrap plus compute-budget experiment plan | Set candidate and probe budgets from measured data. |
| M1 | Canonical schema, cache foundation, source adapters | Stable IDs and provenance-preserving records. |
| M2 | BM25/dense/hybrid retrieval baselines | Retrieval benchmark, not anecdotal examples. |
| M3 | Evidence ledger and provisional resolver | Explicit unknown/conflict behavior. |
| M4 | Bounded sample acquisition and fingerprints | Feasible, scoped observations. |
| M5 | Lightweight direct/transfer utility estimates | Stable, measured probe protocol. |
| M6 | Long-tail exploration and diversified selection | Exposure and redundancy audit. |
| M7 | Ranking and evidence-backed CLI cards | Explanations trace to records/ledger. |
| M8 | Frozen evaluation, ablations, robustness and calibration | Research claims supported by results. |
