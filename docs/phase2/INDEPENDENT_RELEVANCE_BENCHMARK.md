# Independent relevance benchmark protocol

**Status: proposed design; collection and annotation have not started.** The targets below are protocol choices, not achieved sample sizes or results.

## Benchmark unit and target size

The unit of analysis is a **task query**. Each query is paired with a frozen pool of candidate dataset snapshots; each task–candidate pair receives two independent ordinal relevance judgments and separate assessability and constraint judgments.

Proposed target:

| Item | Proposed target |
|---|---:|
| Distinct task briefs | 30 |
| Modality coverage | 10 text, 10 tabular, 10 image |
| Task-type coverage | 12 classification, 6 regression, 6 clustering, and 6 detection tasks; use the modality/type allocation below |
| Candidates per task | 36 |
| Task–candidate pairs | 1,080 |
| Independent first-pass judgments | 2,160 (two per pair) |
| Splits by task | 12 train, 6 development, 12 held-out test |

The split is modality-stratified: 4/2/4 tasks per modality in train/development/test. Task types are balanced as far as the public task frame permits. Thirty tasks are intended to provide more query-level units than M8's eight, while 36 candidates per task allow a union of three retrieval top-10 lists plus up to six independently sourced candidates. This is still a modest study; uncertainty may remain wide and no power claim is made.

Use the template's preregistered seeds for deterministic task-frame sampling, stratified split assignment, and source-stratified candidate fill. The exact source-frame snapshot and ordered eligible task IDs must be frozen before applying the sampling seed; a seed alone cannot reconstruct a changing external catalogue.

At an estimated 2.5 minutes per first-pass pair judgment, 2,160 judgments require about 90 assessor-hours total, roughly 45 hours per assessor. Reserve approximately 10–15 additional hours for adjudication, calibration, and quality checks. These are planning estimates, not observed times. If the budget is unavailable, reduce the benchmark before collection and amend/freeze the protocol; do not silently shrink the test set after seeing labels.

## Task sampling

Build a task frame from public, dated ML problem statements and benchmark/task catalogues. Before querying any recommender, two curators independently identify task briefs, remove duplicates, and record the source URL, retrieval date, short rationale, and task-family grouping. Sample 30 task briefs from predeclared strata spanning:

- text, tabular, and image inputs;
- classification, regression, clustering, and detection tasks;
- multiple domains, target structures, and scale constraints within each modality.

Use this proposed task-type allocation, which totals the target counts:

| Modality | Classification | Regression | Clustering | Detection | Total |
|---|---:|---:|---:|---:|---:|
| Text | 3 | 2 | 3 | 2 | 10 |
| Tabular | 4 | 3 | 2 | 1 | 10 |
| Image | 5 | 1 | 1 | 3 | 10 |
| **Total** | **12** | **6** | **6** | **6** | **30** |

Task briefs must be materially distinct from the eight M8 task specifications and must not reuse M8 task text or benchmark labels. Do not use the N=3 card pilot as a query source or relevance reference. Curators record all eligible briefs and deterministic selection seeds; if a stratum lacks enough eligible tasks, report that limitation and revise the proposed counts before any candidate rankings or annotations are examined. The current system consumes structured `TaskSpecification` objects; a curator may produce the structured form, but no unimplemented natural-language parser is part of this benchmark.

## Candidate collection, identity, and freeze

1. Declare permitted public catalogue sources and access rules before acquisition. Prefer public API/catalog metadata and dataset documentation; do not fetch full dataset payloads unless separately authorized and justified. Cache each permitted response and record request configuration, source, retrieval timestamp, software version, and response hash. Stop on authentication or access restrictions rather than bypassing them.
2. Create a frozen, versioned catalogue snapshot. For each task, collect the top 10 candidates from each of BM25, dense MiniLM, and RRF, run against the same snapshot and predeclared query representation. Add up to six candidates from a query-independent, source-stratified catalogue-screening procedure performed by curators who do not see system rankings. Deduplicate exact same-source ID/version repeats, then form the union; retain distinct mirrors/derivatives as candidates and assign a shared family identifier when supported by documented provenance. Fill toward 36 using the same prespecified source-stratified procedure. If fewer than 36 eligible records exist, freeze the smaller pool and report the count; do not substitute after seeing judgments.
3. Exclude the 24 M8 candidate records and their exact source-ID/version duplicates from the primary Phase II pools. Preserve distinct derivative records only when their provenance justifies treating them as separate candidates, and flag their family relation. Do not reuse any M8 task specification as a Phase II task.
4. Identify each candidate by stable source name, native source ID, dataset version/revision if available, canonical source URL, and a snapshot hash. Keep source identity separate from a deduplication/family key. A changed version or changed source record creates a new snapshot ID. Document cross-catalog aliases and suspected mirrors rather than silently merging them.
5. Freeze the task list, candidate pool membership, source packets, query strings, retrieval outputs, candidate family links, schema version, configurations, seeds, and all content hashes before annotation begins. Record exclusions and access failures with reason codes. No post-annotation candidate substitutions.

