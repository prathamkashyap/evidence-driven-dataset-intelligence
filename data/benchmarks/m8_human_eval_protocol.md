# Milestone 8 Human Evaluation Protocol

> **Status:** Prepared for Review / No Sessions Conducted
> **Commit Boundary:** Milestone 8 Benchmark Execution (`34eeb2b`)
> **Governing Documents:** `docs/PROJECT_SPEC.md` §19/§21, `docs/M8_EVALUATION.md` §12, `data/benchmarks/m8_human_eval_selection.json`
> **Participant Data Status:** Zero participant rating sessions conducted. Prepared prior to data collection.

---

## 1. Protocol Overview and Purpose

This document materializes the stimulus pairs, comparison counts, presentation randomization schedule, and experimental procedure for the Milestone 8 human study required by `PROJECT_SPEC.md` §19/§21 and `docs/M8_EVALUATION.md` §12.

The objective is to evaluate whether evidence-backed recommendation cards (`RecommendationCard`) provide superior **trust**, **understanding**, and **actionability** compared to conventional **plain metadata cards** for dataset discovery in machine learning workflows.

---

## 2. Preregistered Task Selection and Study Scope

Per `data/benchmarks/m8_human_eval_selection.json` (frozen at commit `7a2c774`), exactly three tasks were selected to span the three core modalities (text, tabular, image):

| Modality | Task ID | Task Name | Task Query / Target Description |
| :--- | :--- | :--- | :--- |
| **Text** | `task_21010815ad7dc71a2798bec3` | `task_sentiment_binary` | Binary sentiment classification on movie review text (`max_tokens: 512`) |
| **Tabular** | `task_4ec3bd8ba587c0a84210f1f9` | `task_tabular_titanic` | Binary tabular classification on demographic attributes (`target: binary_2`) |
| **Image** | `task_fb99dac2dd25b90db8778f6b` | `task_image_cifar` | Multiclass visual object classification (`100 classes`) |

---

## 3. Recommendation Source and Stimulus Sizing

### A. Recommendation Source
Stimuli are derived strictly from the frozen Milestone 8 Full System recommendations (**Baseline R3 / Rung 8: Diversified MMR with Family Deduplication**) as recorded in `experiments/m8/results/m8_summary.json`.

### B. Comparison Sizing and Fallback Rule
The frozen protocol stipulates up to $k=3$ recommendations per task, with the explicit rule: *"If fewer than 3 recommendations are available for a task (|S*| < 3, as M7's own design permits for constrained tasks), use all available recommendations for that task."*

* `task_sentiment_binary`: **2 recommendations available** (`fancyzhx/ag_news`, `cornell-movie-review-data/rotten_tomatoes`). Both are included.
* `task_tabular_titanic`: **3 recommendations available** (`Breast Cancer Wisconsin (Diagnostic)`, `Wine`, `Adult`). All 3 are included.
* `task_image_cifar`: **2 recommendations available** (`uoft-cs/cifar100`, `AI-Lab-Makerere/beans`). Both are included.

$$\text{Total Comparisons} = 2 + 3 + 2 = \mathbf{7}\text{ dataset-level comparisons.}$$

---

## 4. Card Format Definitions

For each dataset, raters are presented with two distinct information representations for the same underlying dataset:

1. **Format A — Plain Metadata Card (Baseline Representation):**
   A plain metadata card strictly adhering to `docs/M8_EVALUATION.md` §12 (`"(a) a plain metadata card (name, source, modality, size — no evidence/role/explanation fields)"`):
   - `name`: Dataset name from identity metadata
   - `source`: Source platform (`huggingface`, `openml`, `uci`, `kaggle`)
   - `modality`: Data modality (`text`, `tabular`, `image`)
   - `size`: Dataset sample count if measured/declared in canonical structure schema (`record.structure["sample_count"]`), or `null` if unmeasured
   - *(Explicitly excluded: dataset_id, description, license_claim, file_formats, suitability scores, evidence provenance, role badges, fit/unfit explanations).*

2. **Format B — Evidence-Backed RecommendationCard (System Representation):**
   The full frozen M7 `RecommendationCard` containing:
   - Recommendation Rank & Assigned Semantic Role (`best_overall`, `best_quality`, `best_efficient_option`, `best_alternative`, `hidden_gem`)
   - Multi-Objective Scores (Fit Score, Utility Score, Evidence Support, Content Coverage, Risk Penalty)
   - Marginal Diversity Contribution
   - Structured Explanations: *Why it fits*, *Why it is not perfect*, *Why it appears here*
   - Operational Context (Access restriction, popularity stratum, observed license status)

