# Phase II research design

**Status: proposed protocol. No Phase II benchmark data, annotations, trained models, or evaluation results exist.**

This package describes a future independent relevance study for the evidence-driven dataset recommendation system. It does not authorize data collection, assessor recruitment, annotation, model fitting, or held-out evaluation.

- [Research plan](RESEARCH_PLAN.md) — research questions, baseline scope, and proposed comparisons.
- [Independent relevance benchmark](INDEPENDENT_RELEVANCE_BENCHMARK.md) — task and candidate sampling, two study-size alternatives, annotation custody, and workload scenarios.
- [Judgment rubric](JUDGMENT_RUBRIC.md) — relevance grades, assessability, constraint judgments, calibration examples, and packet corrections.
- [Evaluation protocol](EVALUATION_PROTOCOL.md) — native Track A and oracle-filtered Track B, proposed metrics, and statistical decision rules.
- [Roadmap](ROADMAP.md) — proposed approval gates and future work.

The primary learned-static versus frozen R2-static comparison, optional normalized selector, study size, and statistical analysis remain proposals requiring author and supervisor approval. Both 36 tasks × 36 candidates and 36 tasks × 24 candidates remain under consideration. The proposed H1 cluster bootstrap is also subject to approval. Agreement-statistics weighting and uncertainty estimation remain unresolved.

**Scope of this PR:** PR #5 establishes the proposed research and evaluation design. It does not include or approve executable Phase II tooling. A separate future implementation review may cover manifest design, structural and cross-record validation, annotation lifecycle support, candidate-pool replay, native R2/R3 fidelity, bootstrap verification, custody and reviewer authorization, and public-release claim verification. No implementation or verification capability is implied by this document package.

Before any study proceeds, authors and the supervisor must approve the protocol and sample-size option, statistical plan, source permissions, independent assessor and adjudicator arrangements, reviewer and custodian authority, consent/privacy and retention rules, and available resources. Public release must use an externally authorized review process; matching hashes or self-declared manifest roles alone cannot establish approval authenticity.
