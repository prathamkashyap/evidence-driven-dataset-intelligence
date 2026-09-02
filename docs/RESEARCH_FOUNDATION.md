# Research Foundation

## Evidence-Driven Dataset Intelligence and Recommendation System

This document contains the research foundation used to justify the project architecture. It separates established prior work from adaptations and proposed experiments.

---

## 1. Executive Synthesis

The literature and technical ecosystem indicate that dataset recommendation is already a meaningful information-retrieval problem, while data selection, data cleaning, dataset governance, provenance and diversity have independently developed into data-centric research areas.

The project therefore combines established capabilities into a single task-specific decision pipeline:

```text
Natural-language task
        ↓
Requirement representation
        ↓
Hybrid retrieval
        ↓
Evidence acquisition
        ↓
Content/data analysis
        ↓
Task-specific utility estimate
        ↓
Evidence/confidence resolution
        ↓
Long-tail exploration
        ↓
Utility + diversity selection
        ↓
Explainable recommendation
```

The important research shift is from **retrieval** to **selection under evidence and uncertainty**.

---

## 2. DataFinder

### What it establishes

DataFinder frames scientific dataset recommendation as information retrieval over natural-language research needs and dataset representations. Its evaluation includes lexical retrieval, nearest-neighbor methods and a trained dense bi-encoder.

### Methods to adopt

- BM25 as a lexical baseline.
- Dense embeddings as a semantic baseline.
- Bi-encoder retrieval as a strong learned-retrieval baseline.
- Query–dataset benchmark construction.
- Precision@K, Recall@K and MRR-style evaluation.

### What it does not solve for this project

The research foundation describes DataFinder as depending primarily on dataset metadata and textual descriptions and not inspecting raw dataset contents. This leaves an opportunity to investigate content-aware suitability and evidence quality rather than treating retrieval relevance as sufficient.

### Project implication

Do not claim novelty from:

- natural-language dataset queries;
- RAG over dataset descriptions;
- vector retrieval;
- dense bi-encoders.

Use DataFinder as a benchmark/reference point.

### Local implementation lesson

Start with off-the-shelf dense retrieval and BM25. Only consider training a specialized bi-encoder after the baseline retrieval system is measured and a sufficient query–dataset training set exists.

---

## 3. DataPerf

### What it establishes

DataPerf treats data-centric AI tasks such as data selection, cleaning and acquisition as benchmarkable optimization problems rather than treating training data as a fixed background artifact.

Representative challenge patterns include:

- selecting useful subsets for speech/vision tasks;
- cleaning or ranking suspicious data;
- evaluating data selection through downstream model metrics;
- valuing data under acquisition constraints.

### Methods to adopt

The central lesson is methodological:

> A dataset or subset should ultimately be judged partly by how useful it is for an ML objective.

For our system this motivates a lightweight **task-utility probe**.

### Adaptation to local compute

Full DataPerf-style experiments can be expensive. We adapt the principle to:

- frozen representations;
- linear or logistic probes;
- small tabular models;
- nearest-neighbor structure;
- controlled subset utility tests.

The project should measure utility under a fixed, explicit probe protocol and not present probe performance as a universal guarantee.

---

## 4. Cleanlab and Model-Assisted Data Quality

### What it establishes

Cleanlab operationalizes confident-learning approaches for identifying suspicious labels and other data issues. Its workflows use model prediction probabilities to identify likely label problems.

The research foundation identifies additional uses around duplicates and outliers.

### Methods to adopt

For datasets where assumptions hold:

1. construct appropriate out-of-sample prediction probabilities;
2. estimate suspicious label issues;
3. retain issue counts and scores as evidence;
4. compute duplicate and outlier indicators where feasible.

### Important limitation

Cleanlab outputs depend on the quality of the model probabilities. Small or strongly imbalanced datasets may yield unstable estimates, and a model's confidence is not itself ground truth.

Therefore:

- do not define "quality" as `1 - cleanlab_error_rate` without validation;
- do not silently delete suspicious samples;
- store issue estimates with sample size and method.

### Role in project

Cleanlab-style analysis is a content-evidence module that strengthens ranking when reliable, not the definition of dataset quality.

---

## 5. Croissant

### What it establishes

Croissant provides a standardized machine-readable representation for dataset metadata and structure, including dataset information, distributions, records and machine-learning-relevant fields.

The research foundation also references Croissant 1.1's newer direction toward machine-actionable provenance, vocabulary links and usage-policy concepts.

### Methods to adopt

- parse Croissant metadata where available;
- use standardized fields for interoperability;
- retain raw provenance links;
- expose structured license/governance claims;
- retain native repository metadata alongside normalized fields.

### Important design lesson

Croissant is a schema/evidence standard, not a claim that the underlying values are automatically correct.

The project should preserve:

```text
source claim
    ≠
verified fact
```

A Croissant-valid license entry is evidence about what was published, not legal clearance.

---

## 6. Dataset Cards and Documentation

Dataset cards provide structured contextual information around intended use, dataset characteristics, limitations and documentation.

### Role in the system

Dataset cards become evidence sources for:

- task and domain claims;
- intended use;
- limitations;
- provenance context;
- collection/annotation context;
- documentation completeness.

Documentation quality must not become an unconditional quality proxy. Rich documentation may correlate with ecosystem visibility, creating another route for popularity bias.

---

## 7. Provenance and Licensing Reliability

The research foundation uses public licensing/provenance audits to motivate caution around publisher-supplied governance metadata.

### Design consequences

The system should distinguish:

- repository-reported license;
- documented source license;
- provenance evidence;
- observed contradictions;
- unknown status.

It should not silently turn a license field into a legal conclusion.

For user constraints:

- clearly incompatible license → hard-filter when necessary;
- uncertain/contradictory license → preserve as a risk/uncertainty state;
- unknown license → do not assume compatibility.

Automated analysis is a classification and evidence aid, not legal advice.

---

## 8. Evidence Ledger

The evidence ledger is a project-level design response to the weakness of treating all metadata as equally trustworthy.

Each claim stores:

```text
claim
source
source type
observation time
evidence type
reliability indicator
procedure
sample size
conflict information
resolved state
```

### Why this matters

A dataset may simultaneously have:

```text
Repository: 50 classes
Paper: 48 classes
Observed sample: 47 classes
```

A single flat canonical field would hide the disagreement. The ledger preserves the disagreement so that the ranking and explanation layers can reason about it.

---

## 9. Dempster–Shafer Evidence Fusion

The project evaluates Dempster–Shafer theory for formal evidence resolution because it provides an explicit representation of uncertainty/ignorance distinct from conflict.

For a binary claim:

$$
\Theta = \{\top, \bot\}
$$

A source with reliability prior $r_i$ assigns mass to its stated position and retains $1-r_i$ as uncertainty:

$$
m_i(\top)=r_i, \quad m_i(\bot)=0, \quad m_i(\Theta)=1-r_i
$$

when it asserts the claim, with the true/false roles reversed when it rejects it.

Sources can then be combined with Dempster's rule, retaining:

- belief;
- plausibility;
- uncertainty interval;
- conflict mass.

### Research position

Dempster–Shafer theory itself is established. Therefore the project should **not** claim that the theory is novel.

The testable project contribution is narrower:

> whether formal evidence resolution over heterogeneous dataset claims produces more reliable and better-calibrated dataset recommendations than heuristic or single-source alternatives.

### Fallback requirement

If synthesized belief is poorly calibrated, retain raw evidence and source-level states rather than forcing an unreliable confidence score.

---

## 10. Content-Aware Dataset Fingerprinting

The project defines a Dataset Fingerprint as an **evidence package over a bounded sample**, not a compressed claim about the whole dataset.

### Sampling principles

