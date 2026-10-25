# Independent relevance benchmark protocol

**Status: proposed design; collection and annotation have not started.** The targets below are protocol choices, not achieved sample sizes or results.

## Benchmark unit and target size

The unit of analysis is a **task query**. Each query is paired with a frozen pool of candidate dataset snapshots; each task–candidate pair receives two independent ordinal relevance judgments and separate assessability and constraint judgments.

Proposed target:

| Item | Proposed target |
|---|---:|
| Distinct task briefs | 36 |
| Modality coverage | 12 text, 12 tabular, 12 image |
| Task-type coverage | 14 classification, 8 regression, 7 clustering, and 7 detection tasks; use the modality/type allocation below |
| Candidates per task | 36 |
| Task–candidate pairs | 1,296 |
| Independent first-pass judgments | 2,592 (two per pair) |
| Splits by task | 12 train, 6 development, 18 held-out test |

The split is modality-stratified: 4/2/6 tasks per modality in train/development/test. Task types are balanced as far as the public task frame permits. Thirty-six tasks provide more query-level units than M8's eight, but 18 held-out tasks (six per modality) are still a small basis for uncertainty estimates. Intervals and per-task results remain essential; this design does not establish broad generalizability or high statistical power.

Use the template's preregistered seeds for deterministic task-frame sampling, stratified split assignment, and source-stratified candidate fill. The exact source-frame snapshot and ordered eligible task IDs must be frozen before applying the sampling seed; a seed alone cannot reconstruct a changing external catalogue.

At an estimated 2.5 minutes per first-pass pair judgment, 2,592 judgments require about 108 assessor-hours total, roughly 54 hours per assessor. Reserve approximately 12–18 additional hours for adjudication, calibration, and quality checks. These are planning estimates, not observed times. Confirm this assessor budget before collection. If it is unavailable, amend and freeze a smaller design before collection; do not silently shrink the test set after seeing labels.

## Task sampling

Build a task frame from public, dated ML problem statements and benchmark/task catalogues. Before querying any recommender, two curators independently identify task briefs, remove duplicates, and record the source URL, retrieval date, short rationale, and task-family grouping. Sample 36 task briefs from predeclared strata spanning:

- text, tabular, and image inputs;
- classification, regression, clustering, and detection tasks;
- multiple domains, target structures, and scale constraints within each modality.

Use this proposed task-type allocation, which totals the target counts:

| Modality | Classification | Regression | Clustering | Detection | Total |
|---|---:|---:|---:|---:|---:|
| Text | 4 | 3 | 3 | 2 | 12 |
| Tabular | 5 | 3 | 2 | 2 | 12 |
| Image | 5 | 2 | 2 | 3 | 12 |
| **Total** | **14** | **8** | **7** | **7** | **36** |

Task briefs must be materially distinct from the eight M8 task specifications and must not reuse M8 task text or benchmark labels. Do not use the N=3 card pilot as a query source or relevance reference. Curators record all eligible briefs and deterministic selection seeds; if a stratum lacks enough eligible tasks, report that limitation and revise the proposed counts before any candidate rankings or annotations are examined. The current system consumes structured `TaskSpecification` objects; a curator may produce the structured form, but no unimplemented natural-language parser is part of this benchmark.

## Candidate collection, identity, and freeze

1. Declare permitted public catalogue sources and access rules before acquisition. Prefer public API/catalog metadata and dataset documentation; do not fetch full dataset payloads unless separately authorized and justified. Cache each permitted response and record request configuration, source, retrieval timestamp, software version, and response hash. Stop on authentication or access restrictions rather than bypassing them.
2. Create a frozen, versioned catalogue snapshot. For each task, curators first select **18 candidates independently of retrieval outputs** using a query-relevant but ranking-blind source-stratified screening process: six candidates from each of three source strata defined before collection (general dataset repositories, institutional/domain repositories, and curated benchmark/challenge catalogues). Record the frame, strata, seed, selection rules, and all screened/selected IDs. Then run BM25, dense MiniLM, and RRF independently against the same frozen snapshot and predeclared query representation, retaining each method’s top 6. Form the deduplicated union of the 18 independent candidates and up to 18 retrieval candidates. If overlaps leave fewer than 36 unique candidates, fill remaining slots using the same ranking-blind source-stratified procedure. This makes at least half of the proposed pool independent of the methods being evaluated. Retain distinct mirrors/derivatives as candidates and assign a shared family identifier when supported by documented provenance. If fewer than 36 eligible records exist in the frozen snapshot, freeze the smaller pool and report the count; do not substitute after seeing judgments.
3. Exclude the 24 M8 candidate records and their exact source-ID/version duplicates from the primary Phase II pools. Preserve distinct derivative records only when their provenance justifies treating them as separate candidates, and flag their family relation. Do not reuse any M8 task specification as a Phase II task.
4. Identify each candidate by stable source name, native source ID, dataset version/revision if available, canonical source URL, and a snapshot hash. Keep source identity separate from a deduplication/family key. A changed version or changed source record creates a new snapshot ID. Document cross-catalog aliases and suspected mirrors rather than silently merging them.
5. Freeze the task list, candidate pool membership, source packets, query strings, retrieval outputs, candidate family links, schema version, configurations, seeds, and all content hashes before annotation begins. Record exclusions and access failures with reason codes. No post-annotation candidate substitutions.

