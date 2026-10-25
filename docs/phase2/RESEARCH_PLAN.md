# Phase II research plan

**Status: proposed.** This plan does not report completed Phase II data collection, annotation, training, or evaluation.

## Purpose and boundary

Phase I is the frozen reference implementation and benchmark. Phase II asks whether its fixed heuristic ranking is useful against independent, blinded relevance judgments and whether one small learned ranker improves ranking quality without weakening explicit constraints or exceeding the measured local resource envelope. The benchmark and analysis plan must be frozen before the ranker is implemented or final-test labels are opened.

This is a benchmark-design milestone, not a claim of novelty or permission to change Phase I. Do not edit the approved manuscript, frozen M0–M8 inputs/results, participant files, or production website. Keep future Phase II inputs, manifests, configurations, and results under Phase II-specific paths.

## Audited Phase I baseline

The following are repository-recorded observations, not Phase II targets or guarantees:

| Baseline fact | Source and interpretation |
|---|---|
| M8 has 24 frozen dataset records, 8 structured tasks, 192 task–dataset evaluations, and target set size `k=3`. | [`configs/m8_evaluation.json`](../../configs/m8_evaluation.json), [`data/benchmarks/m8_benchmark_manifest.json`](../../data/benchmarks/m8_benchmark_manifest.json), and the approved paper. M8 starts from the same frozen candidate pool for each task; it does not measure live-discovery recall. |
| The recorded M8 offline recommendation path used 33.11 MiB peak RSS and 327.49 ms wall time, with zero network egress verified. | `experiments/m8/results/m8_summary.json` → `reproducibility.runtime_metrics` and `zero_egress_verified`. These figures are specific to the recorded M8 path and environment. |
| M2's shared benchmark process reached 453.22 MiB peak RSS and its model-load/index-build phase took about 81 seconds. | [`docs/M2_RESULTS.md`](../M2_RESULTS.md) and `experiments/m2/results/benchmark.json`. The process measurement is shared across the retrieval benchmark; it is not attributable to BM25 or any one backend. |
| Ranking weights are fixed heuristic weights. | `src/dataset_intelligence/ranking/scoring.py`; no learned ranking parameters are implemented. R1 is utility-only, R2 is fixed multi-objective scoring, and R3 applies family-aware greedy diversification after hard gates. |
| M8 is not independent relevance validation. | The M8 reference labels were project-authored and informed by the same rubric family as utility. The human-card pilot in [`docs/M8_RESEARCH_FINDINGS.md`](../M8_RESEARCH_FINDINGS.md) is descriptive, N=3, and has a presentation-order confound. It is not Phase II relevance ground truth. |
| R3's selector is greedy, but no formal submodularity property or approximation guarantee is established. | `src/dataset_intelligence/ranking/diversification.py` and the approved paper. Describe it as family-aware greedy diversification only. |

The old `docs/M8_EVALUATION.md` contains historical status text that predates the committed M8 execution. Use the committed M8 manifest/configuration, machine-readable summary, final findings, and approved paper for the frozen baseline; do not copy its stale “not yet created” status into new claims.

## Proposed research questions

**RQ1 — Independent ranking quality.** On a frozen, independently judged candidate pool, does one regularized pairwise linear ranker trained on development queries improve held-out graded relevance ranking over the frozen Phase I R3 recommendation order?

**RQ2 — Evidence feature contribution.** Does adding the existing evidence-support feature to that same pairwise model improve held-out relevance ranking over the identical model trained without that feature?

**RQ3 — Candidate coverage and safety.** How much of the independently judged relevant candidate pool is represented by BM25, dense MiniLM, and reciprocal-rank fusion, and how often do gate-on recommendation outputs violate adjudicated mandatory constraints?

RQ3 is descriptive and pool-bounded. A fixed, judged pool cannot establish recall over all public datasets or web-scale discovery.

## Proposed learned-ranking path

Use **one query-grouped pairwise logistic linear ranker** as the Phase II learned method. For a candidate feature vector `x`, its score is `w · x`; for a labeled pair `i,j`, model `P(i > j) = sigmoid(w · (x_i − x_j))` when `i` has the higher relevance grade. Construct pairs only when adjudicated ordinal grades differ; add the reverse signed-difference example with the opposite binary target. Normalize features using training data only, weight each task's pairwise loss to contribute equally, and select regularization on the development split. Do not use task or dataset identifiers as features or treat the many within-query pairs as independent observations. The evaluation protocol specifies the proposed regularization grid and deterministic tie rule.

The initial feature set is the five existing `CandidateSignals` in `src/dataset_intelligence/ranking/signals.py`: fit, utility, evidence support, content coverage, and risk penalty. All five are bounded deterministic values already consumed by R2/R3. Popularity is excluded. The pre-registered evidence ablation removes only `evidence_support_score`; all other feature computation, training pairs, split, and tuning rules stay fixed. A feature must be available at recommendation time, computed without relevance labels, and versioned before use.

This deliberately favors a small, auditable model over LambdaMART: the proposed labeled sample is modest at the task level, and the current ranker inputs are five tabular signals. `requirements.txt` pins scikit-learn, although `pyproject.toml` does not declare it as a direct dependency. If the implementation uses it, declare it directly and measure the isolated process RSS; the Phase I 128 MiB ceiling is an empirical limit to check, not an assumed pass. A tree ensemble would add model capacity and tuning degrees of freedom before there is evidence that the available independent task groups support them. This is a protocol recommendation only; no ranker or dependency change is made here.

## Status language

- **Implemented:** Phase I structured task specifications, source adapters, evidence states, hard gates, utility components, candidate signals, BM25/dense/RRF baselines, R1/R2/R3, and frozen M8 evaluation artifacts.
- **Proposed here:** 36 new task briefs, 36 candidates per task, relevance rubric, blinded dual annotation, 12/6/18 task split, evaluation metrics, and one pairwise linear ranker.
- **Requires human work:** task/query curation, candidate-source review, two independent annotations per pair, reliability reporting, disagreement adjudication, and test-set custody.
- **Future evaluation:** baseline comparison, the one learned-ranker comparison, gate/evidence ablations, uncertainty intervals, and resource measurements.

No Phase II result, judgment, or performance improvement is claimed in this package.
