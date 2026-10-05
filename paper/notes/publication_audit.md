# Final Paper Audit

## Scientific consistency

- M2 reported means were recomputed from `experiments/m2/results/benchmark.json`: BM25/dense/hybrid Recall@1 = 0.875 and Recall@3 = 1.000; mean latencies = 0.0602/700.1929/15.0808 ms.
- M7's paper values use revision `bff0767`: 25.88 MiB and 13.66 ms. The modified worktree copy's 25.67 MiB and 17.23 ms are disclosed once as an unresolved artifact discrepancy in Section VIII.
- M8 is consistently described as 24 dataset records by eight tasks (192 task--dataset pairs). The consistency audit is identified as an M8 analysis of M7 scores, using the M5-related rubric.
- H1 remains N/A. H4's popularity exclusion is described as an architectural invariant, while its empirical association remains unestimable. M6 is exploratory development evidence; M7 is development-corpus evidence; the human pilot is descriptive.
- The paper does not characterize the M8 run as an end-to-end retrieval/local-envelope evaluation. It states that M8 begins from a fixed corpus and that component/development resource measurements were separate.
- The M8 ablation metric is now defined as a per-task mean over selected candidates followed by an unweighted mean across eight task means. The reduction to two candidates in four tasks after gating is disclosed, preventing an isolated or matched-size gate-effect interpretation.

## Independent reviewer

The read-only reviewer recommended **major revision**, principally because (1) the contribution is an integration with limited independent outcome evidence, (2) the M8 ablation is cumulative and its set sizes change after gating, and (3) the M8 consistency-audit attribution and H3 label needed clarification. Items 2 and 3 were addressed in the source. The limited corpus and non-independent rubric remain genuine study limitations, not wording defects.

## Publication and build checks

- Citation-key audit: all eight cited keys have matching entries in both `references.bib` and the synchronized inline bibliography; no unused or unresolved keys were found.
- Equation layout was split across aligned lines. Wide tables use `tabularx` to constrain them to the two-column text width.
- The built-in LaTeX editor compiler reports successful compilation of `paper/main.tex`.
- The desktop editor compiler and external XeLaTeX build both succeeded. The final PDF is 10 pages on Letter paper. Every rendered page was visually inspected: the two-column layout, Figure 1, six tables, equations, and references are legible, with no clipping or overfull boxes. PDF text extraction found all nine numbered sections, Figure 1, Tables I--VI, and eight bibliography entries; no placeholder or unresolved-reference markers were found.
- The final rendered PDF is `paper/main.pdf`. Only mechanical table-header wording was adjusted during visual QA; no research claims or the evidence map changed.

The evidence map was not changed.
