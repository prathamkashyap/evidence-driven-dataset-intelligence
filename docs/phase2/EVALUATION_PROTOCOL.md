# Phase II evaluation protocol

**Status: proposed; no metrics, model fits, or experiments have been run.** Freeze this document, the manifest, feature code/configuration, and analysis scripts before opening the final test labels.

## Comparisons and ranking conditions

BM25, dense MiniLM, and RRF candidate generation run against the same frozen catalogue snapshot and task/query representation. Downstream ranking comparisons use the same frozen per-task judged pool and structured task specification. Candidate retrieval and recommendation ranking are reported as separate stages. Use the observed Phase I implementations without changing their formulas:

1. BM25 (`bm25-v1`), dense MiniLM, and reciprocal-rank fusion for candidate retrieval. Record top-10 lists against the versioned catalogue snapshot. For ranking metrics, also score/order the common judged pool with each frozen retrieval scoring function. Dense retrieval is optional and outside the M0 memory envelope in the recorded M2 shared-process measurement; pin the exact model revision/checksum before use, run with cached weights, and report its costs separately.
2. Frozen Phase I R1 utility-only, R2 fixed multi-objective score, and R3 family-aware greedy selection, with hard compatibility gates active and original scoring/configuration. R1/R2 full rankings come from their existing score order; obtain a longer R3 order by continuing the same frozen greedy rule over eligible candidates. Report the actual production target set separately at `k=3`.
3. One proposed pairwise linear ranker trained only on train labels; regularization selected on development labels. It receives only the prespecified Phase I signals and does not use dataset IDs, popularity, final test labels, or annotator decisions as input features.

Use identical task-specific mandatory constraints and independent eligibility records. Do not adjust thresholds on test data. Before producing recommendation rankings, apply hard gates. Rankers see only candidates that pass the primary eligibility policy. A candidate known to violate a mandatory constraint is never emitted in the gate-on output.

For pairwise logistic fitting, use `P(i > j) = sigmoid(w · (x_i − x_j))` for each within-task pair with unequal adjudicated grade, where `i` is the higher-grade candidate. Include the reverse signed difference with target 0 for each target-1 pair. Standardize each feature from the training split only; assign each task equal total loss weight regardless of its number of non-tied pairs. Fit an L2-regularized logistic regression with no intercept, fixed solver and tolerance recorded in the run configuration, and the template's preregistered model seed. Select inverse regularization strength `C` from `{0.01, 0.1, 1, 10}` by highest macro development nDCG@10; break ties by choosing the smallest `C` (strongest regularization). After selection, refit once on train plus development labels with the chosen `C` and feature normalization recomputed on train plus development. A task with no unequal assessable training pair contributes no pairwise loss and is reported; stop learned-model work if fewer than 8 of the 12 train tasks contribute pairs. If every development nDCG is undefined or the feature/model fit fails, report that the proposed learned path is infeasible under this protocol and do not open test labels. No other model family, feature search, threshold tuning, or test-set stopping is permitted.

### Gate-on/off diagnostic

Run a controlled offline shadow ablation on the same candidates and ranking scores. Compare the primary gate-on result with a gate-disabled ranking solely to diagnose the effect of excluding confirmed violations. The gate-off branch must not produce user-facing cards, be treated as an eligible recommendation, or be used as a deployable baseline. Report confirmed-violation rate and unknown mandatory-constraint rate separately. No prohibited or access-restricted candidate is promoted for demonstration.

### Evidence feature ablation

Train the same pairwise linear model twice under the same split, task weights, optimization, and development selection procedure: (a) five Phase I signals; (b) four signals with `evidence_support_score` omitted. This is the registered test of incremental evidence-support feature value. It is not a causal estimate of the entire evidence subsystem.

## Metrics and denominators

The task is the independent analysis unit. Pair-level annotations within a task are not treated as independent samples.

### Primary metric

**Macro nDCG@10** on the held-out test tasks, using graded gain `2^grade − 1` for relevance grades 0–3 and discount `log2(rank + 1)`. Rank only eligible candidates in the gate-on comparison. For metric calculation only, an unassessable candidate receives no gain and still occupies its returned position; the annotation remains unassessable, not grade 0. Compute ideal DCG from assessable, eligible candidates in the frozen pool. A task with no positive eligible relevance grade has undefined nDCG and is excluded from the macro denominator, with its count and reason reported. Report assessability and eligible-pool coverage beside nDCG, plus a sensitivity analysis over assessable items that preserves their original rank positions.

Average query-level nDCG equally across evaluable test tasks (macro, not pair-micro). Also provide per-task values and the number of tasks with undefined denominators. The primary contrast is the paired query-level difference between the learned linear ranker and frozen R3.

### Secondary ranking metrics

