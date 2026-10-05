# Research paper workspace

This directory contains the IEEE conference-style capstone research paper and its supporting audit material. `main.tex` now contains the complete manuscript through Conclusion, one inline TikZ architecture figure, six evidence tables, and the synchronized inline bibliography. The evidence map and source artifacts remain the factual authority for results.

## Source-of-truth order

1. Implemented repository code and canonical M0–M8 experiment artifacts.
2. Final capstone report and its evidence map.
3. V5 research draft for framing and literature synthesis, checked against higher-priority sources.
4. Earlier civic-complaint paper for IEEE visual identity and research-quality lessons only.

The old paper directory and the capstone report are read-only inputs to this workspace. Do not copy their author block, unrelated bibliography, or proposal-era claims into this paper without verification.

## Current contents

- `main.tex`: complete Sections I--IX, abstract, index terms, architecture figure, evidence tables, provisional author block, and synchronized IEEE bibliography.
- `references.bib`: eight selected references whose bibliographic metadata was checked against primary publication records.
- `evidence/claim_map.json`: claim-level authoritative evidence, status, and intended section.
- `notes/authorship_basis.md`: source-based authorship and affiliation recommendation with open decisions.
- `notes/figure_inventory.md`: figure assets, provenance, proposed captions, and drawing requirements.
- `notes/table_inventory.md`: table sources, columns, and layout estimates.
- `notes/references_audit.md`: included-entry verification notes and excluded or corrected citations.
- `figures/`, `tables/`: reserved for external assets; Figure 1 is drawn inline in TikZ, while the results are presented in six tables.

## Paper-wide claim rules

- Keep M1–M7 development results separate from frozen M8 benchmark results.
- Label descriptive, exploratory, architectural, and N/A outcomes as such.
- Do not treat the rubric-based M8 consistency audit as independent calibration.
- Treat licenses as source claims, not legal advice, and bounded samples as scoped observations.
- Do not infer practitioner benefit, downstream model performance, or web-scale effectiveness from ranking outputs.
- Describe the implemented pipeline; natural-language requirement parsing, trained retrieval, formal evidence fusion, Cleanlab integration, learned weights, and formal submodular optimization are not presented as implemented.

## Current review status

- Scientific scope is frozen as a bounded systems/evaluation contribution; no independent-effectiveness experiment is claimed.
- The scientific consistency and claim-inflation audits are recorded in `notes/`.
- The independent reviewer recommended major revision because the evidence is bounded and not independent; ablation denominator and audit-attribution clarifications have been incorporated.
- The desktop LaTeX compiler has successfully compiled `main.tex`. Final page-by-page PDF visual inspection and text extraction remain pending.
- The author block remains provisional pending confirmation of paper contributions, order, official school wording, and current corresponding-author details.
