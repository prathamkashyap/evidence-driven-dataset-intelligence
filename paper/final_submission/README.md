# Approved final-submission package

This directory contains the six-author-approved final manuscript, committed on `main` in commit `60d24f595c07af945ffae21f0619f27f52e16d52`. The approved artifact is [`main.pdf`](main.pdf), a 10-page Letter-format paper. [`source_to_final_merge.md`](source_to_final_merge.md) records the manuscript's synthesis and provenance.

## Package contents

- [`main.tex`](main.tex): editable LaTeX source.
- [`main.pdf`](main.pdf): approved manuscript PDF.
- [`references.bib`](references.bib): bibliography source.
- [`IEEEtran.cls`](IEEEtran.cls) and [`IEEEtran.bst`](IEEEtran.bst): local IEEEtran class and bibliography style files.
- [`build.sh`](build.sh): build entry point.
- [`source_to_final_merge.md`](source_to_final_merge.md): source-to-final provenance record and editorial decisions.

## Build instructions and limits

From this directory, run:

```sh
./build.sh
```

The script invokes `latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error main.tex`. The recorded successful build used macOS arm64, TeX Live 2024 (`pdfTeX 3.141592653-2.6-1.40.26`, kpathsea 6.4.0), `latexmk`, BibTeX, and the TeX packages used by the source. The script regenerates `main.pdf` and LaTeX auxiliary files. The approved PDF is committed and should be treated as the reviewed deliverable; rebuilding is not required to use the package.

This build succeeded in the recorded environment. TeX Live packages and fonts are not pinned in a container or lockfile, so this does not establish byte-for-byte reproducibility in a clean environment or across platforms.

## Historical sources and audit context

The root-level [`paper/main.tex`](../main.tex) is an earlier working manuscript retained for provenance because the merge record documents how it informed this synthesis. It is not the approved paper, and `paper/main.pdf` is absent from the current tree. The comparison in `main.tex` to a “current dirty worktree copy” describes the historical audit checkout at commit `8613d9ea8233984e4b63dff16a1a50b78f10f18d`, not the current published repository.

The synthesis audit began from that historical commit while the checkout had pre-existing local changes. This package was later approved, committed, and pushed. References in the merge record to other inspected PDF candidates describe historical review inputs; those files are not package contents or build dependencies. No experiments were rerun to create this package, and the frozen results were not edited.

The manuscript's M2, M8, and human-pilot values cite the recorded artifacts and hashes in the merge/provenance materials. M7 resource values use the historical result committed at `bff07673cc05c638d227d4dc297f6672c611c6cf`; the different local measurement observed during the original audit was not used.

## Author metadata

All six authors approved the final manuscript. The author names and order follow the project-approved roster; the displayed email addresses follow the supplied registration-number convention. Mailbox reachability was not independently tested. The manuscript acknowledges Dr. Pradeep Kumar Mishra as supervisor and does not list him as a co-author; this README makes no independent contribution or authorship determination.