---

## 5. Materialized Stimulus Pairs (All 7 Comparisons)

### Comparison 1: fancyzhx/ag_news (`ds_3e424a817c66aab45e96797a`)
* **Task Context:** `task_sentiment_binary` (Task ID: `task_21010815ad7dc71a2798bec3`) — Query: *"movie review sentiment analysis binary classification text"*
* **System Rank in Task Set:** #1 of task_sentiment_binary

#### Format A: Plain Metadata Card
```yaml
name: "fancyzhx/ag_news"
source: "huggingface"
modality: "text"
size: null
```

#### Format B: Evidence-Backed RecommendationCard
```yaml
card_id: "card_a93bcbb8e77cce5a774971f6"
dataset_id: "ds_3e424a817c66aab45e96797a"
dataset_name: "fancyzhx/ag_news"
final_rank: 1
assigned_role: "best_overall"
raw_candidate_score: 0.8207
marginal_diversity_gain: 1.0
component_scores:
  task_fit_score: 0.9333
  task_utility_score: 0.8929
  evidence_support_score: 0.36
  content_coverage_score: 1.0
  risk_penalty: 0.15
why_it_fits:
  - "Direct task alignment: verified classification compatibility."
  - "Modality match: verified text format."
  - "Structural match: feature dimensionality and sample bounds align with requirements."
why_it_is_not_perfect:
  - "Unmeasured evidence for governance."
  - "Sample-limited inference: target based on bounded 32-row probe."
why_it_appears_here:
  - "Assigned recommendation role: 'best_overall'."
  - "High marginal diversity contribution (1.00) relative to preceding selections."
  - "Multi-objective suitability balance: utility 0.89, fit 0.93, evidence support 0.36."
operational_context:
  source_name: "huggingface"
  license_claim: "unknown"
  access_restriction: "unrestricted"
  popularity_stratum: "low"
```

---

### Comparison 2: cornell-movie-review-data/rotten_tomatoes (`ds_c9a42d9bd6268ce4a4cf6061`)
* **Task Context:** `task_sentiment_binary` (Task ID: `task_21010815ad7dc71a2798bec3`) — Query: *"movie review sentiment analysis binary classification text"*
* **System Rank in Task Set:** #2 of task_sentiment_binary

#### Format A: Plain Metadata Card
```yaml
name: "cornell-movie-review-data/rotten_tomatoes"
source: "huggingface"
modality: "text"
size: null
```

#### Format B: Evidence-Backed RecommendationCard
```yaml
card_id: "card_9bab425df9993a52e90d78d3"
dataset_id: "ds_c9a42d9bd6268ce4a4cf6061"
dataset_name: "cornell-movie-review-data/rotten_tomatoes"
final_rank: 2
assigned_role: "hidden_gem"
raw_candidate_score: 0.7622
marginal_diversity_gain: 0.5
component_scores:
  task_fit_score: 0.9333
  task_utility_score: 0.8929
  evidence_support_score: 0.32
  content_coverage_score: 1.0
  risk_penalty: 0.5
why_it_fits:
  - "Direct task alignment: verified classification compatibility."
  - "Modality match: verified text format."
  - "Structural match: feature dimensionality and sample bounds align with requirements."
why_it_is_not_perfect:
  - "Unresolved conflict in governance evidence."
  - "Sample-limited inference: target based on bounded 32-row probe."
why_it_appears_here:
  - "Assigned recommendation role: 'hidden_gem'."
  - "Multi-objective suitability balance: utility 0.89, fit 0.93, evidence support 0.32."
operational_context:
  source_name: "huggingface"
  license_claim: "unknown"
  access_restriction: "unrestricted"
  popularity_stratum: "low"
```

---

### Comparison 3: Breast Cancer Wisconsin (Diagnostic) (`ds_a67e752b027f81f22083533c`)
* **Task Context:** `task_tabular_titanic` (Task ID: `task_4ec3bd8ba587c0a84210f1f9`) — Query: *"tabular Titanic survival binary classification with demographic features"*
* **System Rank in Task Set:** #1 of task_tabular_titanic

#### Format A: Plain Metadata Card
```yaml
name: "Breast Cancer Wisconsin (Diagnostic)"
source: "uci"
modality: "tabular"
size: 569
```

