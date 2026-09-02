# Evidence-Driven Dataset Intelligence and Recommendation System

## Project Specification for Implementation

**Status:** Implementation-ready specification  
**Domain:** Machine Learning, Deep Learning, Computer Vision, dataset discovery and selection  
**Primary objective:** Move from dataset retrieval toward evidence-driven, task-specific dataset selection.

---

## 1. Product Definition

Build a local-first system that accepts a natural-language ML/DL/CV project description and recommends a small, useful set of datasets from multiple public repositories.

The system must do more than semantic search. It should:

1. Understand the user's task and constraints.
2. Retrieve a broad candidate pool from multiple sources.
3. Treat repository metadata as evidence, not ground truth.
4. Gather additional evidence from dataset documentation, provenance, structured metadata, and accessible samples.
5. Estimate content-aware, task-specific utility with bounded computation.
6. Preserve relevant lesser-known datasets through an explicit long-tail exploration path.
7. Handle missing and conflicting evidence explicitly.
8. Produce a diversified recommendation set rather than five near-duplicates.
9. Explain why each dataset is recommended, what was measured, what was only claimed, and what remains unknown.
10. Log enough evidence and intermediate results for reproducibility and later evaluation.

The project is **not** a generic chatbot, a plain vector database over dataset descriptions, or a web-scale search engine.

---

## 2. Core Research Questions

### RQ1 — Retrieval
Can hybrid lexical and semantic retrieval identify relevant datasets more effectively than lexical-only, dense-only, and trained-retriever baselines?

### RQ2 — Utility
Can content-aware evidence and lightweight task probes improve dataset selection beyond metadata-only suitability ranking?

### RQ3 — Evidence Reliability
Can explicit evidence resolution improve the reliability and calibration of dataset claims when sources are incomplete or contradictory?

### RQ4 — Long-Tail Discovery
Can controlled popularity-neutral exploration increase the discovery of useful lesser-known datasets without materially reducing relevance?

### RQ5 — Recommendation Set Quality
Can diversified selection produce a more useful final recommendation set than simply returning the top five scores?

---

## 3. Research Positioning

Dataset recommendation is already an information-retrieval problem. DataFinder demonstrates strong lexical and dense/bi-encoder retrieval for natural-language dataset queries. Therefore, the retrieval layer is a baseline and candidate-generation mechanism, not the primary novelty.

The project differentiates itself by moving the optimization target from:

> Which dataset looks semantically relevant?

Toward:

> Which dataset is most defensibly useful for this task, what evidence supports that decision, what is uncertain, and which useful alternatives would otherwise be missed?

Established methods are building blocks, not isolated novelty claims:

- **DataFinder** → retrieval baseline and retrieval evaluation.
- **DataPerf** → data-centric selection and downstream-utility perspective.
- **Cleanlab** → model-assisted data-quality evidence.
- **Croissant** → standardized metadata, structure, provenance and policy representation.
- **GIST** → utility + diversity selection principle.
- **Dataset Cards / documentation** → evidence source for intended use, scope and limitations.
- **Dempster–Shafer evidence fusion** → candidate methodology for resolving heterogeneous evidence; novelty is not claimed from the mathematical rule alone.

The contribution must be established experimentally through integration and evaluation.

---

## 4. System Boundary

### In scope

- Natural-language requirement extraction.
- Multi-source dataset ingestion.
- Canonical dataset normalization.
- Source-specific provenance retention.
- BM25/lexical retrieval.
- Dense retrieval.
- Hybrid candidate generation.
- Hard-constraint filtering.
- Evidence ledger.
- Evidence resolution and uncertainty representation.
- Dataset Fingerprinting from bounded samples.
- Modality-specific diagnostics.
- Lightweight task-utility estimation.
- Long-tail exploration.
- Dataset-family deduplication.
- Diversified multi-objective reranking.
- Evidence-backed explanations.
- CLI demonstration artifact.
- Evaluation, ablation, robustness, calibration and efficiency measurement.

### Out of scope for the core system

