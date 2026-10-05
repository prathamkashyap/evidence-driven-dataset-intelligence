# Independent Skeptical Review

## Overall recommendation: Major revision

The manuscript is unusually careful about scope and does not present M8 as web-scale or as an end-to-end retrieval evaluation. Its central contribution is stated as an implemented integration with evidence-backed evaluation. The principal remaining concern is whether the experiments establish a sufficiently clear scientific contribution beyond documenting the implementation and its component behavior.

## Specific reviewer concerns

1. **M2 retrieval:** All methods reach Recall@3 = 1.000 on five metadata-derived relevance pairs. The result is saturated and cannot distinguish retrieval quality; any preference for BM25 should rest on measured cost, not retrieval superiority. BM25 RSS was not separately recorded.
2. **M5 utility comparison:** Spearman and NDCG values show agreement with a human-authored rubric that shares concepts with the estimator. They do not validate suitability against independent judgments or downstream performance. Keep this dependence prominent wherever M5 is summarized.
3. **M6/M7:** M6 additions occur for one of four queries and use an internal high-utility estimate; clarify that the simulation is exploratory. M7 is one development-corpus duplicate case, and R3's aggregate diversity metric is lower. Avoid generalizing either result.
4. **M8 cumulative ablation:** The ladder is cumulative and the candidate corpus is fixed. Its mean set utility should define both averaging and denominator. After gating, four tasks return two items rather than three, so the change from 0.4414 to 0.8189 is affected by eligibility and set-size/composition; it is not an isolated gate effect.
5. **H1/H3/H4:** H1 is correctly N/A. H3's registered retention criterion is met, but its corpus-conditioned interpretation is narrower than a generic “Supported” label suggests. H4 appropriately separates its architectural invariant from an empirical association that could not be estimated.
6. **Consistency audit attribution:** The canonical `m8_summary.json` stores the audit under M8 and describes it as a check of M7 scores against the M5-related rubric. Calling it a “M7 pipeline-consistency audit” without that distinction can look like a milestone-source contradiction. Describe it as an M8 consistency audit of M7 scores.
7. **Robustness/consistency and human pilot:** Fixture results remain fixture-scoped, and Brier/ECE are correctly described as internal diagnostics rather than calibration. The pilot's three participants, shared schedule, author-participant, and lack of inferential tests support descriptive reporting only.

## Corrections applied after review

- The methodology now identifies the consistency analysis as an M8 audit of M7 scores.
- The methodology and Discussion define the ablation statistic and disclose the reduced set sizes after gating.
- H3 is labeled “Criterion met” in the outcomes table.
- The contribution remains framed as an implemented integration and scoped evaluation; no new independent-effectiveness or downstream-performance claim was added.

## Remaining publication question

The review's major-revision recommendation reflects the bounded scientific contribution and limited independence/scale of the evaluation, not an identified false result. These design limits are disclosed in the manuscript; resolving them would require independent judgments or additional evaluation, not editorial wording alone.
