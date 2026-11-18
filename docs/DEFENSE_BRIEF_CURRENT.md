# Current defense brief: Phase I

These short answers are preparation aids, not a replacement for the [reporting corrections](PHASE1_REPORTING_CORRECTIONS.md), frozen results or the [current status](CURRENT_RESEARCH_STATUS.md). The earlier [viva](FINAL_VIVA_EVIDENCE_MAP.md) and [report](FINAL_REPORT_EVIDENCE_MAP.md) maps are historical and contain superseded interpretations.

## 1. What is the contribution?

**Answer:** An implemented, evaluated integration connects source-attributed evidence and bounded observations to hard compatibility gates, heuristic scoring and traceable set selection under a local resource design envelope.

**Evidence:** [Project specification](PROJECT_SPEC.md) · [ranking pipeline](../src/dataset_intelligence/ranking/pipeline.py).

**Qualification / avoid:** Its contribution is integration and characterization, not a novel retrieval algorithm or demonstrated superiority to untested methods.

## 2. What does “evidence-aware” mean?

**Answer:** Source-specific observations retain their state and provenance; resolution describes relations among entries. Bounded fingerprints describe the sample actually inspected.

**Evidence:** [Evidence states](../src/dataset_intelligence/evidence/statuses.py) · [M3 results](M3_RESULTS.md).

**Qualification / avoid:** Agreement is not calibrated confidence or proof that sources are independent; formal resolution records are not directly consumed as a ranking feature.

## 3. How should missing information and licenses be interpreted?

**Answer:** Unknown, unsupported and failed observations are represented separately; a missing claim is not automatically a confirmed incompatibility. A license field is a source claim used by a rule, not legal advice.

**Evidence:** [Project specification](PROJECT_SPEC.md) · [gates](../src/dataset_intelligence/utility/estimator.py).

**Qualification / avoid:** Do not claim gate accuracy or full-dataset properties from metadata and bounded samples.

## 4. What does the M2 comparison establish?

**Answer:** M2 compared lexical, MiniLM and hybrid retrieval on ten development records and four queries. All recorded the same recall on its small source-derived relevance set.