- Training a large language model from scratch.
- Full forensic auditing of every file in every dataset.
- Legal clearance or legal advice.
- Web-scale optimization over millions of samples.
- Indiscriminate complete downloads of all candidate datasets.
- Dependence on proprietary APIs for the core pipeline.

Advanced methods such as trained retrievers, Cleanlab integration, formal evidence fusion, GIST-inspired selection and broader human evaluation are included only when justified by experiments and available compute.

---

## 5. End-to-End Architecture

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
        +-------------------------+
        |                         |
        v                         v
[Hard Constraint Policy]   [Semantic Query Expansion]
        |                         |
        +------------+------------+
                     v
          [HYBRID CANDIDATE RETRIEVAL]
              BM25 + dense embeddings
                     |
                     v
             [CANDIDATE POOL 50-100]
                     |
          +----------+----------+
          |                     |
          v                     v
 [EVIDENCE LAYER]       [CONTENT EVIDENCE]
 metadata/docs/         samples/fingerprints/
 provenance/license     quality/probes
          |                     |
          +----------+----------+
                     v
              [EVIDENCE LEDGER]
                     |
                     v
          [EVIDENCE RESOLUTION]
        belief / plausibility / conflict
                     |
                     v
        [TASK UTILITY ESTIMATION]
                     |
                     v
        [LONG-TAIL EXPLORATION]
                     |
                     v
        [DIVERSIFIED RERANKING]
                     |
                     v
        [FINAL RECOMMENDATION SET]
     overall | quality | efficient |
     hidden gem | alternative
                     |
                     v
        [EVIDENCE-BACKED REPORT]