#### Format B: Evidence-Backed RecommendationCard
```yaml
card_id: "card_361fd57b208295a9e7232eca"
dataset_id: "ds_a67e752b027f81f22083533c"
dataset_name: "Breast Cancer Wisconsin (Diagnostic)"
final_rank: 1
assigned_role: "best_overall"
raw_candidate_score: 0.879
marginal_diversity_gain: 1.0
component_scores:
  task_fit_score: 1.0
  task_utility_score: 0.9286
  evidence_support_score: 0.36
  content_coverage_score: 1.0
  risk_penalty: 0.0
why_it_fits:
  - "Direct task alignment: verified classification compatibility."
  - "Modality match: verified tabular format."
  - "Target structure alignment: label and class structure match task requirements."
  - "Structural match: feature dimensionality and sample bounds align with requirements."
why_it_is_not_perfect:
  - "Unmeasured evidence for governance."
why_it_appears_here:
  - "Assigned recommendation role: 'best_overall'."
  - "High marginal diversity contribution (1.00) relative to preceding selections."
  - "Multi-objective suitability balance: utility 0.93, fit 1.00, evidence support 0.36."
operational_context:
  source_name: "uci"
  license_claim: "unknown"
  access_restriction: "unrestricted"
  popularity_stratum: "unknown"
```

---

### Comparison 4: Wine (`ds_9f128b3a604eed483953e7f8`)
* **Task Context:** `task_tabular_titanic` (Task ID: `task_4ec3bd8ba587c0a84210f1f9`) — Query: *"tabular Titanic survival binary classification with demographic features"*
* **System Rank in Task Set:** #2 of task_tabular_titanic

#### Format A: Plain Metadata Card
```yaml
name: "Wine"
source: "uci"
modality: "tabular"
size: 178
```

#### Format B: Evidence-Backed RecommendationCard
```yaml
card_id: "card_7ff4f846b481a729c4690d4f"
dataset_id: "ds_9f128b3a604eed483953e7f8"
dataset_name: "Wine"
final_rank: 2
assigned_role: "best_quality"
raw_candidate_score: 0.879
marginal_diversity_gain: 0.5
component_scores:
  task_fit_score: 1.0
  task_utility_score: 0.9286
  evidence_support_score: 0.36
  content_coverage_score: 1.0
  risk_penalty: 0.0
why_it_fits:
  - "Direct task alignment: verified classification compatibility."
  - "Modality match: verified tabular format."
  - "Target structure alignment: label and class structure match task requirements."
  - "Structural match: feature dimensionality and sample bounds align with requirements."
why_it_is_not_perfect:
  - "Unmeasured evidence for governance."
why_it_appears_here:
  - "Assigned recommendation role: 'best_quality'."
  - "Multi-objective suitability balance: utility 0.93, fit 1.00, evidence support 0.36."
operational_context:
  source_name: "uci"
  license_claim: "unknown"
  access_restriction: "unrestricted"
  popularity_stratum: "unknown"
```

---

### Comparison 5: Adult (`ds_bdf285c7cdab311e6bd061ed`)
* **Task Context:** `task_tabular_titanic` (Task ID: `task_4ec3bd8ba587c0a84210f1f9`) — Query: *"tabular Titanic survival binary classification with demographic features"*
* **System Rank in Task Set:** #3 of task_tabular_titanic

#### Format A: Plain Metadata Card
```yaml
name: "Adult"
source: "uci"
modality: "tabular"
size: 48842
```

#### Format B: Evidence-Backed RecommendationCard
```yaml
card_id: "card_82d36f9826c4a4e5cc598a8e"
dataset_id: "ds_bdf285c7cdab311e6bd061ed"
dataset_name: "Adult"
final_rank: 3
assigned_role: "best_efficient_option"
raw_candidate_score: 0.8787
marginal_diversity_gain: 0.5
component_scores:
  task_fit_score: 1.0
  task_utility_score: 0.9277
  evidence_support_score: 0.36
  content_coverage_score: 1.0
  risk_penalty: 0.0
why_it_fits:
  - "Direct task alignment: verified classification compatibility."
  - "Modality match: verified tabular format."
  - "Target structure alignment: label and class structure match task requirements."
  - "Structural match: feature dimensionality and sample bounds align with requirements."
why_it_is_not_perfect:
  - "Unmeasured evidence for governance."
why_it_appears_here:
  - "Assigned recommendation role: 'best_efficient_option'."
  - "Multi-objective suitability balance: utility 0.93, fit 1.00, evidence support 0.36."
operational_context:
  source_name: "uci"
  license_claim: "unknown"
  access_restriction: "unrestricted"
  popularity_stratum: "unknown"
```

---

### Comparison 6: uoft-cs/cifar100 (`ds_40356f676278cb9903556c6e`)
* **Task Context:** `task_image_cifar` (Task ID: `task_fb99dac2dd25b90db8778f6b`) — Query: *"multiclass natural image classification"*
* **System Rank in Task Set:** #1 of task_image_cifar

