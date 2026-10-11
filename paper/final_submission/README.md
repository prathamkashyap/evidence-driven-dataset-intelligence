# Final submission candidate

This is a new, isolated synthesis of the tracked paper and the alternate TeX manuscript. The files in the parent `paper/` directory were left unchanged.

## Contents

- `main.tex`: synthesized editable manuscript.
- `main.pdf`: built candidate.
- `references.bib`: bibliography source.
- `IEEEtran.cls` and `IEEEtran.bst`: local copies of the class and bibliography style needed by this source.
- `source_to_final_merge.md`: concise merge record and editorial decisions.
- `build.sh`: build entry point.

## Build and environment

Verified on the current macOS arm64 environment with TeX Live 2024 (`pdfTeX 3.141592653-2.6-1.40.26`, kpathsea 6.4.0), `latexmk`, and BibTeX available:

```sh
./build.sh
```

The script runs `latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error main.tex`. The source uses pdfLaTeX because it contains no Unicode or system-font requirements and IEEEtran's standard text fonts are available in this toolchain. The local class and bibliography style are included; standard TeX Live packages used by the source include `amsmath`, `amssymb`, `graphicx`, `booktabs`, `tabularx`, `tikz`, `pgfplots`, `cite`, `placeins`, `algorithm`, `algpseudocode`, `url`, and `hyperref`.

The current candidate builds to a 10-page Letter PDF in the inspected host environment. This does not establish a clean-environment or cross-platform reproducible build: TeX Live package versions and fonts are not pinned in a container or lockfile.

## Evidence provenance

The audit checkout was branch `main` at `8613d9ea8233984e4b63dff16a1a50b78f10f18d`; the repository had pre-existing dirty and untracked files. Those files were preserved. Only the new `paper/final_submission/` candidate was created by this work; no commit was made.

The reported result values use these artifacts and SHA-256 hashes:

- M2 retrieval comparison (`experiments/m2/results/benchmark.json`): `bace53d9f0e76623ae9737ff079d961f459e3463754b06b81df067762b754206`.
- M8 frozen offline benchmark summary, including the ablation, lambda sweep, registered outcomes, robustness checks, and task-level results (`experiments/m8/results/m8_summary.json`): `ce246572089a6cefd4955a88733859020baa87ece13829bf3713553625ece3d3`.
- M8 human-pilot summary (`experiments/m8/results/m8_human_eval_summary.json`): `bece59e2ef60c3be8ede9720a8902106e50249dc4425ee8df4f93f72a386fe8a`.

The M8 summary hash was rechecked during the final submission-hygiene pass and remains unchanged. M7 resource values intentionally refer to the historical result artifact at commit `bff0767`; the dirty worktree copy is different and was not used.

The recorded M8 freeze references are: implementation `7d6172813e78afd15488ea8995b7365be66e215c`; benchmark inputs `7a2c774eecbd32f13abf26129cadd48dfae2f1b2`; corpus preparation `ee9171b4bff6f3522232f111d7f96120ad3741e4`; and protocol `3df1bae455c36e81d266b7c45edfc5465763d281`. The M7 historical result commit is `bff07673cc05c638d227d4dc297f6672c611c6cf`.

No experiments were rerun. The frozen result artifacts and existing manuscripts were not edited.

## Author metadata

The author names and order follow the project-supplied roster. All six addresses are displayed in one 3-by-2 author block using the supplied registration-number convention; mailbox validity has not been independently tested. No individual is designated as corresponding author. The shared affiliation uses School of Computing Science and Artificial Intelligence (SCAI), VIT Bhopal University, with the supplied university address.

The acknowledgment thanks Dr. Pradeep Kumar Mishra as supervisor and links ORCID 0000-0002-2549-1200. Supervisor authorship was not presumed; the team should decide whether substantive scholarly contributions warrant co-authorship.

The Results section includes task-level lambda-sweep endpoints, a compact robustness table, and a compact M3--M7 table. Tables VI--VIII appear before Threats to Validity and are placed near their corresponding findings. The bibliography uses IEEEtran's `\IEEEtriggeratref{7}` to start reference [7] in the right column; line-break penalties keep entries together, and global `flushend` balancing is not used.