```

The 50–100 candidate range is a starting hypothesis only. Final pool size and probe depth are determined by the M0 compute-budget experiment.

---

## 6. Canonical Dataset Representation

Every source gets a dedicated adapter. Repository-specific structures must not leak into ranking logic.

### Required record groups

| Group | Representative fields |
|---|---|
| Identity | internal_id, source_id, source_name, dataset_name, URL, version/family identifiers |
| Semantics | description, task, domain, modality, learning_type, target, tags, intended_use |
| Structure | sample_count, class_count, schema, formats, splits, feature information |
| Governance | license_claim, usage_policy, citation, creators, provenance_links, documentation_links |
| Community context | downloads, stars, ratings, citations, update timestamps, repository activity |
| Observed content | sample_count_observed, modality diagnostics, duplicate rate, embedding statistics, probe results |
| Operational | access method, sampling feasibility, cache state, time cost, risk flags |

Use Croissant where available as a standards-aligned representation, but retain native source metadata and raw provenance references.

---

## 7. Requirement Extraction Contract

The requirement parser must produce a constrained schema such as:

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

Rules:

- Unknown fields are rejected or moved to `unresolved_constraints`.
- Hard requirements are never silently treated as soft preferences.
- Unresolved requirements are visible to downstream logic and, where appropriate, to the user.
- Requirement extraction is evaluated independently from retrieval.

---

## 8. Retrieval Layer

### Stage 1 — Sparse retrieval
Use BM25 for exact terms, rare domain vocabulary, names, formats, modalities and target variables.

### Stage 2 — Dense retrieval
Use compact sentence/document embeddings over the natural-language query plus structured task representation.

### Stage 3 — Fusion
Combine lexical and dense candidates using reciprocal-rank fusion or calibrated score normalization.

### Stage 4 — Hard constraints
Apply mandatory constraints without destroying the initial recall pool prematurely.

### Stage 5 — Family deduplication
Remove obvious mirrors and highly redundant dataset families before expensive analysis.

### Target
Retain approximately 50–100 candidates for evidence analysis, subject to the measured compute budget.

---

## 9. Evidence Ledger

The ledger is a core subsystem and is stored independently from the final ranking score.

Each claim should contain:

```text
Dataset ID
Claim type
Claim value
Source
Source timestamp
Evidence type
Reliability indicator / prior
Observation procedure
Sample size (when applicable)
Contradictions
Resolution state
Belief / plausibility (when fusion is used)
```

### Evidence states

| State | Meaning |
|---|---|
| Measured | Computed from an accessible sample/resource. |
| Corroborated | Supported by multiple independent sources or source + computation. |
| Single-source claim | Present in one source without independent validation. |
| Conflicting | Sources disagree or source conflicts with observation. |
| Unknown | Evidence unavailable or inaccessible. |

`Unknown` is not a neutral positive value.

---

## 10. Formal Evidence Resolution

Dempster–Shafer evidence fusion is an **experimental methodology**, not an automatic novelty claim.

For claims with multiple explicit sources:

- represent true/false as the frame of discernment;
- assign bounded source reliability priors;
- preserve residual uncertainty mass;
- combine evidence;
- retain belief, plausibility and conflict;
- map these quantities to user-facing trust states;
- validate and tune source priors using held-out correctness/calibration data.

The system must be able to fall back to raw source lists and evidence counts if synthesized confidence is poorly calibrated.

---

## 11. Dataset Fingerprinting

A Dataset Fingerprint is a compact package of **observed evidence from a bounded sample**. It is not a claim about the complete dataset.

Sampling should be adaptive:

1. obtain a small initial sample;
2. estimate feasibility and coarse stability;
3. expand only when a measurement is unstable and added computation is justified.

Record sample size, acquisition method, selection/randomization procedure and measurement uncertainty.

### Image evidence

- dimensions
- unreadable/corrupt rate
- brightness/contrast summaries
- blur estimate
- exact and near-duplicate rate
- embedding clusters
- class distribution

### Tabular evidence

- row/column counts
- missingness
- type consistency
- duplicate rows
- categorical cardinality
- numeric summaries
- outliers
- target balance

### Text evidence

- empty/duplicate rate
- length distribution
- language indicators
- label distribution
- embedding clusters
- task/vocabulary coverage

### Detection evidence

- annotation counts
- missing labels
- bounding-box validity
- class balance
- duplicate indicators

---

## 12. Data Quality Analysis

Cleanlab-style analysis is evidence, not ground truth.

Workflow:

1. Preserve original labels.
2. Obtain out-of-sample prediction probabilities using cross-validation or an appropriate holdout.
3. Estimate suspicious label issues.
4. Compute exact/near duplicates.
5. Compute modality-specific structural diagnostics.
6. Store every measurement with sample size and procedure.
7. Penalize or flag issues only according to validated ranking behavior.

Do not silently delete suspicious records during analysis.

---

## 13. Task-Specific Utility

The central ranking improvement is a lightweight estimate of whether a candidate appears useful for the user's actual task.

Preferred probes, subject to task and compute budget:

| Probe | Use |
|---|---|
| Linear/logistic probe | Frozen representation separability for classification. |
| Small tree/linear model | Fast tabular utility estimate. |
| Frozen nearest-neighbor analysis | Coverage and semantic structure without model training. |
| Subset utility test | Complementarity relative to an available fixed reference set. |
| Coverage alignment | Compare requested concepts with labels, embeddings and clusters. |

A probe result is an estimate under a specific sample, representation and evaluation protocol. It is not a guarantee of full-dataset model performance.

### Cold-start fallback

If a dataset cannot be sampled because of access restrictions or technical limitations, do not drop it automatically.

Estimate utility from nearby already-probed datasets in embedding space. Mark the result explicitly as:

`TransferredEstimate-NotDirectlyObserved`

and widen its uncertainty / lower its influence relative to direct observations.

---

## 14. Popularity Bias and Long-Tail Discovery

Popularity signals include downloads, stars, ratings, citations, reviews and repository visibility.

They are **contextual evidence, not suitability labels**.

The recommendation pipeline must maintain an explicit exploration path:

```text
Main pool = normally retrieved relevant candidates
Long-tail pool = relevant candidates in non-dominant visibility strata
                + same hard constraints
                + same evidence/utility evaluation