- **Recall@3 and Recall@10:** number of eligible candidates with grade ≥2 in the top `k`, divided by all eligible grade-≥2 candidates in that task's judged pool. If the denominator is zero, report N/A and the task count; do not assign perfect recall.
- **Precision@3 and Precision@10:** relevant eligible candidates (grade ≥2) in the top positions divided by `min(k, number of eligible candidates)`. Unassessable positions add no relevant hit and are included in the denominator.
- **MRR@10:** reciprocal rank of the first eligible grade-≥2 candidate within ten; zero if relevant candidates exist in the pool but none appears in the top ten; N/A if the task has no relevant eligible candidate in its pool.
- **Candidate retrieval coverage:** for each retrieval method, report eligible grade-≥2 candidates it returns at 10 divided by eligible grade-≥2 candidates in that task's frozen judged pool. Label this **judged-pool recall**, list the pool construction and denominator, and explicitly state that it is not full-catalog or live-discovery recall.
- **Top-3 recommendation set:** report set-level graded precision/recall at 3, average relevance grade, family redundancy (same-family pairs / all selected pairs), source/family coverage, and Phase I attribute diversity. If fewer than three eligible candidates exist, use the number returned as denominator and report the shortfall.

### Constraint, evidence, and provenance measures

- **Confirmed mandatory-constraint violation rate:** returned top-3 candidates adjudicated `violated` for any applicable mandatory constraint divided by top-3 outputs with an assessable constraint state. The gate-on target is zero violations; if the denominator is empty, report N/A. Report `unknown` states separately and never count them as confirmed violations.
- **Evidence support:** among top-3 candidates, report the proportion of applicable task-critical facets whose evidence state/source is present and consistent with the independent packet, along with missing/unknown/conflicting counts. No calibrated confidence interpretation.
- **Provenance traceability:** report source-reference coverage (claims with a resolvable source ID/URI and observation timestamp / claims requiring provenance) and a blinded source audit of a prespecified 20% sample of output claim references. Report both coverage and sampled support correctness; do not collapse them into a single trust score.
- **Diversity/redundancy:** report mean pairwise attribute distance under the frozen Phase I definition and same-family redundancy rate. Keep relevance separate; more diversity is not inherently better if relevance falls.

### Efficiency

For each method, record wall time, peak process RSS, environment, software/package/model versions, warm/cold state, cache state, seed, and network-egress observation. Measure candidate acquisition/index construction separately from per-query ranking and report end-to-end totals. Use isolated runs when comparing memory; do not assign M2's shared 453.22 MiB to a single retrieval backend. Compare the M8 33.11 MiB/327.49 ms only as its own frozen recorded path. Report whether Phase II runs meet or exceed the 128 MiB and 20-second M0 design ceilings without treating those ceilings as proof of quality.

## No-relevant and missing-evidence rules

Never convert `unassessable` to a human relevance grade of zero. For ranking metrics, it receives no gain but remains at its original rank position; report its frequency and a sensitivity analysis. If a task has no assessable, eligible positive grade, metrics whose denominator requires positives are N/A. Do not silently drop the task or count it as a successful result. Report access failures and unknown mandatory constraints separately from confirmed violations.

## Uncertainty and statistical analysis

For every model contrast, compute the metric per held-out task, then the paired difference. Use 10,000 stratified cluster-bootstrap replicates: sample the four test tasks with replacement within each of the three modality strata, recombine 12 task clusters, and recompute the macro difference. Report percentile 95% intervals and all per-task paired differences. The task, not a task–dataset pair or an individual assessor judgment, is the resampling unit. With only 12 proposed test tasks, intervals may be broad; report uncertainty and avoid claims of high power or generalization beyond the sampled task frame.

Report raw primary judgments, weighted agreement, adjudicated values, and assessability separately. Agreement is descriptive of these assessors and tasks. Do not use the N=3 M8 pilot as a prior, training label, or independent benchmark result.

## Preregistered hypotheses and decision rules

All are prospective protocol hypotheses. Thresholds below are design choices, not achieved effects.

- **H1 (primary):** the learned pairwise linear ranker improves macro test nDCG@10 over frozen R3. Treat the result as evidence of a practically meaningful improvement only if the point estimate is at least +0.03 and the paired 95% task-cluster interval excludes 0 in the positive direction. Otherwise report no conclusive evidence for the registered improvement; a negative estimate is reported as a regression.
- **H2 (evidence feature):** the five-signal model exceeds the matched four-signal model on macro test nDCG@10. Report its paired difference and interval as secondary; do not claim an isolated causal benefit from one feature based on a small observational test set.
- **H3 (hard constraints):** the gate-on primary outputs contain zero confirmed mandatory-constraint violations. Any violation fails the safety criterion regardless of relevance metrics. Unknown mandatory constraints are a separate reported rate.
- **H4 (retrieval coverage):** compare judged-pool Recall@10 for BM25, dense MiniLM, and RRF descriptively, with per-task values and paired query-bootstrap intervals. No method-superiority claim unless supported by the registered interval and pool limitations.

Only H1 is confirmatory for the primary outcome. H2/H4 are secondary; no multiplicity-adjusted superiority claims are planned. Do not change thresholds, exclusions, metric definitions, candidate pools, or stopping rules after test labels are opened. Report every registered comparison, including null and negative outcomes.

## Exclusions, seeds, and reproducibility

Before evaluation, freeze and hash the task/candidate manifest, rubric, annotation exports, adjudication file, code revision, configuration, feature definitions, dependency lock, dense-model revision where used, and analysis script. Record seeds and timestamps. Run no final-test experiment until all the above and the decision rules are committed. Apply only predeclared exclusions; publish a flow count by split and reason. No new experiment or benchmark result is created by this protocol PR.
