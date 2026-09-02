# Evidence-Driven Dataset Intelligence and Recommendation System

This Capstone Project 1 builds a local-first system that recommends a small, useful **set** of public ML/DL/CV datasets for a natural-language task description. It is deliberately not a generic LLM or RAG application: retrieval produces candidates, while evidence collection, bounded content observations, uncertainty, task utility, long-tail exploration, and diversification support the final decision.

The implementation follows [the project specification](docs/PROJECT_SPEC.md) and [research foundation](docs/RESEARCH_FOUNDATION.md). Repository metadata is treated as evidence rather than unquestioned fact; unknown and conflicting evidence must remain visible.

## Current milestone: M0 — bootstrap and compute-budget validation planning

The repository is bootstrapped for measured, incremental implementation. M0 does **not** implement retrieval, evidence resolution, probing, or ranking. Its next execution will run a bounded experiment over roughly ten real datasets to set feasible candidate-pool and probe budgets before expensive functionality is built.

- [Implementation architecture and roadmap](docs/IMPLEMENTATION_PLAN.md)
- [M0 experiment protocol](docs/M0_COMPUTE_BUDGET_PLAN.md)
- [Bootstrap reconnaissance and gap report](docs/BOOTSTRAP_RECONNAISSANCE.md)

## Local setup

M0 uses only the Python standard library. Python 3.10 or later is required; Python 3.11–3.13 is the preferred range for later scientific-library compatibility. Create an isolated environment when subsequent milestones introduce pinned dependencies.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_bootstrap.py
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