```

A lesser-known dataset reaches the final recommendation only when it provides real task-relevant value such as utility, specialization, efficiency, diversity or better evidence.

Do not replace popularity bias with obscurity bias.

### Exposure Disparity Index

Measure the gap between recommendation exposure across popularity strata and the distribution of human-judged relevant candidates. Use this as a bias-audit metric rather than assuming diversification automatically reduces bias.

---

## 15. Diversified Recommendation

The final output is a set, not merely a sorted list.

Candidate recommendation roles:

1. Best overall.
2. Best data-quality profile.
3. Best efficient option.
4. Hidden-gem option.
5. Best alternative.

Avoid multiple slots being consumed by:

- mirrors;
- versions of the same dataset;
- highly derived variants;
- candidates with effectively identical coverage.

GIST is used as a guiding principle for utility + diversity. A bounded GIST-inspired greedy procedure, farthest-first selection, or submodular facility-location alternative may be selected after the M0 compute test.

---

## 16. Multi-Objective Ranking

Use a multi-objective formulation rather than a fixed metadata average:

$$
R(D \mid Q) =
\alpha Fit +
\beta Utility +
\gamma Evidence +
\delta Coverage +
\epsilon Novelty -
\lambda Risk
$$

Interpretation:

- **Fit:** explicit task requirements.
- **Utility:** direct probe or weaker transfer estimate.
- **Evidence:** support strength and conflict.
- **Coverage:** task coverage, representativeness and non-redundancy.
- **Novelty:** useful long-tail discovery value.
- **Risk:** uncertainty, contradictions, governance gaps and operational problems.

Popularity is excluded from the core suitability term.

Initial weights may be hand-designed. Later, where enough judgments exist, tune them using pairwise relevance data and a simple learning-to-rank model.

---

## 17. Explanation Contract

Every recommendation must include:

```text
Dataset
Overall score
Recommendation role
Evidence strength

Why it fits
- task
- domain
- modality
- labels
- observed sample evidence

Why it is not perfect
- unknown evidence
- conflicts
- operational limitations
- transferred rather than direct utility, if applicable

Why it appears here
- utility / coverage / efficiency / long-tail advantage
- distinction from nearby alternatives