The pool intentionally includes retrieval-generated candidates. Consequently, report **judged-pool coverage** only: retrieval coverage against independently judged relevant items present in the frozen pool. The design does not estimate the number or relevance of datasets outside the collected snapshot/pool and cannot support live-discovery or web-scale recall claims.

## Train/development/test separation

Split at the task level before annotation: 12 train, 6 development, and 12 test tasks, stratified by modality (4/2/4 per modality). Keep semantically equivalent task briefs and near-duplicate benchmark variants in the same split. Where the candidate frame permits, keep dataset families disjoint across splits; if that cannot be achieved without materially distorting task pools, record all cross-split family overlap before fitting and provide an additional family-disjoint sensitivity analysis. Do not use test labels, disagreements, or metric outcomes for feature selection, hyperparameter selection, thresholds, or stopping.

Train labels may be used only to fit the prespecified ranker. Development labels may select its regularization value and verify the evaluation pipeline. Keep test judgments under an independent assessor/custodian; before final evaluation, publish/commit the test-manifest and protocol hashes while keeping the test labels inaccessible to model developers. Open test labels once after code, features, baseline settings, exclusions, and analysis script are frozen. Release the labels and adjudication records after evaluation with appropriate assessor privacy protections and provenance.

## Blind annotation and independence

Recruit two assessors who did not implement the Phase I ranking, author the task/query set, or select candidates using the ranking outputs. Use a third independent adjudicator for disagreements. If the team cannot recruit independent assessors, pause and revise this protocol; do not relabel project-author judgments as independent.

For each pair, provide the task brief and a standardized evidence packet made from public source documentation, metadata snapshots, bounded sample observations only where allowed, and provenance links. Hide all system rankings, scores, recommendation cards, method names, rank positions, training/development/test labels, and the reason a candidate entered the pool. Randomize candidate order separately for each assessor and task. Assessors may not search for model outputs; any supplementary source investigation must be logged and applied equally under the rubric. Capture the assessor's relevance grade, assessability, mandatory-constraint state, short rubric-grounded reason, and sources consulted. Do not collect names or unnecessary personal data; use pseudonymous assessor IDs.

## Missing evidence and eligibility

Assess relevance, evidence sufficiency, and eligibility as distinct fields. `Unknown` or unavailable documentation is not an automatic relevance grade of 0. Use `unassessable` when the packet and permitted source review cannot support a relevance judgment; record why and include the pair in assessability reporting. A failed request or inaccessible source is recorded as a provenance/access failure, not as a negative fact about the dataset. Preserve conflicting source claims and mark the conflict; do not choose the favorable claim without evidence.

For every explicit mandatory task constraint, independently record `satisfied`, `violated`, `unknown`, or `not_applicable` with cited evidence. A candidate whose known license/access terms violate a mandatory constraint is ineligible for the gate-on recommendation list regardless of relevance grade. An unknown mandatory property remains distinct from a confirmed violation; the system must follow the task's explicit evidence requirement and abstain/exclude when the requirement demands verified compliance. Gate-off comparisons are offline diagnostic shadows only and may not issue recommendation cards or promote known-ineligible records.

## Adjudication and reliability

Compute agreement from the two untouched first-pass labels before adjudication. For ordinal relevance, calculate quadratic-weighted Cohen's kappa on pairs both assessors marked assessable; also report the jointly-assessable denominator, raw exact and within-one-grade agreement, grade frequencies, and binary-threshold agreement for grade ≥2. Obtain 95% uncertainty intervals by resampling task clusters, not individual pairs. Report assessability agreement and exact constraint-state agreement separately, including their denominators. If a bootstrap replicate has no variation and kappa is undefined, omit it and report how many replicates were undefined. With only two assessors, do not report a statistic that assumes independent dataset-pair observations.

Send a pair to the third adjudicator if the first relevance grades differ at all, the assessors disagree on assessability, or they disagree on any mandatory-constraint state. The adjudicator sees both rationales but remains blind to method, scores, and rank. Preserve both original judgments and the adjudication as separate records; never overwrite. If more than 25% of pairs require adjudication, pause, inspect rubric ambiguity without opening system scores, revise the protocol, and re-annotate affected material under a new version before proceeding.

## Exclusions and release

Predeclare objective pair exclusions: exact duplicate source snapshots after freeze, corrupted/empty source packets, or an assessor conflict that cannot be resolved under the adjudication guide. Do not exclude a pair because it lowers a system score, is inconvenient, or has an unfavorable judgment. Publish counts and reasons by split, modality, task type, and source. Keep assessor identity private; release pseudonymized ratings only if the consent and review conditions permit. This protocol makes no assumption that participant/pilot data can be reused as benchmark annotation.