**Evidence:** [M2 results](../experiments/m2/results/benchmark.json) · [reporting corrections](PHASE1_REPORTING_CORRECTIONS.md#m2-retrieval-and-resource-measurements).

**Qualification / avoid:** Fixed method order, single calls and shared-process state preclude a controlled dense-versus-hybrid latency claim; relevance labels were not independently adjudicated.

## 5. Did the implementation meet its resource envelope?

**Answer:** M8 recorded 33.11 MiB process-lifetime peak RSS and a 327.49 ms eight-task timed harness interval. M2's shared process recorded 453.22 MiB, above the 128 MiB design ceiling.

**Evidence:** [M8 resources](PHASE1_REPORTING_CORRECTIONS.md#m8-harness-timing-offline-policy-and-replay) · [M2 artifact](../experiments/m2/results/benchmark.json).

**Qualification / avoid:** Suite time is not per-task recommendation latency; M2's shared RSS is not a backend-specific peak. Do not generalize to unmeasured machines or upstream workloads.

## 6. What do hard gates do?

**Answer:** Confirmed modality mismatch, prohibited license claims and required anonymous access on a gated source can exclude a candidate before ranking. In unperturbed M8, 140 of 192 pairs were excluded by modality; license and access gates did not activate.

**Evidence:** [Gating](../src/dataset_intelligence/utility/estimator.py) · [M8 summary](../experiments/m8/results/m8_summary.json).

**Qualification / avoid:** The observed activations do not establish independently measured false-accept or false-reject rates.

## 7. Why use fixed weights, and are they robust?

**Answer:** The implementation uses transparent, hand-specified heuristic weights. The recorded diversity-weight sweep reached the selector and changed some sets.

**Evidence:** [Sensitivity correction](PHASE1_REPORTING_CORRECTIONS.md#m8-utility-reference-labels-and-sensitivity) · [selector](../src/dataset_intelligence/ranking/diversification.py).

**Qualification / avoid:** Positive/risk perturbations did not reach the intended R2/R3 scorer. Their unchanged outputs are not evidence of scoring-weight robustness.

## 8. Can M5 prove evidence improved ranking?

**Answer:** No. Its nDCG consumed the common corpus order, not predicted-score order, while the strict-rank correlations broke predicted and reference ties by identifier.

**Evidence:** [M5 runner](../scripts/run_m5_utility.py) · [correction](PHASE1_REPORTING_CORRECTIONS.md#m5-historical-ranking-metrics).

**Qualification / avoid:** Do not call those correlations conventional average-tied-rank Spearman or present them as comparative effectiveness. No corrected metrics are reported.

## 9. What does the M8 utility jump mean?

**Answer:** On the fixed pool, equally weighted task-level internal utility aggregates changed 0.441350 → 0.818950 after hard gates, then 0.858825 at utility-only R1; later R2, farthest-first and R3 retained that macro mean.

**Evidence:** [M8 summary](../experiments/m8/results/m8_summary.json) · [utility correction](PHASE1_REPORTING_CORRECTIONS.md#m8-utility-reference-labels-and-sensitivity).

**Qualification / avoid:** Gating changes eligibility and realized set size and gated candidates receive zero internal utility. This is neither independent recommendation accuracy nor an isolated universal causal gate effect; equal means do not prove equal sets or rankings.

## 10. Did M8 validate family exclusion?

**Answer:** Registered H1 is N/A: no R1 set met its same-family trigger. A separate M8 Iris rung-7/rung-8 contrast exercised family exclusion, and M7 had its own development example.

**Evidence:** [M8 summary](../experiments/m8/results/m8_summary.json) · [M7 results](M7_RESULTS.md).

**Qualification / avoid:** Do not present either descriptive case as a passed registered M8 H1. M7's selected-set size changed; the separate M8 Iris comparison preserved size.

## 11. Are Brier and ECE proof of calibrated suitability?

**Answer:** No. They are internal score–rubric consistency diagnostics using project-authored reference labels.

**Evidence:** [Consistency audit](../src/dataset_intelligence/evaluation/consistency.py) · [reporting correction](PHASE1_REPORTING_CORRECTIONS.md#m8-utility-reference-labels-and-sensitivity).

**Qualification / avoid:** Neither independent relevance nor probability calibration follows from these values.

## 12. Can the recorded M8 run be exactly reproduced offline?

**Answer:** Frozen inputs, configuration and recorded outputs are inspectable. M8 used a lightweight 64-bin test encoder; its built-in token hashing depends on a historical Python hash state that was not recorded.

**Evidence:** [Replay and network scope](PHASE1_REPORTING_CORRECTIONS.md#m8-harness-timing-offline-policy-and-replay) · [manifest](../data/benchmarks/m8_benchmark_manifest.json).

**Qualification / avoid:** Exact fresh-process dense/hybrid ordering is unestablished. Offline policy and a socket test limited to construction and loading do not prove measured whole-run zero egress.

## 13. What can the human pilot support?

**Answer:** Three participants each compared seven pairs of minimal and explanation-rich cards; the recorded ratings favor the richer card descriptively.

**Evidence:** [Pilot findings](M8_RESEARCH_FINDINGS.md) · [instrument](../data/benchmarks/m8_human_eval_instrument.md).

**Qualification / avoid:** All used the same initial schedule, one was an author and repeat linkage is uncertain for two; the understanding question asks for explanations B supplies and A omits. These observations do not establish general preference, recommendation correctness or causal benefit.

## 14. What remains to be tested?

**Answer:** Independent relevance and gate-accuracy assessment, repeated resource measurements, downstream evaluation and larger governed human studies are candidates for future work.

**Evidence:** [Phase II design proposal](phase2/README.md) · [current status](CURRENT_RESEARCH_STATUS.md).

**Qualification / avoid:** Phase II is unexecuted; protocol freeze, calibration and human data collection require separate authorization. Gate B remains closed.