#### Format A: Plain Metadata Card
```yaml
name: "uoft-cs/cifar100"
source: "huggingface"
modality: "image"
size: null
```

#### Format B: Evidence-Backed RecommendationCard
```yaml
card_id: "card_3b4323f785d2d8f7ac483136"
dataset_id: "ds_40356f676278cb9903556c6e"
dataset_name: "uoft-cs/cifar100"
final_rank: 1
assigned_role: "best_overall"
raw_candidate_score: 0.829
marginal_diversity_gain: 1.0
component_scores:
  task_fit_score: 0.9
  task_utility_score: 0.8857
  evidence_support_score: 0.36
  content_coverage_score: 1.0
  risk_penalty: 0.0
why_it_fits:
  - "Direct task alignment: verified classification compatibility."
  - "Modality match: verified image format."
  - "Structural match: feature dimensionality and sample bounds align with requirements."
why_it_is_not_perfect:
  - "Unmeasured evidence for governance."
  - "Unmeasured evidence for target."
why_it_appears_here:
  - "Assigned recommendation role: 'best_overall'."
  - "High marginal diversity contribution (1.00) relative to preceding selections."
  - "Multi-objective suitability balance: utility 0.89, fit 0.90, evidence support 0.36."
operational_context:
  source_name: "huggingface"
  license_claim: "unknown"
  access_restriction: "unrestricted"
  popularity_stratum: "very_low"
```

---

### Comparison 7: AI-Lab-Makerere/beans (`ds_4e61d125afd0915cf8dcb4c6`)
* **Task Context:** `task_image_cifar` (Task ID: `task_fb99dac2dd25b90db8778f6b`) — Query: *"multiclass natural image classification"*
* **System Rank in Task Set:** #2 of task_image_cifar

#### Format A: Plain Metadata Card
```yaml
name: "AI-Lab-Makerere/beans"
source: "huggingface"
modality: "image"
size: null
```

#### Format B: Evidence-Backed RecommendationCard
```yaml
card_id: "card_86fa51d3c6f375d05815a7d5"
dataset_id: "ds_4e61d125afd0915cf8dcb4c6"
dataset_name: "AI-Lab-Makerere/beans"
final_rank: 2
assigned_role: "best_alternative"
raw_candidate_score: 0.718
marginal_diversity_gain: 0.5
component_scores:
  task_fit_score: 0.9
  task_utility_score: 0.6714
  evidence_support_score: 0.12
  content_coverage_score: 1.0
  risk_penalty: 0.0
why_it_fits:
  - "Direct task alignment: verified classification compatibility."
  - "Modality match: verified image format."
  - "Structural match: feature dimensionality and sample bounds align with requirements."
why_it_is_not_perfect:
  - "Operational probe failure in access_feasibility."
  - "Unmeasured evidence for governance."
  - "Operational probe failure in quality."
  - "Unmeasured evidence for target."
why_it_appears_here:
  - "Assigned recommendation role: 'best_alternative'."
  - "Multi-objective suitability balance: utility 0.67, fit 0.90, evidence support 0.12."
operational_context:
  source_name: "huggingface"
  license_claim: "unknown"
  access_restriction: "unrestricted"
  popularity_stratum: "very_low"
```

---

## 6. Deterministic Presentation Randomization Schedule

To eliminate systematic presentation bias (order effects), the sequence of **Format A** versus **Format B** is randomized per comparison per rater.

### A. Outcome-Independent Randomization Protocol
* **Algorithm:** Standard library pseudo-random generator `random.Random(seed)`.
* **Fixed Random Seed:** `20260914` (the pre-session protocol freeze execution date; completely outcome-independent).
* **Randomization Rule:** For each rater and comparison, `rng.choice(['A_first', 'B_first'])` determines whether Format A (plain) is presented before Format B (evidence) or vice versa.

### B. Pre-Committed Presentation Schedule

