# Evidence-Driven Dataset Intelligence and Recommendation System

*LLM-assisted discovery, content-aware suitability estimation, long-tail exploration, provenance, calibrated confidence, and explainable ranking*

**Research-Grounded Final Proposal**
Pratham Kashyap — B.Tech. CSE (AI/ML), School of Computer Science and Engineering (SCAI), VIT Bhopal University
September 2026

*Design status: implementation-ready research specification*

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Foundation and Scope](#2-project-foundation-and-scope)
3. [Research Gap and Problem Definition](#3-research-gap-and-problem-definition)
4. [Research Questions and Objectives](#4-research-questions-and-objectives)
5. [Research Foundations and Adopted Methods](#5-research-foundations-and-adopted-methods)
6. [Final Design Principles](#6-final-design-principles)
7. [Final System Architecture](#7-final-system-architecture)
8. [Canonical Dataset Representation](#8-canonical-dataset-representation)
9. [Evidence Ledger and Trust Model](#9-evidence-ledger-and-trust-model)
10. [Content-Aware Dataset Fingerprinting](#10-content-aware-dataset-fingerprinting)
11. [Data Quality Analysis](#11-data-quality-analysis)
12. [Task-Specific Utility Estimation](#12-task-specific-utility-estimation)
13. [Popularity Bias and Long-Tail Discovery](#13-popularity-bias-and-long-tail-discovery)
14. [Diversified Recommendation](#14-diversified-recommendation)
15. [Multi-Objective Recommendation Model](#15-multi-objective-recommendation-model)
16. [Explanation and Recommendation Output](#16-explanation-and-recommendation-output)
17. [Local Implementation Strategy](#17-local-implementation-strategy)
18. [End-to-End Recommendation Algorithm](#18-end-to-end-recommendation-algorithm)
19. [Evaluation Framework](#19-evaluation-framework)
20. [Baselines and Ablation Plan](#20-baselines-and-ablation-plan)
21. [Scope and Development Roadmap](#21-scope-and-development-roadmap)
22. [Risks, Limitations, and Safeguards](#22-risks-limitations-and-safeguards)
23. [Expected Project Contribution](#23-expected-project-contribution)
24. [Expected User-Facing Result](#24-expected-user-facing-result)
25. [References](#25-references)
- [Appendix A. Practical Repository Structure](#appendix-a-practical-repository-structure)
- [Appendix B. Minimum Viable System vs. Full Research System](#appendix-b-minimum-viable-system-vs-full-research-system)
- [Appendix C. Implementation Stop Conditions](#appendix-c-implementation-stop-conditions)
- [Appendix D. Worked Evidence-Resolution Example](#appendix-d-worked-evidence-resolution-example)
- [Appendix E. Suggested Evaluation Dataset and Query Construction](#appendix-e-suggested-evaluation-dataset-and-query-construction)
- [Appendix F. Hardware-Agnostic Local Compute Policy](#appendix-f-hardware-agnostic-local-compute-policy)

---

## 1. Executive Summary

The project is an evidence-driven dataset intelligence system for Machine Learning (ML), Deep Learning (DL), and Computer Vision (CV) practitioners. A user supplies a natural-language description of a project. The system converts the description into a structured task specification, discovers candidate datasets across multiple public repositories, gathers evidence about those datasets, performs lightweight analysis of accessible samples where feasible, estimates task-specific utility, mitigates popularity bias, and produces a diversified, explainable recommendation set.

The system is intentionally positioned beyond generic dataset search. Existing dataset-recommendation work demonstrates that strong lexical and dense retrieval can already identify semantically relevant datasets. Therefore, retrieval is treated as the candidate-generation layer rather than the principal contribution. The project instead focuses on the harder decision problem: selecting datasets that are defensibly useful for a task, while exposing evidence quality, uncertainty, provenance, and trade-offs.

Repository metadata is treated as one evidence source rather than ground truth. Where technically and legally feasible, actual samples are inspected to create a Dataset Fingerprint containing observed structural, quality, diversity, and representation characteristics. A lightweight task probe may estimate downstream usefulness without requiring full model training. When sampling is infeasible, the system uses an explicitly weaker transfer estimate from already-probed candidates rather than dropping the dataset entirely.

Popularity is separated from suitability. Downloads, stars, ratings, reviews, citations, and repository visibility may provide contextual community evidence, but they do not define dataset fitness. A long-tail exploration pool reserves candidates that are relevant but not dominant in popularity, and diversified reranking prevents near-identical popular dataset families from crowding out useful alternatives.

The final result is not a single opaque score. Each recommended dataset is returned with its role, evidence strength, supporting observations and sources, limitations, uncertainty, and the factors that caused it to rank above nearby alternatives. The research program evaluates retrieval quality, task utility, long-tail discovery, diversity, robustness to missing or contradictory metadata, calibration, human trust, and computational cost.

## 2. Project Foundation and Scope

The core problem remains dataset discovery and selection for ML/DL/CV projects. The system accepts natural-language project descriptions, searches across multiple public repositories such as Kaggle, Hugging Face Hub, UCI, OpenML, and other compatible sources, and returns a ranked set of recommendations with source links and explanations. Complete downloads of every candidate dataset are not required in the default path.

### 2.1 System boundary

**In scope:** requirement extraction, multi-source ingestion, canonical normalization, lexical and dense retrieval, hard-constraint filtering, evidence collection, content-aware analysis, task-aware utility estimation, long-tail discovery, diversified ranking, explanations, and evaluation.

**Out of scope for the core system:** training a large language model from scratch, full forensic auditing of every file in every dataset, legal clearance, and web-scale optimization over millions of samples.

Advanced mechanisms such as retriever fine-tuning, Cleanlab-style diagnosis, formal evidence fusion, GIST-inspired selection, and human evaluation are implemented where they improve the research questions and remain inside the validated compute budget.

## 3. Research Gap and Problem Definition

### 3.1 Why metadata-only recommendation is insufficient

Dataset recommendation is already an information-retrieval problem. DataFinder demonstrates a benchmark using research needs and evaluates BM25, nearest-neighbor, and trained dense bi-encoder retrieval, showing that a task-specific retriever can substantially outperform generic search. A system whose novelty is limited to LLM extraction, vector retrieval, and metadata scoring would therefore risk reproducing an existing direction [1].

The project consequently shifts the optimization target from "retrieve something semantically similar" to "select a dataset whose evidence supports its usefulness for the requested task." Metadata remains valuable for inexpensive candidate generation and constraint handling, but stronger ranking claims are supported by additional documentation, provenance, structure, and sample evidence when available.

### 3.2 Why repository metadata cannot be treated as ground truth

Repository metadata is publisher-supplied and heterogeneous. Documentation quality can vary with visibility, maintenance, and community attention. Licensing is particularly sensitive: public audits have documented substantial missing or incorrectly stated dataset licenses [7]. The system therefore preserves the difference between a repository claim and a verified or cross-supported fact.

A field such as "License: CC BY 4.0" can be displayed as a source claim; it is not silently translated into legal clearance. When sources disagree, the contradiction is surfaced. When no reliable evidence is available, the field remains *Unknown* rather than being imputed as favorable.

### 3.3 Why popularity must not define suitability

Downloads, stars, ratings, reviews, citations, and repository visibility can be useful community signals, but they are not equivalent to task fitness. A popularity-dominated ranking systematically favors already-visible datasets and can create a feedback loop that suppresses specialized or smaller datasets. The proposed system therefore reserves an explicit long-tail path and evaluates whether the final recommendations remain useful when visibility is reduced as a selection pressure.

### 3.4 Problem statement

Given a natural-language ML/DL/CV project objective and a heterogeneous collection of public datasets, design a local-first system that identifies a small set of task-suitable datasets using multiple evidence sources, estimates content and task utility where feasible, explicitly represents uncertainty and conflicts, reduces popularity-driven exposure bias, and explains why each recommendation is defensible.

## 4. Research Questions and Objectives

### 4.1 Research questions

1. Can hybrid lexical and semantic retrieval identify relevant datasets more effectively than lexical-only, dense-only, and strong trained-retriever baselines?
2. Can content-aware evidence and lightweight task probes improve dataset selection beyond metadata-only suitability ranking?
3. Can an evidence-resolution layer improve the reliability and calibration of claims about datasets, particularly under conflicting or incomplete metadata?
4. Can popularity-neutral long-tail exploration increase the discovery of useful lesser-known datasets without materially reducing relevance?
5. Can diversified recommendation produce a more useful final set than simply returning the five highest-scoring datasets?

### 4.2 Objectives

1. Build a normalized multi-source dataset corpus with stable internal identifiers and provenance pointers.
2. Extract structured requirements using a constrained schema, with unresolved requirements explicitly represented.
3. Generate a broad candidate pool using hybrid retrieval and apply hard constraints without prematurely sacrificing recall.
4. Assemble an evidence ledger containing source, observation time, evidence type, confidence, and contradiction information.
5. Create content-aware Dataset Fingerprints from bounded samples when access is permitted and useful.
6. Estimate task-specific utility using lightweight probes rather than full-scale training.
7. Preserve a long-tail candidate path and diversify final recommendations by utility, coverage, and dataset family.
8. Produce explanations that separate measured evidence, source claims, assumptions, unknowns, and limitations.
9. Evaluate the resulting system with retrieval, ranking, utility, long-tail, robustness, calibration, human-trust, and efficiency metrics.

## 5. Research Foundations and Adopted Methods

The project adopts established ideas as building blocks and evaluates their value in the integrated dataset-selection setting. The goal is not to claim that each component is novel in isolation; the research contribution is the task-specific integration, evidence model, and empirical evaluation of the resulting decision process.

| Foundation | Established capability | Role in this project |
|---|---|---|
| DataFinder [1] | Natural-language dataset retrieval; BM25, dense, and bi-encoder baselines. | Primary retrieval reference and baseline; retrieval is candidate generation rather than the endpoint. |
| DataPerf [2] | Data-centric benchmarks for selection, cleaning, and acquisition. | Informs task-utility estimation and the principle that data selection can be evaluated through downstream performance. |
| Cleanlab [3] | Model-assisted label-issue and data-quality analysis. | Optional sample-level evidence for suspicious labels, duplicates, and outliers when assumptions are satisfied. |
| Croissant [4] | Machine-readable metadata, structure, provenance, and usage-policy concepts. | Canonical evidence and interoperability layer; used where available without discarding source-specific fields. |
| GIST [5,6] | Utility + diversity subset selection. | Informs bounded diversified reranking; a lightweight greedy approximation is sufficient for local candidate pools. |
| Dataset Cards [9] | Structured dataset context, intended use, and limitations. | Evidence source for task, provenance, scope, and documentation claims. |
| Provenance / licensing audits [7] | Evidence that public dataset governance metadata can be missing or incorrect. | Motivates cross-source verification, uncertainty, and explicit license-risk handling. |

**Design consequence.** None of these sources is treated as a reason to copy an existing system wholesale. Each is mapped to a specific subsystem and subjected to ablation or robustness evaluation.

## 6. Final Design Principles

- **Evidence over assertion:** every material recommendation factor must be traceable to a source, observation, computed metric, or explicit assumption.
- **Suitability over popularity:** community visibility is contextual evidence, not a quality label.
- **Long-tail discovery is intentional:** relevant low-visibility candidates retain a route into deeper evaluation.
- **Content when available:** actual sample evidence supplements descriptions without requiring indiscriminate full downloads.
- **Hard constraints are filters:** mandatory modality, size, or usage requirements are not reduced to minor score penalties.
- **Unknown is a first-class state:** missing evidence is not silently converted into average or positive evidence.
- **Recommendations are sets:** final results should be useful together and avoid redundant mirrors, versions, and closely derived datasets.
- **Local-first and reproducible:** central functionality uses open-source, cacheable components that can run on ordinary personal computers with constrained resources.
- **Confidence must be calibrated:** "High" evidence strength is shown only when empirical evaluation supports the reliability of the underlying confidence estimate.

## 7. Final System Architecture

```text
USER PROJECT DESCRIPTION
        |
        v
[Requirement Analyst: LLM / constrained parser]
        |
        v
[TASK SPECIFICATION]
 task | domain | modality | target | labels | constraints
        |
        +----------------------+----------------------+
        |                                             |
        v                                             v
[Hard Constraint Policy]                    [Semantic Query Expansion]
        |                                             |
        +----------------------+----------------------+
                               v
                 [HYBRID CANDIDATE RETRIEVAL]
                       BM25 + dense embeddings
                               |
                               v
                       [CANDIDATE POOL 50-100]
                               |
                  +------------+-------------+
                  |                          |
                  v                          v
          [EVIDENCE LAYER]          [CONTENT EVIDENCE]
        metadata/docs/provenance     samples/fingerprints
        license/community signals    quality/probes
                  |                          |
                  +------------+-------------+
                               v
                    [EVIDENCE LEDGER]
                               |
                    [EVIDENCE RESOLUTION]
                 belief / plausibility / conflict
                               |
                    [TASK UTILITY ESTIMATION]
                               |
                  [LONG-TAIL EXPLORATION POOL]
                               |
                 [DIVERSIFIED MULTI-OBJECTIVE
                         RERANKING]
                               |
                    [FINAL RECOMMENDATION SET]
       best overall | quality | efficient | hidden gem | alternative
                               |
                               v
                    [EVIDENCE-BACKED REPORT]
```

### 7.1 Candidate-pool strategy

A broad candidate pool is retrieved cheaply before expensive inspection. A default range of approximately 50–100 candidates is a working hypothesis, not a hard architectural constant. A compute-budget validation milestone measures retrieval time, sample acquisition time, memory use, and probe cost before the team commits to the final pool size.

## 8. Canonical Dataset Representation

Each source is ingested through an adapter. Repository-specific fields remain attached to their source so that normalization does not erase important context. A canonical record provides stable fields for cross-source retrieval and ranking while preserving raw provenance references.

Croissant metadata is used where available as a standards-aligned representation. Native repository metadata is retained rather than replaced, because heterogeneous sources are themselves part of the evidence problem.

| Field group | Representative fields |
|---|---|
| Identity | internal_id, source_id, source_name, dataset_name, canonical_url, version/family identifiers |
| Semantics | description, task, domain, modality, learning_type, target, tags, intended_use |
| Structure | sample_count, class_count, schema, formats, splits, feature/field information |
| Governance | license_claim, usage_policy, citation, creators, provenance_links, documentation_links |
| Community context | downloads, stars, ratings, citations, update timestamps, repository activity |
| Observed content | sample_count_observed, modality diagnostics, duplicate rate, embedding statistics, probe results |
| Operational | access method, sampling feasibility, cache status, time cost, retrieval contribution, risk flags |

## 9. Evidence Ledger and Trust Model

The evidence ledger stores claims independently from the final score. Each claim has a dataset identifier, claim type, value, source, source timestamp, evidence type, reliability prior or quality indicator, observation procedure, and contradiction information. This prevents the explanation layer from converting uncertain metadata into authoritative-sounding statements.

| Evidence state | Meaning | Ranking behavior |
|---|---|---|
| Measured | Computed directly from an accessible sample or parsed resource. | Strong evidence, scoped to the measurement procedure. |
| Corroborated | Supported by two or more independent sources, or by source + computation. | Higher confidence than a single-source claim. |
| Single-source claim | Present in one repository or document without independent validation. | Usable but confidence-limited. |
| Conflicting | Sources disagree, or a source conflicts with observed data. | Penalize confidence and surface the contradiction. |
| Unknown | Information unavailable or inaccessible. | Do not infer a positive or negative value; reduce confidence where material. |

### 9.1 Formal evidence resolution: Dempster–Shafer as a candidate core methodology

For claims where several independent sources provide explicit positions, the project evaluates Dempster–Shafer evidence fusion [10, 11] because it represents ignorance separately from disagreement. **This is a methodology adopted for evaluation, not a guaranteed novelty claim.** Using Dempster–Shafer theory to combine heterogeneous evidence is itself an established methodological pattern; the research contribution rests on whether this evidence-resolution design measurably improves dataset-recommendation reliability and calibration in the integrated system, as tested by the ablation plan (§20) and the calibration study (§19.3) — not on the combination rule in isolation.

For a binary claim $c$ about dataset $d$, let the frame of discernment be $\Theta = \{\top, \bot\}$ (claim true / claim false). Each source $i$ receives a bounded reliability prior $r_i \in (0,1)$ and assigns mass to its stated position, with residual mass placed on $\Theta$ to represent uncertainty:

$$
m_i(\top) = \begin{cases} r_i & \text{source asserts true} \\ 0 & \text{source asserts false} \end{cases}
\qquad
m_i(\bot) = \begin{cases} 0 & \text{source asserts true} \\ r_i & \text{source asserts false} \end{cases}
\qquad
m_i(\Theta) = 1 - r_i
$$

Sources are combined pairwise using Dempster's rule of combination:

$$
m_{12}(A) = \frac{1}{1-K}\sum_{B \cap C = A} m_1(B)\,m_2(C), \qquad
K = \sum_{B \cap C = \emptyset} m_1(B)\,m_2(C)
$$

where $K$ is the conflict mass. The result preserves: **Belief** $\mathrm{Bel}(\top) = m(\top)$, **Plausibility** $\mathrm{Pl}(\top) = 1 - m(\bot)$, the **uncertainty interval** $[\mathrm{Bel}(\top), \mathrm{Pl}(\top)]$, and the **accumulated conflict** $K_{\text{total}}$ across all pairwise combinations.

**Algorithm 1 — `ResolveClaim(c, sources)`**

```text
if no sources exist:
    return UNKNOWN, Bel = 0, Pl = 1

initialize mass m from the first source
K_total = 0
for each remaining source i:
    compute conflict K between m and BPA(i)
    combine masses using Dempster's rule: m = m ⊕ BPA(i)
    accumulate conflict: K_total = K_total + K * (1 - K_total)

compute Bel(true) = m(true), Pl(true) = 1 - m(false)

if exactly one source:
    return SINGLE_SOURCE_CLAIM
elif K_total > kappa_high:
    return CONFLICTING
elif Bel(true) >= tau_v and K_total <= kappa_low:
    return VERIFIED
elif Bel(true) >= tau_c and K_total <= kappa_low:
    return CORROBORATED
else:
    return SINGLE_SOURCE_CLAIM   # low-confidence fallback state
```

Default source priors are treated as prototype parameters and are tuned against observed correctness (§19.3). The system must be able to fall back to raw evidence counts and source lists if synthesized confidence remains poorly calibrated.

| Source type | Typical claims | Initial prior |
|---|---|---|
| Direct measurement | modality, approximate class count, file format, sampled structural statistics | 0.90 |
| Peer-reviewed paper | task, domain, collection method | 0.85 |
| Validated Croissant metadata | license, schema, splits | 0.80 |
| Official dataset card | license, size, task, modality | 0.70 |
| Bare repository metadata | license, tags, size | 0.60 |
| Unverified community description | general claims | 0.35 |

## 10. Content-Aware Dataset Fingerprinting

A Dataset Fingerprint is a compact evidence package describing what was actually observed in a bounded sample. It is not presented as a claim about the entire dataset. Sampling is adaptive: an initial sample establishes feasibility and coarse stability; additional sampling is performed only when a measurement is unstable and the expected information gain justifies the cost.

Sample-level conclusions are stored with sample size, acquisition method, randomization or selection rule, and measurement uncertainty. They are never promoted to full-dataset ground truth merely because the sample was convenient to access.

| Modality | Fingerprint evidence |
|---|---|
| Image | sample count; dimensions; unreadable rate; brightness/contrast summaries; blur estimate; exact/near-duplicate estimate; embedding clusters; class distribution |
| Tabular | row/column counts; missingness; type consistency; duplicate rows; categorical cardinality; numeric summaries; outliers; target balance |
| Text | empty/duplicate rate; length distribution; language indicators; label distribution; embedding clusters; vocabulary/task coverage |
| Object detection | annotation count; missing labels; bounding-box validity; class balance; image-level and box-level duplicate indicators |

## 11. Data Quality Analysis

Cleanlab-style model-assisted checks are included as a tool for estimating suspicious labels and other data issues when the required assumptions hold [3]. The project does not equate a Cleanlab output with absolute correctness. A probe model that generates poor probability estimates can make label-issue detection unreliable, so the workflow uses out-of-sample predictions obtained through cross-validation or an appropriate held-out procedure.

1. Obtain a task-appropriate sample and preserve original labels.
2. Create out-of-sample prediction probabilities with stratified validation where feasible.
3. Run label-issue analysis and record suspicious-example counts rather than silently deleting data.
4. Compute exact and near-duplicate statistics using hashes and embedding similarity.
5. Compute modality-specific structural and distributional diagnostics.
6. Store measurements with sample size and procedure in the evidence ledger.
7. Use the resulting metrics as bounded quality evidence, not as ground truth.

## 12. Task-Specific Utility Estimation

The central extension beyond conventional dataset recommendation is an estimate of whether a dataset appears useful for the stated ML task. DataPerf establishes the principle that data selection should be evaluated by the effect of selected data on downstream performance [2]. This project adapts that principle to bounded local computation by using lightweight probes rather than full model training.

| Probe type | Purpose | Local implementation |
|---|---|---|
| Linear/logistic probe | Measure whether a frozen representation separates target classes. | Extract compact embeddings; train a small classifier with stratified validation. |
| Small tree/linear model | Estimate tabular utility quickly. | Train on sampled features; report F1, RMSE, or R² as appropriate. |
| Frozen-model nearest-neighbor probe | Estimate semantic coverage without training. | Compare class/target clusters in embedding space. |
| Subset utility test | Estimate complementarity of candidate samples. | Combine sampled candidate data with a fixed reference set where one exists and measure validation change. |
| Coverage alignment | Check requested concept coverage. | Compare task ontology terms against labels, embeddings, and cluster summaries. |

### 12.1 Cold-start transfer estimate

Some useful datasets cannot be sampled because of gating, access restrictions, format limitations, or platform policy. Dropping them would create a new accessibility bias. For an unsampled dataset $d$, the system therefore computes a transfer estimate from its nearest already-probed datasets in description/metadata embedding space. The transferred value is explicitly labeled "Not Directly Observed," given a wider uncertainty interval, and down-weighted relative to direct evidence.

$$
\hat{u}(d) = \frac{\sum_{d' \in N_k(d)} w(d,d')\, u(d')}{\sum_{d' \in N_k(d)} w(d,d')},
\qquad
w(d,d') = \exp\!\left(-\frac{\lVert e(d) - e(d') \rVert^2}{2\sigma^2}\right)
$$

where $N_k(d)$ is the set of $k$ nearest already-probed datasets to $d$. Uncertainty increases as the nearest probed candidate becomes less similar, and the result is labeled `TransferredEstimate-NotDirectlyObserved` in the evidence ledger.

## 13. Popularity Bias and Long-Tail Discovery

Popularity is separated from suitability. The retrieval pipeline reserves a controlled exploration pool for datasets that satisfy task requirements but are not dominant on downloads, stars, citations, or related visibility signals. These candidates are then evaluated using the same evidence and utility criteria as mainstream candidates.

The system must not reward obscurity by itself. A lesser-known dataset reaches the final recommendation only when it provides relevant evidence, task utility, specialization, efficiency, diversity, or another user-relevant advantage.

```text
main_pool = relevant candidates ranked normally
long_tail_pool = relevant candidates in non-dominant popularity strata
long_tail_pool must still satisfy hard constraints
score both pools using the same utility/evidence/risk model
merge and diversify without allowing popularity to dominate suitability
```

### 13.1 Exposure Disparity Index

To test the claim that long-tail exploration reduces popularity-driven exposure, the benchmark partitions the candidate pool into popularity deciles. For decile $j$, $R_j$ is the share of human-judged relevant candidates in that decile, and $E_j$ is the share of final recommendation slots assigned to that decile. The Exposure Disparity Index is:

$$
\mathrm{EDI} = \frac{1}{2}\sum_j \left| E_j - R_j \right|
$$

$\mathrm{EDI} = 0$ means recommendation exposure tracks judged relevance regardless of popularity; higher values indicate greater distortion. A baseline retrieval system and the full system are evaluated under the same benchmark.

## 14. Diversified Recommendation

GIST formulates a max-min diversification problem that balances a utility objective with diversity [5,6]. The project adopts the principle on a bounded candidate pool rather than reproducing a web-scale implementation. A GIST-inspired greedy procedure, farthest-first selection, or a submodular facility-location alternative can be evaluated depending on compute results.

Dataset-family similarity is included in diversification. Mirrors, versions, and closely derived datasets should not occupy multiple final slots when they represent effectively the same coverage and evidence. This makes the recommendation set useful as a decision-support artifact instead of merely a sorted list.

## 15. Multi-Objective Recommendation Model

The final model is a multi-objective scoring and selection process rather than a fixed metadata-weighted average:

$$
R(D \mid Q) = \alpha \cdot \mathrm{Fit} + \beta \cdot \mathrm{Utility} + \gamma \cdot \mathrm{Evidence} + \delta \cdot \mathrm{Coverage} + \varepsilon \cdot \mathrm{Novelty} - \lambda \cdot \mathrm{Risk}
$$

| Term | Meaning |
|---|---|
| Fit | Compatibility with explicit task requirements and preferences. |
| Utility | Content-aware task evidence, including direct probes or weaker transfer estimates. |
| Evidence | Resolved support for important claims, reflecting belief and conflict. |
| Coverage | Representativeness and non-redundancy of the dataset relative to the task and recommendation set. |
| Novelty | Useful long-tail discovery value; not a reward for obscurity itself. |
| Risk | Uncertainty, contradiction, missing governance evidence, sampling limitations, and operational problems. |

The coefficients are not universal constants. Prototype values can be hand-set, then tuned against pairwise human relevance judgments with a simple learning-to-rank model such as logistic regression or a small gradient-boosted pairwise ranker when sufficient judgments are available. Popularity is excluded from the core suitability term and used only as contextual evidence, stratification, and bias-audit information.

## 16. Explanation and Recommendation Output

Each recommendation is an evidence-backed card rather than a single number.

```text
Dataset: <name>
Overall recommendation: <score>
Role: Best overall / Quality / Efficient / Hidden gem / Alternative
Evidence strength: High / Medium / Low

Why it fits
  - Task: measured / corroborated / source claim
  - Domain: ...
  - Modality: ...
  - Labels: ...
  - Observed sample quality: ...

Why it is not perfect
  - Unknown or conflicting evidence: ...
  - Operational limitations: ...
  - Utility is transferred rather than directly observed: ...

Why it appears here
  - Better measured utility / balance / coverage / efficiency
  - Adds a distinct dataset family or useful long-tail option

Sources and timestamps
  - Repository metadata
  - Dataset documentation / paper
  - Provenance / Croissant data
  - Sample analysis
```

The explanation must separate source claims from measured facts and explicitly expose unknowns. This output is also the artifact used in the human evaluation of trust and explanation quality (§19.4).

## 17. Local Implementation Strategy

The implementation is local-first, CPU-conscious, memory-aware, and cache-heavy. The central pipeline should be portable to ordinary personal computers with constrained resources. Optional local acceleration can be enabled when available, but it is not a dependency of the research design. Exact machine specifications are deliberately excluded from the proposal so the methodology remains hardware-independent.

### 17.1 Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install pandas numpy scipy scikit-learn
pip install sentence-transformers
pip install faiss-cpu
pip install cleanlab
pip install mlcroissant
# optional
pip install pyserini
pip install submodlib
```

Versions are pinned after the first stable build. The repository includes a lock/requirements file and an environment validation script. Dense embeddings are precomputed once and cached. Search results, source responses, fingerprints, and probe metrics are cached so experiments do not repeatedly consume external resources or recompute expensive features.

### 17.2 Repository ingestion

1. Create a source adapter per repository and prevent repository-specific fields from leaking into downstream ranking logic.
2. Assign a stable internal dataset identifier while retaining each native source identifier.
3. Normalize semantics, modality, format, counts, governance fields, timestamps, and popularity signals into the canonical schema.
4. Retain raw source snapshots or request/response data where terms permit reproducible storage.
5. Parse Croissant metadata where available and retain validation/provenance references.
6. Generate controlled retrieval text from name, description, tags, task semantics, and structured fields.
7. Precompute dense embeddings and build the BM25 index.
8. Cache every source fetch and record observation timestamps.

### 17.3 Legal and Terms-of-Service compliance for sample acquisition

1. Record whether the source permits automated/programmatic access for the intended educational or research use.
2. Record documented rate limits and implement a client-side rate limiter.
3. Check `robots.txt` or equivalent access policies where applicable.
4. Check dataset license terms separately from platform API terms; access permission does not imply reuse permission.
5. Prefer repository-provided viewers, previews, or documented sample endpoints over unnecessary bulk retrieval.
6. Log acquisition method and sample scope for reproducibility.

### 17.4 Requirement extraction

```json
{
  "task": "image classification",
  "domain": "plant disease",
  "modality": "image",
  "learning_type": "supervised",
  "label_type": "multiclass",
  "min_samples": 5000,
  "required_classes": null,
  "license_requirement": "academic_use",
  "hard_constraints": [],
  "soft_preferences": [],
  "unresolved_constraints": []
}
```

The schema rejects unknown fields or places them into an explicit unresolved-constraints field. This makes requirement-extraction errors observable and evaluable.

### 17.5 Hybrid retrieval

1. Run BM25 for exact terms such as domain vocabulary, disease names, modalities, formats, and target variables.
2. Run dense retrieval over the natural-language query plus structured task representation.
3. Fuse candidate lists with reciprocal-rank fusion or calibrated score normalization.
4. Apply hard constraints without collapsing the initial lexical/dense recall pool prematurely.
5. Deduplicate obvious mirrors and dataset-family duplicates.
6. Retain approximately 50–100 candidates for evidence analysis, subject to the M0 compute validation.

### 17.6 Sample acquisition and probing

Sampling proceeds in an evidence-preserving order: streaming or documented viewer APIs; small file/range requests where supported; public sample endpoints; repository-provided previews; finally, limited manual acquisition for benchmark datasets. Every sample-analysis record states the number of observations inspected and the acquisition method.

1. Check feasibility under a bounded time and memory budget.
2. If infeasible, use the transfer-estimate fallback rather than dropping the candidate.
3. Construct task-appropriate representations: image/text embeddings or normalized tabular features.
4. Compute structural and distributional diagnostics.
5. When labels are available, train a small probe model with stratified validation and obtain out-of-sample predictions.
6. Run Cleanlab-style label-issue analysis when assumptions are satisfied.
7. Compute class coverage, diversity, and representation statistics.
8. Persist intermediate metrics so ranking can be rerun without reprocessing samples.

### 17.7 Provenance and license workflow

```text
Repository claim ----+
Dataset card --------+
Paper / source ------+--> Evidence Resolver --> state + belief + plausibility + conflict
Croissant ------------+
Observed sample ------+
```

Automated license parsing is a classification aid, not legal advice. A clearly incompatible license can be treated as a hard exclusion when the user's usage constraint requires it. An unknown or conflicting license is not silently treated as compatible: the dataset may remain in the candidate pool, but the risk and confidence are lowered and the evidence path is shown to the user.

## 18. End-to-End Recommendation Algorithm

```python
def recommend(query, k=5):
    spec = extract_requirements(query)

    lexical = bm25_retrieve(spec.text_query, top_n=100)
    dense = dense_retrieve(spec.embedding_query, top_n=100)
    candidates = fuse_and_deduplicate(lexical, dense)
    candidates = hard_filter(candidates, spec.hard_constraints)

    raw_evidence = collect_evidence(candidates)
    evidence = {d: resolve_claims(raw_evidence[d]) for d in candidates}

    feasible = select_sample_accessible(candidates, budget=probe_budget)
    content = analyze_samples(feasible, spec)
    unsampled = [d for d in candidates if d not in feasible]
    transferred = transfer_estimate(unsampled, content)

    for d in candidates:
        d.fit = requirement_fit(d, spec)
        d.utility = content.get(d.id, transferred.get(d.id))
        d.evidence = mean_belief(evidence[d.id])
        d.risk = uncertainty_and_conflict(evidence[d.id])
        d.novelty = long_tail_value(d)
        d.coverage = coverage_value(d, spec)

    pool = multi_objective_rank(candidates)
    main, long_tail = split_exploration_pool(pool)
    final = diversified_select(main + long_tail, k=k)
    audit_exposure_disparity(pool, final)
    return explain_with_evidence(final, evidence, content)
```

## 19. Evaluation Framework

Evaluation is treated as a first-class research artifact. The system is not considered successful because its output merely appears plausible. Each architectural addition must demonstrate an effect on retrieval, ranking, discovery, trust, or efficiency.

### 19.1 Hidden-Gem benchmark

A purpose-built benchmark contains queries for which expert-approved relevant datasets include at least one lower-visibility candidate. A hidden gem is not defined only by low downloads; it must provide useful task evidence or relevance while being less visible than dominant alternatives. Popularity strata are frozen before evaluation to avoid leakage.

### 19.2 Robustness benchmark

Synthetic corruption tests remove or contradict selected metadata fields. Examples include removing class counts, weakening descriptions, marking licenses unknown, or introducing source disagreement. The expected behavior is graceful degradation: lower confidence, reliance on surviving evidence, and explicit uncertainty rather than confident inference from missing data.

### 19.3 Calibration

Confidence estimates are evaluated with reliability diagrams, Expected Calibration Error (ECE), and Brier score. A high-confidence label is shown in the interface only when the calibration study supports it. If calibration remains poor after tuning source priors, the system falls back to displaying raw evidence and source lists rather than presenting an uncalibrated synthesis as reliable.

$$
\mathrm{ECE} = \sum_{b} \frac{n_b}{N} \left|\, \mathrm{acc}(b) - \mathrm{conf}(b) \,\right|,
\qquad
\mathrm{Brier} = \frac{1}{N}\sum_{i=1}^{N} (p_i - o_i)^2
$$

### 19.4 Human evaluation of trust and explanation quality

A small study with approximately 10–15 participants with ML background compares a plain metadata card against the evidence-backed recommendation card for a fixed set of query–dataset examples. Participants rate trust in acting on the recommendation and understanding of why the dataset is or is not a fit, and indicate which card they would act on faster. A paired non-parametric comparison can be used when sample size is small and normality is not justified.

### 19.5 Primary metrics

| Metric group | Metrics |
|---|---|
| Retrieval | Precision@K, Recall@K, MRR, NDCG@K |
| Task utility | Probe performance, correlation with human relevance, downstream improvement where a reference set exists |
| Long-tail | Long-Tail Recall@K, Useful Long-Tail Rate, popularity rank of recommendations |
| Diversity | Intra-list embedding distance, family diversity, coverage |
| Evidence | Evidence coverage, contradiction rate, claim correctness |
| Calibration | ECE, Brier score, reliability diagrams |
| Robustness | Performance degradation under missing/conflicting metadata; abstention/flag rate |
| Efficiency | Latency, peak memory, sample count, CPU time, cache hit rate |

## 20. Baselines and Ablation Plan

1. LLM zero-shot recommendation: direct dataset recommendations without retrieval, evidence, or probing.
2. BM25-only retrieval.
3. Dense embedding-only retrieval.
4. DataFinder-style trained bi-encoder retrieval.
5. Hybrid retrieval without evidence scoring.
6. Hybrid retrieval + metadata suitability scoring.
7. Hybrid + evidence ledger + formal evidence resolution.
8. Hybrid + content-aware utility estimation, including transfer estimates.
9. Full system without diversification.
10. Full system with long-tail exploration and diversified reranking.

| Experiment | Comparison | Primary metrics |
|---|---|---|
| E1 Retrieval | BM25 vs. dense vs. DataFinder-style bi-encoder vs. hybrid | Recall@K, Precision@K, MRR, NDCG@K |
| E2 Suitability | Metadata-only vs. evidence-aware ranking | NDCG@K, human relevance, calibration |
| E3 Content utility | Without vs. with sample-aware probes | Utility correlation, probe/downstream improvement |
| E4 Quality evidence | Without vs. with Cleanlab-style analysis | Quality-risk separation, human verification rate |
| E5 Long-tail | Popularity-dominated vs. long-tail exploration | Long-Tail Recall@K, Useful Long-Tail Rate, EDI |
| E6 Diversity | Top-k utility ranking vs. diversified selection | Pairwise distance, family diversity, relevance |
| E7 Robustness | Complete vs. missing/conflicting metadata | Degradation, confidence calibration, flags |
| E8 Efficiency | Full vs. cached/reduced budgets | Latency, memory, sample count, CPU time |

## 21. Scope and Development Roadmap

The architecture supports many advanced components, but implementation proceeds through gated stages. A component is not allowed to consume disproportionate project time merely because it appears scientifically interesting.

### 21.1 Milestone M0: compute-budget validation

Before building the full evidence stage at scale, run one retrieval-to-probe cycle on approximately ten representative datasets. Record wall-clock time per stage, peak memory, sampling success rate, and probe cost. These measurements determine the practical candidate-pool size, sample size, and probe depth.

### 21.2 Staged roadmap

| Phase | Scope | Exit condition |
|---|---|---|
| A — Foundation | Repository adapters, canonical schema, metadata store, BM25 + dense retrieval. | Stable reproducible corpus and candidate retrieval. |
| B — Retrieval baseline | DataFinder-style baseline, benchmark queries, IR metrics. | Baseline results reproducible. |
| C — Evidence system | Evidence ledger, Croissant parsing, documentation/provenance, license states. | Every ranked candidate has auditable evidence records. |
| D — Content-aware analysis | Sampling, Dataset Fingerprint, modality diagnostics, quality checks. | Content evidence validated on at least two modalities where feasible. |
| E — Utility + long-tail | Task probes, transfer fallback, long-tail pool, family deduplication, diversified selection. | Hidden-gem and diversity metrics computed. |
| F — Full evaluation | Ablations, robustness, calibration, human study, efficiency. | All research questions answered with measured results. |

### 21.3 Stop conditions

- If dense retrieval cannot beat or complement lexical retrieval, revisit corpus normalization and query formulation before adding downstream complexity.
- If sample acquisition is unreliable, retain provenance/metadata evidence and explicitly label content evidence as unavailable or transferred.
- If probes exceed the validated compute budget, reduce candidate depth or sample size before relaxing evaluation rigor.
- If long-tail diversification materially reduces human relevance, tune the exploration quota rather than forcing novelty.
- If evidence-fusion calibration remains poor, show source-level evidence rather than synthesized confidence labels.
- If multimodal scope becomes too large, freeze one modality for the end-to-end experiment and retain the second as a validated extension.

## 22. Risks, Limitations, and Safeguards

| Risk | Why it matters | Safeguard |
|---|---|---|
| Incomplete metadata | Good datasets may be under-described. | Multiple evidence channels; Unknown state; content sampling. |
| Incorrect metadata | Repository claims may be stale or wrong. | Evidence ledger, cross-source comparison, contradiction flags. |
| License ambiguity | Machine-readable licenses can be absent or inconsistent. | No automated legal clearance; source comparison; hard exclusion only when incompatibility is clear and required. |
| Popularity feedback loop | Visible datasets can crowd out specialized options. | Separate popularity from utility; long-tail pool; EDI audit. |
| Probe bias | A probe can favor its own representation/model. | Use multiple probe types where practical; report assumptions. |
| Sampling bias | A bounded sample may not represent the full dataset. | Record sample scope and procedure; call all conclusions estimates. |
| Compute cost | Content analysis can become expensive. | M0 validation; adaptive sampling; caching; bounded candidate pool. |
| Lineage duplication | Mirrors/versions can consume multiple recommendation slots. | Stable IDs; family clustering; diversified selection. |
| Overclaiming | Scores can appear more certain than evidence allows. | Calibration gates, explicit unknowns, source-level evidence, and cautious language. |
| Access/ToS risk | Automated sampling can violate platform restrictions. | Per-source compliance checklist, documented rate limits, caching-first design. |

## 23. Expected Project Contribution

The project is not positioned as a new language model or a generic RAG interface. Its expected contribution is a reproducible methodology for moving from dataset retrieval to evidence-driven dataset selection.

- An integrated pipeline that combines retrieval, provenance, sample-derived evidence, task utility, and diversified recommendation under a single decision process.
- A formal evidence-resolution methodology, evaluated as a candidate core contribution, that distinguishes uncertainty from conflict rather than collapsing both into a single average score.
- A content-aware suitability layer that supplements publisher descriptions with observed dataset behavior under bounded sampling.
- A popularity-neutral discovery mechanism with an explicit benchmark for useful long-tail datasets and measured exposure disparity.
- An uncertainty-aware explanation format that tells users not only why a dataset fits, but also what is unknown, conflicting, or merely inferred.
- A local-first and reproducible implementation strategy that can be executed on ordinary personal computers without proprietary APIs at the core.
- A complete evaluation and ablation framework separating retrieval quality, utility, evidence quality, diversity, bias, and compute cost.

Novelty is claimed only where the resulting method and experiments establish a defensible distinction from prior work. Established algorithms such as BM25, bi-encoders, Cleanlab methods, Croissant, Dempster–Shafer fusion, submodular selection, and GIST-inspired diversification are treated as research foundations and evaluated in the specific dataset-intelligence setting.

## 24. Expected User-Facing Result

For a query such as "I want to build a CNN model for classifying plant diseases from leaf images; I need a multi-class dataset," the system returns a recommendation set with distinct roles rather than five near-duplicates:

| Role | Purpose |
|---|---|
| Best overall | Highest evidence-backed task utility under explicit constraints. |
| Best data-quality profile | Strongest measured structural and sample-quality evidence. |
| Best efficient option | A smaller or computationally convenient dataset with strong task fit. |
| Hidden-gem option | A less popular but evidence-supported dataset that adds genuine value. |
| Best alternative | A distinct dataset family with a different trade-off or coverage profile. |

Every result includes source links, evidence strength, main reasons, limitations, uncertainty, and the factors that caused it to outrank or differ from nearby alternatives. The system does not claim that every dataset fact is verified; it communicates the strength and provenance of what is actually known.

## 25. References

1. Lin, V. et al. "DataFinder: Scientific Dataset Recommendation from Natural Language." *WSDM 2023*. https://arxiv.org/abs/2305.16636. Official implementation: https://github.com/viswavi/datafinder.
2. Mazumder, M. et al. "DataPerf: Benchmarks for Data-Centric AI Development." *arXiv:2207.10062*. Official repository: https://github.com/mlcommons/dataperf.
3. Northcutt, C. et al. "Confident Learning: Estimating Uncertainty in Dataset Labels." *NeurIPS 2021*. Implementation/documentation: https://github.com/cleanlab/cleanlab and https://docs.cleanlab.ai/.
4. MLCommons. Croissant Dataset Metadata Format Specification, including provenance and usage-policy extensions. https://docs.mlcommons.org/croissant/.
5. Zadimoghaddam, M. et al. "GIST: Greedy Independent Set Thresholding for Max-Min Diversification with Submodular Utility." *NeurIPS 2025 / arXiv:2405.18754*. https://arxiv.org/abs/2405.18754.
6. Google Research. "Introducing GIST: The Next Stage in Smart Sampling." https://research.google/blog/introducing-gist-the-next-stage-in-smart-sampling/.
7. Data Provenance Initiative and public reporting on dataset licensing/provenance quality in widely used ML datasets. Used as motivation for verification and uncertainty rather than treating repository license fields as ground truth.
8. Google Research. Dataset Search research and dataset-discovery literature on heterogeneous web-scale dataset indexing.
9. Hugging Face Hub documentation on dataset cards, dataset metadata, and dataset viewer functionality. https://huggingface.co/docs/hub/datasets-cards.
10. Shafer, G. *A Mathematical Theory of Evidence.* Princeton University Press, 1976.
11. Dempster, A. P. "A Generalization of Bayesian Inference." *Journal of the Royal Statistical Society, Series B*, 1968.
12. Guo, C. et al. "On Calibration of Modern Neural Networks." *ICML 2017*.

---

## Appendix A. Practical Repository Structure

```text
capstone-dataset-intelligence/
|-- data/
|   |-- raw/                  # source snapshots where permitted
|   |-- normalized/           # canonical dataset records
|   |-- evidence/             # claim-level evidence ledger
|   |-- fingerprints/         # cached sample-level measurements
|   `-- benchmarks/           # query, relevance and robustness data
|-- indexes/
|   |-- bm25/
|   `-- dense/
|-- src/
|   |-- ingestion/            # source adapters + compliance metadata
|   |-- normalization/
|   |-- retrieval/
|   |-- evidence/              # evidence resolver
|   |-- probing/               # fingerprints, quality, utility
|   |-- ranking/
|   |-- diversification/
|   `-- reporting/             # explanation cards + CLI
|-- experiments/
|   |-- baselines/
|   |-- ablations/
|   |-- robustness/
|   |-- calibration/
|   |-- bias_audit/
|   `-- long_tail/
|-- configs/
|-- scripts/
|-- tests/
|-- requirements.txt
`-- README.md
```

## Appendix B. Minimum Viable System vs. Full Research System

| Component | MVP | Full research system |
|---|---|---|
| Requirements | Structured extraction with schema. | Extraction evaluation and fallback parser. |
| Corpus | 3–5 sources; canonical schema. | Expanded source set, stronger lineage normalization. |
| Retrieval | BM25 + dense embeddings. | Add trained bi-encoder baseline. |
| Evidence | Basic claim ledger. | Full provenance, conflict, and formal evidence resolution. |
| Content | One modality for first end-to-end validation. | At least two modalities where feasible. |
| Quality | Basic structural diagnostics. | Cleanlab-style checks and uncertainty-aware aggregation. |
| Utility | Lightweight probe. | Probe comparison + transfer fallback + downstream validation where possible. |
| Long-tail | Controlled candidate reserve. | Benchmark, EDI, and useful-long-tail metrics. |
| Diversification | Greedy baseline. | GIST-inspired / submodular comparison. |
| Explanation | Top reasons + sources. | Evidence-backed report + limitations + counterfactual/rejection reasons. |
| Evaluation | IR metrics. | IR + utility + long-tail + robustness + calibration + human trust + efficiency. |
| Interface | Minimal CLI. | CLI plus polished demo/report artifact. |

## Appendix C. Implementation Stop Conditions

- If hybrid retrieval does not outperform or complement the strongest baseline, revisit normalization and query representation before tuning downstream modules.
- If sample acquisition fails across a large fraction of sources, preserve evidence-first ranking and use the transfer fallback rather than discarding inaccessible candidates.
- If probe time exceeds the validated budget, reduce candidate depth and sampling before sacrificing benchmark rigor.
- If long-tail exploration lowers human-rated usefulness, reduce its allocation and report the trade-off instead of forcing novelty.
- If evidence confidence cannot be calibrated, remove synthesized confidence labels and expose raw source-level evidence.
- If two-modality scope becomes infeasible, complete one modality end-to-end and validate the second as an extension.

## Appendix D. Worked Evidence-Resolution Example

Consider the claim "license of dataset $d$ is CC BY 4.0" with three sources: a bare repository field asserting true ($r_1 = 0.60$), an official dataset card asserting true ($r_2 = 0.70$), and an unverified mirror README asserting false ($r_3 = 0.35$). Each source receives a reliability prior below one, so residual mass remains on uncertainty. The two supporting sources combine without direct conflict; introducing the opposing source creates conflict mass.

**Step 1 — individual masses.**
$m_1(\top)=0.60,\ m_1(\Theta)=0.40$; $\ m_2(\top)=0.70,\ m_2(\Theta)=0.30$; $\ m_3(\bot)=0.35,\ m_3(\Theta)=0.65$.

**Step 2 — combine the two supporting sources.** No conflict arises since both support $\top$:
$m_{12}(\top) = 0.60(0.70) + 0.60(0.30) + 0.40(0.70) = 0.88$, $\quad m_{12}(\Theta) = 0.40(0.30) = 0.12$.

**Step 3 — introduce the opposing source.** Conflict mass $K = m_{12}(\top)\,m_3(\bot) = 0.88 \times 0.35 = 0.308$. After renormalizing by $1-K$: $\mathrm{Bel}(\top) \approx 0.827$, $\mathrm{Pl}(\top) \approx 0.940$, $K_{\text{total}} \approx 0.308$.

**Interpretation.** The important behavior is qualitative and measurable: because $K_{\text{total}}$ exceeds the calibrated conflict threshold, the system surfaces the claim as **Conflicting** rather than averaging the three statements into a neutral-looking mid-range score. If later evidence resolves the discrepancy, the claim can move to **Corroborated** or **Verified**. This demonstrates why disagreement and ignorance must remain separate states.

```text
Support sources  -> high belief in CC BY 4.0
Opposing source  -> non-zero conflict
Final state      -> Conflicting, when conflict crosses the calibrated threshold
User output      -> show both supporting and opposing sources; do not claim legal clearance
```

## Appendix E. Suggested Evaluation Dataset and Query Construction

The benchmark should contain a mixture of mainstream and specialized tasks across the supported modalities. Each query records structured requirements, relevance judgments, popularity strata, evidence sources, and whether at least one useful lower-visibility candidate exists. The benchmark should be frozen before model tuning to reduce evaluation leakage.

| Query attribute | Example |
|---|---|
| Task | Image classification, semantic segmentation, regression, retrieval, object detection |
| Domain | Plant disease, medical imaging, traffic, remote sensing, finance, language |
| Modality | Image, tabular, text, multimodal |
| Constraints | Minimum sample count, required classes, format, intended use, domain restrictions |
| Judgments | Relevant, partially relevant, unsuitable; optionally pairwise preference |
| Popularity stratum | Decile or percentile based on frozen community-visibility signals |
| Hidden gem | Lower-visibility candidate judged useful by experts or strong task evidence |

## Appendix F. Hardware-Agnostic Local Compute Policy

- Prefer compact embedding and instruction models for local inference; model size is selected from measured latency and memory rather than brand preference.
- Precompute dataset embeddings and cache them; query-time operations should be lightweight.
- Use CPU-compatible vector search and small candidate pools by default.
- Use adaptive sampling instead of fixed large sample counts.
- Persist every expensive intermediate result and configuration needed to reproduce the ranking.
- Treat local acceleration as optional. The research claims must remain reproducible without depending on a particular accelerator.

**Implementation stance.** The project should follow the staged roadmap, start with the M0 compute validation, and only then commit to the depth of content probing, evidence fusion, and diversification that the measured environment can support. The research objective is measured improvement and defensible evidence, not maximum feature count.