The pool intentionally includes some retrieval-generated candidates, so even with a substantial independent half, retrieval methods influence part of the judged pool. Report **judged-pool coverage** only: retrieved relevant items among independently judged relevant items present in the frozen pool. State the pool’s mixed construction beside the metric; do not interpret method differences as unbiased catalog-recall estimates. The design does not estimate relevance of unjudged datasets outside the pool and cannot support live-discovery or web-scale recall claims.

## Train/development/test separation

Split at the task level before candidate ranking and annotation: 12 train, 6 development, and 18 test tasks, stratified by modality (4/2/6 per modality). Freeze the split from the ordered eligible task frame with the preregistered seed before running retrieval methods. Keep semantically equivalent task briefs and near-duplicate benchmark variants in the same split. Where the candidate frame permits, keep dataset families disjoint across splits; if that cannot be achieved without materially distorting task pools, record all cross-split family overlap before fitting and provide an additional family-disjoint sensitivity analysis. Do not use test labels, disagreements, or metric outcomes for feature selection, hyperparameter selection, thresholds, or stopping.

Train labels may be used only to fit the prespecified ranker. Development labels may select its regularization value and verify the evaluation pipeline. Keep test judgments under an independent assessor/custodian; before final evaluation, publish/commit the test-manifest and protocol hashes while keeping the test labels inaccessible to model developers. Open test labels once after code, features, baseline settings, exclusions, and analysis script are frozen. Release the labels and adjudication records after evaluation with appropriate assessor privacy protections and provenance.

## Blind annotation and independence

Recruit two assessors who did not implement the Phase I ranking, author the task/query set, or select candidates using the ranking outputs. Use a third independent adjudicator for disagreements. If the team cannot recruit independent assessors, pause and revise this protocol; do not relabel project-author judgments as independent.

For each pair, provide the task brief and a standardized evidence packet made from public source documentation, metadata snapshots, bounded sample observations only where allowed, and provenance links. Hide all system rankings, scores, recommendation cards, method names, rank positions, training/development/test labels, and the reason a candidate entered the pool. Randomize candidate order separately for each assessor and task. Assessors may not search for model outputs; any supplementary source investigation must be logged and applied equally under the rubric. Capture the assessor's relevance grade, assessability, mandatory-constraint state, short rubric-grounded reason, and sources consulted. Do not collect names or unnecessary personal data; use pseudonymous assessor IDs.

## Missing evidence and eligibility

Assess relevance, evidence sufficiency, and eligibility as distinct fields. `Unknown` or unavailable documentation is not an automatic relevance grade of 0. Use `unassessable` when the packet and permitted source review cannot support a relevance judgment; record why and include the pair in assessability reporting. A failed request or inaccessible source is recorded as a provenance/access failure, not as a negative fact about the dataset. Preserve conflicting source claims and mark the conflict; do not choose the favorable claim without evidence.

For every explicit mandatory task constraint, independently record `satisfied`, `violated`, `unknown`, or `not_applicable` with cited evidence. Freeze each task's constraint policy before candidate ranking: a confirmed violation makes a candidate `ineligible_confirmed_violation`; an unknown property remains eligible as `eligible_with_unknown` unless the task explicitly requires that property to be verified, in which case it is `ineligible_unverified_required`. A post-adjudication unresolved eligibility state is `unresolved` and excluded from primary eligible-pool denominators, but its count is reported. These distinctions apply uniformly to every method. Relevance is judged separately even for ineligible candidates so the study can report relevant-but-ineligible cases. Gate-off comparisons are offline diagnostic shadows only and may not issue user-facing recommendation cards or promote known-ineligible records.

## Adjudication and reliability

Compute agreement from the two untouched first-pass labels before adjudication. For ordinal relevance, calculate quadratic-weighted Cohen's kappa on pairs both assessors marked assessable; also report the jointly-assessable denominator, raw exact and within-one-grade agreement, grade frequencies, and binary-threshold agreement for grade ≥2. Obtain 95% uncertainty intervals by resampling task clusters, not individual pairs. Report assessability agreement and exact constraint-state agreement separately, including their denominators. If a bootstrap replicate has no variation and kappa is undefined, omit it and report how many replicates were undefined. With only two assessors, do not report a statistic that assumes independent dataset-pair observations.

Send a pair to the third adjudicator if the first relevance grades differ at all, the assessors disagree on assessability, or they disagree on any mandatory-constraint state. The adjudicator sees both rationales but remains blind to method, scores, and rank. Preserve both original judgments and the adjudication as separate records; never overwrite. If more than 25% of pairs require adjudication, pause, inspect rubric ambiguity without opening system scores, revise the protocol, and re-annotate affected material under a new version before proceeding.

## Exclusions and release

Predeclare objective pair exclusions: exact duplicate source snapshots after freeze, corrupted/empty source packets, or an assessor conflict that cannot be resolved under the adjudication guide. Do not exclude a pair because it lowers a system score, is inconvenient, or has an unfavorable judgment. Publish counts and reasons by split, modality, task type, and source. Keep assessor identity private; release pseudonymized ratings only if the consent and review conditions permit. This protocol makes no assumption that participant/pilot data can be reused as benchmark annotation.