- start small;
- measure feasibility;
- expand only when unstable measurements justify the cost;
- record acquisition method;
- record sample size;
- record selection/randomization method;
- preserve uncertainty.

### Examples

**Images:** dimensions, unreadable rate, brightness/contrast, blur, duplicates, embedding clusters, class balance.

**Tabular:** shape, missingness, type consistency, duplicate rows, cardinality, numeric summaries, outliers, target balance.

**Text:** empty records, duplicates, lengths, language indicators, label distribution, embedding clusters, vocabulary/task coverage.

**Detection:** annotations, missing labels, bounding-box validity, class balance and duplicate indicators.

---

## 11. Task-Specific Utility Estimation

This is the most important conceptual step beyond conventional dataset recommendation.

The system asks not only:

> Does the dataset look relevant?

but:

> Does bounded evidence suggest that this dataset can support the user's actual task?

### Candidate probes

- linear/logistic classification on frozen representations;
- small tree/linear model for tabular tasks;
- frozen nearest-neighbor structure;
- coverage alignment against task concepts;
- controlled subset utility when a fixed reference set exists.

### Cold-start fallback

Sampling can fail because a repository is gated, inaccessible, or restricted. Automatically discarding unsampled candidates would create a new accessibility bias.

Use a transfer estimate from already-probed neighbors:

$$
\hat{u}(d)=
\frac{\sum_{d'\in N_k(d)} w(d,d')u(d')}
{\sum_{d'\in N_k(d)}w(d,d')}
$$

with an RBF-style weight based on embedding similarity.

The result must be marked:

`TransferredEstimate-NotDirectlyObserved`

and assigned wider uncertainty than a direct probe.

---

## 12. Popularity Bias and Long-Tail Recommendation

Popularity signals are useful context but can become self-reinforcing selection pressure.

The system therefore maintains two conceptual pools:

```text
Main relevance pool
Long-tail exploration pool
```

Both use the same hard constraints and evidence/utility evaluation.

A lower-visibility dataset should only win because it offers a real advantage:

- task fit;
- measured utility;
- specialization;
- cleaner data;
- better coverage;
- efficiency;
- useful diversity.

The project is explicitly about **useful long-tail discovery**, not rewarding obscurity.

### Exposure Disparity Index

For popularity deciles $j$:

- $R_j$ = fraction of human-judged relevant candidates in decile $j$;
- $E_j$ = fraction of final recommendation exposure in decile $j$.

Define:

$$
EDI=\frac12\sum_j|E_j-R_j|
$$

Lower values mean exposure better tracks judged relevance across popularity strata rather than concentrating on already-visible datasets.

---

## 13. GIST and Diversity

GIST addresses max-min diversification with submodular utility, balancing utility and diversity under a bounded selection problem.

### What to adopt

- the utility-versus-diversity principle;
- max-min style separation;
- bounded greedy selection.

### What not to do

Do not attempt web-scale GIST reproduction for the capstone.

For a local candidate pool, compare:

- top-k utility-only;
- farthest-first;
- submodular facility-location style selection;
- lightweight GIST-inspired greedy procedure.

The chosen method should be determined by measured quality/compute trade-offs.

### Dataset families

Diversification should operate at dataset-family level when possible so mirrors, versions and closely derived variants do not consume multiple final slots.

---

## 14. Multi-Objective Ranking

Proposed ranking form:

$$
R(D|Q)=\alpha Fit+\beta Utility+\gamma Evidence+\delta Coverage+\epsilon Novelty-\lambda Risk
$$

This separates the major concepts:

| Component | Meaning |
|---|---|
| Fit | Explicit user requirements. |
| Utility | Direct probe or weaker transfer evidence. |
| Evidence | Strength and agreement of supporting claims. |
| Coverage | Representativeness and non-redundancy. |
| Novelty | Useful long-tail discovery. |
| Risk | Uncertainty, contradictions, governance gaps and operational issues. |

The coefficients are not universal constants. Start with transparent prototype weights and later test learning-to-rank if enough relevance judgments are available.

---

## 15. Evaluation Framework

### Retrieval

- Precision@K;
- Recall@K;
- nDCG@K;
- MRR.

### Long-tail

- hidden-gem recall;
- hidden-gem position;
- useful long-tail rate;
- Exposure Disparity Index.

### Diversity

- pairwise distance;
- family-level redundancy;
- distinct-coverage rate.

### Utility

- probe performance;
- controlled downstream improvement where possible;
- stability across repeated runs.

### Evidence and trust

- claim correctness;
- calibration curves;
- Expected Calibration Error;
- Brier score;
- conflict-state correctness.

### Human evaluation

Compare a plain metadata recommendation card with an evidence-backed card. Measure:

- willingness to trust/use;
- understanding of why it was recommended;
- forced-choice actionability.

### Robustness

Simulate:

- missing metadata;
- contradictory licenses;
- weakened descriptions;
- removed class information;
- unavailable sample access.

The expected behavior is graceful degradation, explicit uncertainty and recovery through alternative evidence where possible.

### Efficiency

Record:

- wall-clock time;
- peak memory;
- sampling success/failure;
- per-candidate probe cost;
- end-to-end latency.

---

## 16. Baselines and Ablations

The research foundation recommends the following ladder:

1. LLM zero-shot recommendation.
2. BM25-only.
3. Dense-only.
4. DataFinder-style trained bi-encoder.
5. Hybrid retrieval.
6. Hybrid + metadata scoring.
7. + evidence ledger / formal evidence resolution.
8. + content-aware utility.
9. Full system without diversification.
10. Full system with long-tail exploration and diversified reranking.

This ordering answers the most important causal question:

> Which additions actually improve recommendation quality?

---

## 17. Robustness and Hidden-Gem Benchmarks

### Hidden-gem benchmark

Construct tasks for which expert judgments identify at least one lower-visibility dataset that is genuinely useful.

A hidden gem is **not** merely low-download. It is lower-visibility plus useful evidence.

### Robustness benchmark

Remove or corrupt metadata fields and test whether the system:

- lowers confidence;
- changes `Verified` toward weaker states when corroboration disappears;
- surfaces contradictions;
- uses other evidence channels;
- avoids inventing missing values.

Freeze the benchmark before extensive ranking tuning to reduce leakage.

---

## 18. Local Implementation Research Guidance

### Environment

The research foundation suggests:

- Python 3.10+;
- `pandas`, `numpy`, `scipy`, `scikit-learn`;
- `sentence-transformers`;
- `faiss-cpu`;
- `cleanlab`;
- `mlcroissant`;
- `pyserini` and `submodlib` as optional components.

Exact versions should be pinned after the first successful build.

### Retrieval

Precompute dataset embeddings. Store them in a local vector index. Maintain BM25 over the same normalized retrieval representation.

### Source ingestion

Use one adapter per repository. Normalize into a canonical schema while retaining raw source provenance.

### Evidence

Cache source responses and observation timestamps. Never repeatedly hit external sources during experiments if the same data can be replayed locally.

### Sample acquisition

Prefer documented APIs/viewers/previews and only use limited sampling under verified access conditions. Platform access terms and dataset license terms are separate constraints.

### Compute policy

Run an early M0 experiment on approximately 10 real datasets. Measure:

- retrieval cost;
- evidence-collection cost;
- sample-acquisition success;
- probe time;
- peak memory.

Use those measurements to set the candidate-pool size and probe depth.

---

## 19. Risks and Research Caveats

### Metadata bias

Rich metadata may be correlated with popularity. Do not let documentation completeness become a direct proxy for quality.

### Accessibility bias

Datasets that are easy to sample are not necessarily better. Preserve unsampled candidates via transfer estimates and uncertainty.

### Popularity bias

High download counts can reflect visibility rather than task fitness. Keep popularity contextual and audit exposure.

### License uncertainty

Repository license metadata can be missing or incorrect. The system should expose evidence and conflicts, not claim legal clearance.

### Sample bias

A convenient sample may not represent the full dataset. All sample-derived evidence must carry scope and uncertainty.

### Probe bias

Probe model performance depends on the representation, sampling procedure and task formulation. Treat it as one evidence channel.

### Overengineering

Every advanced method must justify its compute and evaluation cost. A simple method with reproducible measured gains is preferable to a sophisticated method that cannot be validated.

---

## 20. Research-to-Implementation Mapping

| Research source | Adopt | Do not overclaim |
|---|---|---|
| DataFinder | BM25, dense, bi-encoder baseline, retrieval metrics | Retrieval itself as novelty |
| DataPerf | downstream utility mindset, selection evaluation | Full benchmark replication |
| Cleanlab | suspicious-label/data-quality evidence | Absolute data correctness |
| Croissant | standardized metadata/provenance representation | Automatic truth/legal clearance |
| Dataset Cards | documentation/context evidence | Documentation quality as universal quality |
| GIST | utility + diversity principle | Web-scale implementation |
| Provenance/licensing audits | verification and uncertainty design | Automatic legal interpretation |
| Evidence fusion | formal uncertainty/conflict handling | Mathematical rule itself as novelty |

---

## 21. References

1. Lin et al., **DataFinder: Scientific Dataset Recommendation from Natural Language**, WSDM 2023.  
   https://arxiv.org/abs/2305.16636  
   Official implementation: https://github.com/viswavi/datafinder

2. Mazumder et al., **DataPerf: Benchmarks for Data-Centric AI Development**, arXiv / DataPerf work.  
   https://arxiv.org/abs/2207.10062  
   Official repository: https://github.com/mlcommons/dataperf

3. Northcutt et al., **Confident Learning: Estimating Uncertainty in Dataset Labels**, NeurIPS 2021.  
   https://github.com/cleanlab/cleanlab  
   https://docs.cleanlab.ai/

4. MLCommons, **Croissant Dataset Metadata Format Specification**.  
   https://docs.mlcommons.org/croissant/

5. MLCommons, **Croissant 1.1** provenance and usage-policy materials.  
   https://mlcommons.org/2026/02/croissant-1-1-standard/

6. Zadimoghaddam et al., **GIST: Greedy Independent Set Thresholding for Max-Min Diversification with Submodular Utility**, NeurIPS 2025 / arXiv.  
   https://arxiv.org/abs/2405.18754

7. Google Research, **Introducing GIST: The Next Stage in Smart Sampling**.  
   https://research.google/blog/introducing-gist-the-next-stage-in-smart-sampling/

8. Google Dataset Search research and dataset discovery literature.

9. Hugging Face Hub documentation on dataset cards and dataset viewing.

10. Public research and reporting on dataset licensing/provenance quality, including work from the Data Provenance Initiative.

11. Shafer, **A Mathematical Theory of Evidence**, Princeton University Press, 1976.

12. Dempster, **A Generalization of Bayesian Inference**, Journal of the Royal Statistical Society, Series B, 1968.

13. Guo et al., **On Calibration of Modern Neural Networks**, ICML 2017.

---

## 22. Implementation Principle

The project should be built as a sequence of measured experiments, not as a monolithic AI application.

The correct development order is:

```text
M0: Compute + repository validation
        ↓
M1: Corpus + canonical schema
        ↓
M2: Retrieval baselines
        ↓
M3: Evidence ledger
        ↓
M4: Content evidence
        ↓
M5: Task utility
        ↓
M6: Long-tail + diversity
        ↓
M7: Final ranking + explanations
        ↓
M8: Evaluation + ablation
```

Any component that cannot be measured, reproduced or kept within the validated compute budget should be simplified, deferred or removed.