Sources and timestamps
```

Do not let the LLM invent unsupported facts.

---

## 18. Local Implementation Policy

The system is local-first, CPU-conscious, memory-aware and cache-heavy.

### Initial dependency direction

- Python 3.10+
- pandas
- numpy
- scipy
- scikit-learn
- sentence-transformers
- faiss-cpu
- cleanlab
- mlcroissant
- pyserini (optional)
- submodlib (optional)

Exact package versions are pinned after the first stable environment build.

### Caching

Cache:

- source responses;
- normalized records;
- embeddings;
- retrieval results;
- sample fingerprints;
- probe metrics;
- evidence-resolution results;
- experiment configurations.

Never repeatedly call a remote source just because a ranking experiment is being rerun.

### Sample acquisition order

1. documented viewer/streaming API;
2. small file/range request;
3. public sample endpoint;
4. repository-provided preview;
5. limited manual acquisition for benchmark datasets.

Each source adapter must track terms/rate limits/access policy and the acquisition method used.

---

## 19. Evaluation Requirements

### Retrieval metrics

- Precision@K
- Recall@K
- nDCG@K
- MRR

### Long-tail metrics

- hidden-gem recall@K;
- hidden-gem rank;
- useful long-tail rate;
- Exposure Disparity Index.

### Diversity metrics

- average pairwise distance;
- family-level redundancy;
- coverage of distinct dataset families.

### Utility metrics

- probe performance;
- downstream improvement where a controlled reference exists;
- stability across probe runs.

### Evidence metrics

- claim correctness;
- confidence calibration;
- Expected Calibration Error;
- Brier score;
- conflict detection accuracy.

### Human evaluation

Compare plain metadata cards with evidence-backed recommendation cards on trust, understanding and actionability.

### Robustness

Deliberately remove or corrupt metadata fields and measure:

- recommendation degradation;
- confidence degradation;
- correct transition toward `Unknown` or `Conflicting` states;
- recovery from alternative evidence.

### Efficiency

Measure:

- wall-clock time;
- peak memory;
- sample acquisition success rate;
- probe cost per candidate;
- end-to-end query latency.

---

## 20. Baseline and Ablation Ladder

Implement and evaluate progressively:

1. LLM zero-shot recommendation.
2. BM25-only.
3. Dense embedding-only.
4. DataFinder-style trained bi-encoder.
5. Hybrid retrieval without evidence scoring.
6. Hybrid + metadata suitability scoring.
7. + evidence ledger / evidence resolution.
8. + content-aware utility estimation.
9. Full system without diversification.
10. Full system with long-tail exploration + diversified reranking.

No component should be described as beneficial until the corresponding ablation demonstrates its effect.

---

## 21. Development Roadmap

### M0 — Bootstrap and compute validation

- inspect repository;
- establish project structure;
- freeze development rules;
- validate dependencies;
- benchmark a small end-to-end sample on roughly 10 real datasets;
- record time, memory and source-access failures.

**Stop condition:** do not scale candidate analysis until compute budgets are known.

### M1 — Corpus and canonical schema

- source adapters;
- stable IDs;
- normalization;
- provenance retention;
- cache layer.

### M2 — Retrieval baseline

- BM25;
- dense embeddings;
- fusion;
- retrieval benchmark.

### M3 — Evidence system

- evidence ledger;
- Croissant parsing;
- source claims;
- conflict representation;
- provisional resolver.

### M4 — Content evidence

- sample acquisition;
- dataset fingerprint;
- modality diagnostics;
- duplicate/quality analysis.

### M5 — Utility

- lightweight probes;
- utility score;
- cold-start transfer estimate.

### M6 — Long-tail and diversification

- exploration pool;
- popularity audit;
- dataset-family deduplication;
- diversified selection.

### M7 — Ranking and explanations

- multi-objective ranker;
- recommendation cards;
- CLI output.

### M8 — Research evaluation

- benchmark freeze;
- ablations;
- robustness;
- calibration;
- human evaluation;
- final report.

---

## 22. Stop Conditions

Immediately reduce scope when any of the following occurs:

- sample probing exceeds the validated time budget;
- memory becomes unstable on the target class of machines;
- source access is inconsistent or violates documented terms;
- a component adds complexity without measurable research value;
- a method cannot be evaluated with the available benchmark;
- a module causes the ranking to become impossible to reproduce;
- the team is implementing features faster than it can test and document them.

Prefer a smaller, measured system over a large unvalidated pipeline.

---

## 23. Repository Contract

Recommended structure:

```text
capstone-dataset-intelligence/
├── AGENTS.md
├── README.md
├── docs/
│   ├── PROJECT_SPEC.md
│   └── RESEARCH_FOUNDATION.md
├── data/
│   ├── raw/
│   ├── normalized/
│   ├── evidence/
│   ├── fingerprints/
│   └── benchmarks/
├── indexes/
│   ├── bm25/
│   └── dense/
├── src/
│   ├── ingestion/
│   ├── normalization/
│   ├── retrieval/
│   ├── evidence/
│   ├── probing/
│   ├── ranking/
│   ├── diversification/
│   └── reporting/
├── experiments/
│   ├── baselines/
│   ├── ablations/
│   ├── robustness/
│   └── long_tail/
├── configs/
├── scripts/
├── tests/
├── requirements.txt
└── README.md
```

### Development rules

- Inspect before modifying.
- Work in one milestone at a time.
- Keep source adapters isolated.
- Preserve evidence and provenance.
- Keep unknown values explicit.
- Never use popularity as a quality proxy.
- Never claim legal clearance.
- Never present sample measurements as complete-dataset truth.
- Add tests for every substantial module.
- Review the Git diff before committing.
- Use small, coherent commits.
- Do not rewrite history.
- Push only completed, tested milestones.
- Stop at milestone boundaries.

---

## 24. Definition of Done

A milestone is complete only when:

1. the code is implemented;
2. the relevant tests pass;
3. the design/documentation is updated;
4. cached artifacts or schemas are reproducible;
5. the Git diff contains no unrelated changes;
6. the commit message describes one coherent change;
7. the commit is pushed when the repository workflow permits it;
8. the milestone report states what changed and what remains.

The final research artifact is considered successful only if it demonstrates measurable behavior, not merely plausible recommendations.
