# Repository Working Agreement

## Source of truth

`docs/PROJECT_SPEC.md` and `docs/RESEARCH_FOUNDATION.md` govern scope and research claims. The versioned proposal documents under `docs/v1`, `docs/v2`, and `docs/v3` are preserved research history and should not be reformatted or regenerated during implementation work.

## Engineering boundaries

- Implement one roadmap milestone at a time; do not begin the next milestone without completing and reporting the current one.
- Keep each source adapter inside `src/dataset_intelligence/ingestion/`; native source fields must be preserved as provenance and must not leak into ranking interfaces.
- Canonical fields, evidence claims, observations, and derived scores must be separate objects when those modules are introduced.
- Model missing information explicitly. `Unknown`, `Single-source claim`, `Measured`, `Corroborated`, and `Conflicting` are distinct states.
- Treat bounded sample results as scoped observations, not full-dataset facts. Treat license metadata as a claim, not legal advice.
- Popularity may be recorded as context but must not enter the core suitability term.
- Cache remote responses and record configurations, seeds, versions, and observation timestamps for every experiment.

## Git and verification

- Use small, coherent commits and inspect `git diff --check` plus the staged diff before each commit.
- Do not rewrite history or modify unrelated files.
- Run the relevant tests before committing. Push only when a remote is configured and the milestone is complete.
