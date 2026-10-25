# Phase II research design

**Status: proposed protocol; no Phase II benchmark data, annotations, or model results exist.**

This package specifies the next research milestone before any learned ranker or final benchmark is built. It keeps the frozen Phase I artifacts as the baseline and separates proposed choices from completed work.

- [Research plan](RESEARCH_PLAN.md) — questions, baseline audit, scope, and the proposed ranking approach.
- [Independent relevance benchmark](INDEPENDENT_RELEVANCE_BENCHMARK.md) — task and candidate sampling, snapshots, splits, annotation, and budget.
- [Judgment rubric](JUDGMENT_RUBRIC.md) — relevance grades, assessability, constraint judgments, and adjudication.
- [Evaluation protocol](EVALUATION_PROTOCOL.md) — baselines, metrics, hypotheses, ablations, uncertainty, and decision rules.
- [Roadmap](ROADMAP.md) — staged entry and exit criteria.
- [Manifest schema](schemas/benchmark-manifest.schema.json), [empty proposed manifest template](benchmark-manifest.template.json), and the standard-library [cross-record validator](validate_manifest.py).

The files are design artifacts only. The manifest template has no task, candidate, provenance, or annotation rows. Human annotation, dataset collection, model implementation, and experiments remain future work. The validator checks referential integrity and target-count consistency after records are added; it does not replace JSON Schema validation or human provenance review.
