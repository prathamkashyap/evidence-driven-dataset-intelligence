# Bootstrap Reconnaissance and Implementation Gap Report

Date: 2026-09-02

## Repository state discovered

At the start of M0, this directory contained only project/research documentation: the two authoritative documents at `docs/PROJECT_SPEC.md` and `docs/RESEARCH_FOUNDATION.md`, plus historical proposal material under `docs/v1`, `docs/v2`, and `docs/v3`. It contained no application code, package manifest, dependency lockfile, tests, CI workflow, scripts, README, Git metadata, branch, or Git remote. A new local Git repository was initialized on `main` for this bootstrap work. There is no configured GitHub remote, so no push can be attempted yet.

The versioned proposal files are related research history, not unrelated work. They are preserved untouched. System `.DS_Store` files are unrelated and will be ignored.

## Comparison with the specification

| Area | Existing | Gap / M0 decision |
|---|---|---|
| Research direction | Complete implementation specification and research foundation | Reuse as governing documents; do not replace with generic LLM/RAG scope. |
| Repository conventions | No code conventions or Git history | Add a short working agreement and a minimal Python project configuration. |
| Ingestion and canonical schema | Absent | M1; isolate adapters and preserve native provenance. |
| Retrieval | Absent | M2; measure candidate-pool cost first. |
| Evidence ledger/resolution | Absent | M3; retain explicit unknown/conflict states. |
| Sample analysis and probes | Absent | M4–M5; M0 only defines cost measurement. |
| Long-tail, ranking, explanations | Absent | M6–M7; no implementation during bootstrap. |
| Evaluation | Absent | M0 defines an efficiency experiment; full benchmark/evaluation is M8. |
| Tests and CI | Absent | Add only bootstrap configuration checks now; defer CI choice until the GitHub remote exists. |

## Reuse and preservation

Reuse the authority, terminology, architecture, roadmap, metrics, and caveats in the two root documentation files. Preserve all files under `docs/v1`, `docs/v2`, and `docs/v3`; M0 does not alter proposal PDFs, Word files, TeX, or historical Markdown.

## Contradictions and decisions

There is no contradiction between the existing materials and the specification. The prescribed 50–100 candidate pool is explicitly a starting hypothesis, not a fixed implementation setting. The discovered interpreter is Python 3.14, while later scientific dependencies may lag it; M0 therefore has no third-party runtime dependencies and recommends Python 3.11–3.13 when M1 introduces the scientific stack. A GitHub remote/branch policy must be provided or configured before this local repository can push.
