# Evidence-Driven Dataset Intelligence and Recommendation System

This Capstone Project 1 builds a local-first system that recommends a small, useful **set** of public ML/DL/CV datasets for a natural-language task description. It is deliberately not a generic LLM or RAG application: retrieval produces candidates, while evidence collection, bounded content observations, uncertainty, task utility, long-tail exploration, and diversification support the final decision.

The implementation follows [the project specification](docs/PROJECT_SPEC.md) and [research foundation](docs/RESEARCH_FOUNDATION.md). Repository metadata is treated as evidence rather than unquestioned fact; unknown and conflicting evidence must remain visible.

## Current milestone: M1 — canonical corpus and source adapters

M0 measured the local access and compute envelope. M1 now provides a deterministic, source-independent ten-record development corpus with preserved source claims and explicit access capabilities. It does **not** implement retrieval, evidence resolution, probing, ranking, or recommendations.

- [Implementation architecture and roadmap](docs/IMPLEMENTATION_PLAN.md)
- [M0 experiment protocol](docs/M0_COMPUTE_BUDGET_PLAN.md)
- [Bootstrap reconnaissance and gap report](docs/BOOTSTRAP_RECONNAISSANCE.md)
- [Canonical schema](docs/CANONICAL_SCHEMA.md)
- [Source adapters](docs/SOURCE_ADAPTERS.md)
- [M1 results](docs/M1_RESULTS.md)

## Local setup

M0 uses only the Python standard library. Python 3.10 or later is required; Python 3.11–3.13 is the preferred range for later scientific-library compatibility. Create an isolated environment when subsequent milestones introduce pinned dependencies.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_bootstrap.py
python3 scripts/build_m1_corpus.py
```

No dataset retrieval or remote source calls occur during bootstrap validation. Future optional dependencies are selected only after M0 measures their need and cost.

## Development rules

- Work one milestone at a time and stop at each boundary.
- Keep source adapters isolated from canonical records and downstream ranking.
- Record provenance, timestamps, procedure, scope, and unknown/conflicting states.
- Treat hard requirements as filters; never use popularity as a suitability proxy.
- Cache external observations and make experiments replayable.
- Do not infer legal clearance or whole-dataset quality from a source claim or bounded sample.
- Add a test and documentation for each substantial module; inspect every diff before committing.

See [AGENTS.md](AGENTS.md) for the repository working agreement.
