# Table inventory

Stage 4 uses six compact evidence tables. They replace the need for additional result figures in Sections V--VI; values remain directly inspectable and repeated-measure pilot observations are not presented as inferential plots.

| Table | Source artifact | Section | Required columns | One IEEE column? | `table*` needed? | Exact evidence source |
|---|---|---|---|---|---|---|
| I. Evaluation strata and protocol | `configs/m0_compute_budget.json`, `experiments/m2/results/benchmark.json`, `configs/m8_evaluation.json`, M8 reproducibility block | V-A--B | Setting; corpus/tasks; protocol boundary; resource/offline conditions | No; grouped protocol text needs width | Yes | M0 summary/budget; M2 benchmark; M8 manifest/config and `m8_summary.json` |
| II. Development component results | M2--M7 result JSON and result notes | VI-A--D | Milestone; scope; measured findings; evidence boundary | No at readable text size | Yes | `experiments/m2/results/benchmark.json` through `experiments/m7/results/ranking_comparison.json`; frozen M7 values from revision `bff0767` |
| III. M8 cumulative ablation | `experiments/m8/results/m8_summary.json#ablation_ladder` | VI-E | Rung; mean set utility | Yes | No | Eight task ladders aggregated over the frozen 24-record / eight-task benchmark |
| IV. M8 hypotheses | `experiments/m8/results/m8_summary.json#hypotheses` | VI-E | Hypothesis; status; exact observed outcome; boundary | No at readable text size | Yes | H1--H5 machine-readable outcome blocks; H4 per-task N/A counts |
| V. M8 robustness, sensitivity, and consistency audit | `experiments/m8/results/m8_summary.json` | V-D, VI-F | Protocol; cases; state/crash/utility/set metrics; audit values and limitation | No | Yes | `robustness`, `sensitivity`, and `consistency_audit` blocks; seed/environment in `reproducibility` |
| VI. Human-pilot descriptive results | `experiments/m8/results/m8_human_eval_summary.json`, `data/benchmarks/m8_human_eval_protocol.md` | V-D, VI-G | Dimension; A mean/median; B mean/median; paired B--A mean/median | Yes | No | Primary first-exposure summary: N=3 participants, 7 comparisons each, 42 card rows, 126 Likert values |

The M7 resource fields in the worktree's currently modified `m7_summary.json` differ from the committed `bff0767` snapshot and `docs/M7_RESULTS.md`. The paper uses the user-specified `bff0767` measurements and reports this unresolved worktree discrepancy in the stage audit rather than silently mixing versions.
