# Source-to-final merge record

| Final section or element | Primary source | Adopted material | Editorial treatment |
|---|---|---|---|
| Abstract and contribution framing | `paper/main.tex` | Evidence semantics, constraints, bounded observations, traceable cards, resource scope | Rewritten around hard-gating jump, post-gating plateau, and diversity trade-off; avoids general-effectiveness claims. |
| Introduction and research question | Dossier, `paper/main.tex` | Problem framing and explicit limitations | Adds the agreed research question and an operational definition of the local-first M8 path. |
| Related work | Both TeX sources and dossier | DataFinder, Croissant, Data Cards, DataPerf, Confident Learning, GIST | Updates Longpre to the published Nature Machine Intelligence record; adds DatasetResearch as a different design point; reserves DataFinder's 392 queries for future evaluation. |
| System and method | `paper/main.tex` and verified implementation | Two evidence-state layers, three hard gates, seven utility components, five score dimensions, greedy selection | Adds labeled formulations for eligibility, utility, attribute distance, set diversity, empty-set marginal diversity, greedy choice, and M8 aggregation; no learned-ranker or formal submodularity claim. |
| M8 ablation | Both TeX sources | Nine frozen mean utilities; clearer alternate-source figure interpretation | Uses a table instead of the alternate bar chart; adjacent text states fixed-pool scope and set-size confounding. |
| Lambda sensitivity | Dossier and frozen M8 summary | All eight weights, utility, diversity, and Jaccard values | Adds a two-panel trend figure plus exact-value table; makes the plateau and measured utility-diversity trade-off visible. |
| Task-level sensitivity | Frozen M8 summary | Per-task utility, diversity, and set-overlap fields | Adds endpoint comparison at the default and largest tested lambda; interprets the flat aggregate without equating it with unchanged membership. |
| M2 resource comparison | `paper/main.tex` plus alternate source's presentation emphasis | Recall, latency, dense preparation, whole-process RSS | Separates optional dense MiniLM cost from M8 path; omits unsupported isolated BM25 memory. |
| M3--M7 and robustness | `paper/main.tex` and frozen/historical artifacts | Development evidence, negative and N/A results, M7 historical values | Keeps robustness and development tables compact and near their discussion; preserves the `bff0767` artifact distinction. |
| Human pilot | Tracked source, dossier, and human summary | Format A and B means, paired mean and median differences | Adds realized 5 B-first / 2 A-first split, author participation, repeat-exposure caveat, and descriptive-only interpretation. Table VIII follows the pilot discussion. |
| Author block and acknowledgment | Project-supplied roster and supervisor details | Six author addresses and acknowledgment | Uses one unified 3-by-2 author block and one shared SCAI affiliation; no individual corresponding-author designation; acknowledges Dr. Pradeep Kumar Mishra with an ORCID link and does not presume co-authorship. |
| Architecture / plots | Main inline TikZ and alternate `fig2`--`fig4` | Conceptual pipeline from canonicalization through cards; result plots inspected | Recreates a functional pipeline diagram in TikZ; tables carry key quantitative results instead of duplicating the alternate plots. |
| PDF presentation | Three compiled PDF candidates | Candidate PDFs inspected for technical content and presentation | Retains IEEE two-column Letter presentation, uses descriptive tables and a functional architecture diagram, and revises author metadata, results flow, and bibliography layout without modifying prior candidates. |
| Third PDF candidate | `paper/Evidence-Driven-Dataset-Intelligence-IEEE-rev2-21ba31d1.pdf` | Presentation inspected only | No technical text copied; editable source is unidentified and the PDF contains an unsupported transfer estimate. |

## Verified facts versus editorial judgments

Verified against the checkout and recorded artifacts: candidate file existence and dimensions; TeX source section structures; M8 summary hash and result values; M2 recorded metrics; M7 historical/current artifact difference; and human-pilot summary values. PDF checks confirm ten pages, all six supplied email strings, no corresponding-author marker, and no overfull-box or unresolved-reference warnings. Editorial judgments: using the tracked source as the factual spine, suppressing duplicate graphics in favor of tables, ordering results around the principal M8 finding, and retaining the third PDF only as a visual/presentation reference.

## Unresolved before submission

- The supplied student email convention and each mailbox's validity should be confirmed by the team before submission. No corresponding author is designated in this candidate.
- The supervisor is acknowledged, not listed as an author. The team and supervisor should resolve co-authorship if they believe substantive scholarly contributions warrant it.
- The current repository has unrelated dirty/untracked state, including a modified M7 worktree summary. The manuscript identifies the historical M7 artifact used.
- A clean-environment build is not established because the TeX distribution and package versions are not pinned.
