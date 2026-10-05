# Bibliography verification record

The eight entries in `references.bib` were checked against primary or authoritative publication records on 2026-10-05. Author/title/year/venue and page/volume/DOI fields are populated where the publication record provides them. The sources are linked below for audit; the BibTeX uses IEEE-compatible metadata.

| BibTeX key | Verification result | Authoritative record | Notes/corrections against report reference list |
|---|---|---|---|
| `noy2019googledatasetsearch` | Verified: Natasha F. Noy, Matthew Burgess, Dan Brickley; Web Conference 2019; pp. 1365–1375; DOI 10.1145/3308558.3313685. | [Google Research publication page](https://research.google/pubs/google-dataset-search-building-a-search-engine-for-datasets-in-an-open-web-ecosystem/), [ACM DOI](https://doi.org/10.1145/3308558.3313685) | Correct title order and full venue/pages from publication record. |
| `viswanathan2023datafinder` | Verified: Vijay Viswanathan, Luyu Gao, Tongshuang Wu, Pengfei Liu, Graham Neubig; ACL 2023 long paper; pp. 10288–10303; DOI 10.18653/v1/2023.acl-long.573. | [ACL Anthology record](https://aclanthology.org/2023.acl-long.573/) | Corrects report's inaccurate authors (which listed Lin, Zhu, Ji, Roth) and title (which omitted “Descriptions”). |
| `mazumder2023dataperf` | Verified: full author list, NeurIPS 2023 Datasets and Benchmarks Track (NeurIPS 36); pp. 5320–5347; DOI 10.52202/075280-0235. | [NeurIPS 2023 record](https://papers.nips.cc/paper_files/paper/2023/hash/112db88215e25b3ae2750e9eefcded94-Abstract-Datasets_and_Benchmarks.html), [proceedings PDF](https://www.proceedings.com/content/075/075280-0235open.pdf) | Corrected report's arXiv-only record to the published NeurIPS track record. |
| `akhtar2024croissant` | Verified: 31 named authors; NeurIPS 2024 Datasets and Benchmarks Track (NeurIPS 37); pp. 82133–82148; DOI 10.52202/079017-2610. | [NeurIPS record](https://proceedings.neurips.cc/paper_files/paper/2024/hash/9547b09b722f2948ff3ddb5d86002bc0-Abstract-Datasets_and_Benchmarks_Track.html), [MLCommons citation](https://docs.mlcommons.org/croissant/) | Replaces the report's specification-only citation with the peer-reviewed Croissant paper; the normative specification can also be cited as documentation during drafting if a direct format-rule claim needs it. |
| `pushkarna2022datacards` | Verified: Mahima Pushkarna, Andrew Zaldivar, Oddur Kjartansson; ACM FAccT 2022; pp. 1776–1826; DOI 10.1145/3531146.3533231. | [ACM DOI](https://doi.org/10.1145/3531146.3533231), [FAccT paper](https://facctconference.org/static/pdfs_2022/facct22-3533231.pdf) | Corrects report's title wording “Purpose-Driven Visual Summaries” to the published title. |
| `longpre2023dataprovenance` | Verified: 17 authors; arXiv:2310.16787; submitted 2023. | [arXiv record](https://arxiv.org/abs/2310.16787) | Cited as an arXiv work, not as a journal/conference publication. |
| `northcutt2021confident` | Verified: Curtis G. Northcutt, Lu Jiang, Isaac L. Chuang; JAIR vol. 70; pp. 1373–1411; DOI 10.1613/jair.1.12125. | [JAIR/MIT publication record](https://dspace.mit.edu/entities/publication/39b0f8e0-b673-42c6-99f6-0af829bef7f5), [DOI](https://doi.org/10.1613/jair.1.12125) | Included for related-work positioning only; Cleanlab is not claimed as implemented. |
| `fahrbach2025gist` | Verified: Matthew Fahrbach, Srikumar Ramalingam, Morteza Zadimoghaddam, Sara Ahmadian, Gui Citovsky, Giulia DeSalvo; NeurIPS 2025 Main Conference (NeurIPS 38); DOI 10.52202/085713-1542. | [NeurIPS record](https://proceedings.neurips.cc/paper_files/paper/2025/hash/41febbd2bd4bd1f268ada869cee28e44-Abstract-Conference.html) | Corrects report's attribution to Zadimoghaddam et al. and title; project uses no GIST library or formal submodular optimizer. |

## Entries not included at this stage

- Dempster (1968) and Shafer (1976): formal evidence-fusion background is a deferred alternative, not the implemented resolver. Add only if Related Work needs the contrast and after checking the relevant edition/details.
- Guo et al. (2017): not needed to support the current claim map; the M8 Brier/ECE result is explicitly an internal pipeline-consistency audit, not a calibration claim. Add only if the methods discussion needs a calibration-metric citation.
- The previous civic-complaint paper's bibliography is unrelated and excluded.

No included entry currently requires manual bibliographic confirmation. Before submission, rerun the reference audit against the exact venue style and any new citations added during drafting.

## Editor build note

The desktop editor's standalone compiler successfully compiles `main.tex`, but it does not import sibling `.bib` files or invoke BibTeX. To keep its live preview self-contained, `main.tex` contains a keyed IEEE-style `thebibliography` mirror of these eight verified entries. `references.bib` remains the maintained bibliographic source; keep the inline mirror synchronized when references change.