| Comparison ID | Task Name | Dataset Evaluated | Rater 1 Order | Rater 2 Order | Rater 3 Order |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `comp_1` | `task_sentiment_binary` | `fancyzhx/ag_news` | **Format B first** (B, then A) | **Format B first** (B, then A) | **Format A first** (A, then B) |
| `comp_2` | `task_sentiment_binary` | `cornell-movie-review-data/rotten_tomatoes` | **Format B first** (B, then A) | **Format A first** (A, then B) | **Format B first** (B, then A) |
| `comp_3` | `task_tabular_titanic` | `Breast Cancer Wisconsin (Diagnostic)` | **Format B first** (B, then A) | **Format B first** (B, then A) | **Format B first** (B, then A) |
| `comp_4` | `task_tabular_titanic` | `Wine` | **Format A first** (A, then B) | **Format A first** (A, then B) | **Format B first** (B, then A) |
| `comp_5` | `task_tabular_titanic` | `Adult` | **Format B first** (B, then A) | **Format B first** (B, then A) | **Format B first** (B, then A) |
| `comp_6` | `task_image_cifar` | `uoft-cs/cifar100` | **Format B first** (B, then A) | **Format A first** (A, then B) | **Format A first** (A, then B) |
| `comp_7` | `task_image_cifar` | `AI-Lab-Makerere/beans` | **Format A first** (A, then B) | **Format A first** (A, then B) | **Format B first** (B, then A) |

---

## 7. Experimental Procedure and Rater Governance

1. **Participants / Raters (`docs/M8_EVALUATION.md` §12):**
   - Minimum 2, target 3 raters.
   - The project author may be one rater but is disclosed as non-blind.
   - At least one additional rater should be someone not involved in building the pipeline, if available before the study runs.
   - No additional or invented rater restrictions beyond the frozen protocol text.
2. **Within-Subjects Design:**
   - Every rater independently reviews and rates all 7 comparisons.
   - Each comparison requires independent 1–5 Likert ratings for Format A and Format B across the three dimensions (Trust, Understanding, Actionability).
3. **Blinding & Neutrality Instructions:**
   - Raters are provided with the target task description and query context.
   - Raters are told which task each comparison is for but not which baseline (R1/R2/R3) produced the recommendation card.
   - Raters are instructed that formats are alternative representations, with no framing that one is 'superior' or 'experimental'.

---

## 8. Response-Recording Schema

Participant responses must be logged in a standardized CSV artifact (`data/benchmarks/m8_human_eval_responses.csv`) adhering to the following schema:

```csv
rater_id,task_name,comparison_id,dataset_id,format_presented,presentation_order,trust_score,understanding_score,actionability_score,notes
```

### Field Specifications:
* `rater_id`: `rater_1`, `rater_2`, or `rater_3`
* `task_name`: `task_sentiment_binary`, `task_tabular_titanic`, or `task_image_cifar`
* `comparison_id`: `comp_1` through `comp_7`
* `dataset_id`: Canonical dataset ID (`ds_...`)
* `format_presented`: `format_a_plain` or `format_b_evidence`
* `presentation_order`: `first` or `second` (per the randomization schedule)
* `trust_score`: Integer `1` to `5`
* `understanding_score`: Integer `1` to `5`
* `actionability_score`: Integer `1` to `5`
* `notes`: Optional qualitative feedback

### Response Accounting:
Each rater provides $7 \times 2 = 14$ card evaluations ($42$ discrete Likert ratings across the 3 dimensions).
* **If 2 raters participate (minimum requirement):** $2 \times 14 = \mathbf{28}$ card evaluation rows ($\mathbf{84}$ discrete Likert observations).
* **If 3 raters participate (target cohort):** $3 \times 14 = \mathbf{42}$ card evaluation rows ($\mathbf{126}$ discrete Likert observations).

---

## 9. Preregistered Analysis Plan & Limitations

* **Descriptive Statistics:** Calculate Median and Interquartile Range (IQR) for Trust, Understanding, and Actionability independently for Format A and Format B.
* **Exploratory Inferential Test:** Given the small target $n$ (2–3 raters), no inferential test is pre-registered as confirmatory; a Wilcoxon signed-rank test may be reported as an exploratory supplement only, clearly labeled as such.
* **Mandatory Limitations Statement:** Must be reproduced in all research findings documents:
  > "The human evaluation study has small sample size (n=2–3 raters), lacks formal statistical power analysis, involves at least one non-blind rater, and was conducted in a single-investigator research context. All findings are descriptive and exploratory characterizations of user perception rather than confirmatory statistical proofs of generalizable behavioral effects."
* **Methodological Note (Understanding Item Asymmetry):** The questionnaire item for Understanding (*"I understand why this dataset was surfaced and how it connects to the specific technical requirements of the task."*) is structurally asymmetric between formats. Format A intentionally contains no explanation of task fit, whereas Format B contains explanatory fields (`why_it_fits`, `why_it_is_not_perfect`, `why_it_appears_here`) that directly address the item's wording. This is a design characteristic of the baseline/system comparison, not a demonstrated participant response pattern, and must be contextualized accordingly in reporting.
