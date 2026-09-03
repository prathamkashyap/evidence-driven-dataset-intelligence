# Milestone 6 — Popularity-Bias Audit & Long-Tail Exploration Specification

## 1. Overview and Purpose

Milestone 6 establishes the **popularity-bias audit and under-exposed exploration framework** of the dataset intelligence pipeline.

M6 investigates:
> *"Does conventional dataset retrieval systematically favor popular datasets, and can a bounded long-tail exploration strategy discover lower-popularity candidates that have comparable or better task-specific utility?"*

---

## 2. Core Epistemic & Methodological Principles

1. **Popularity is Contextual Evidence, NOT Suitability:** Popularity signals (downloads, stars, likes) reflect platform visibility and community activity. They are **not** positive utility signals or quality certifications.
2. **M5 Utility Independence Invariant:** Popularity profiling, exposure auditing, and exploration eligibility **never** modify, rescale, or penalize M5 task utility scores ($U_{\text{M6}}(D \mid T) \equiv U_{\text{M5}}(D \mid T)$).
3. **Unknown Popularity $\neq$ Low Popularity:** If a source platform does not expose popularity counters (e.g. OpenML, UCI), the dataset is classified as `under_observed` with stratum `unknown`. It is **never** assigned 0 downloads, never called "long-tail", and never labeled a "hidden gem" without empirical popularity verification.
4. **Guarded Metrics:** Exposure Disparity Ratio ($EDR$) and Utility-Weighted Exposure ($UWE$) implement explicit `"not_estimable"` guards when denominators are zero, preventing division-by-zero crashes or fabricated numbers.
5. **Conservative Multi-Signal Family Linkage:** To prevent identical mirrors from consuming exploration slots, family linkage requires a name token or lineage anchor **plus** at least one secondary corroborating signal (modality/task compatibility or structural overlap). Uncertain lineage remains `unknown_family`.

---

## 3. DatasetPopularityProfile Schema

```python
@dataclass(frozen=True)
class DatasetPopularityProfile:
    profile_id: str                           # 'pop_' + sha256(...)[:24]
    profile_version: str                      # '1.0'
    dataset_id: str                           # Canonical ID ('ds_...')
    source_name: str                          # 'huggingface', 'kaggle', 'openml', 'uci'
    raw_signals: dict[str, Any]               # Verbatim community_context fields
    primary_metric_name: str | None           # 'downloads', 'stars', or None
    primary_metric_value: float | None        # Numeric value if measured; None if under_observed
    popularity_measurement_state: str         # 'measured' | 'under_observed'
    source_relative_percentile: float | None  # Percentile rank within same source [0.0, 1.0]
    popularity_stratum: str                   # 'very_high', 'high', 'medium', 'low', 'very_low', 'unknown'
    observed_at: str                          # Timestamp from M1 snapshot
    provenance: dict[str, Any]                # Normalization method, population size
```

---

## 4. Source-Specific Semantics & Normalization

- **Hugging Face:** `downloads` (fallback: `likes`/`stars`). Stratified via source-relative quantiles into `very_high`, `high`, `medium`, `low`, `very_low`.
- **Kaggle:** `totalDownloads` (fallback: `voteCount`/`stars`). Stratified within Kaggle measured population.
- **OpenML & UCI:** Native API/catalog responses lack community counters. Classified as `under_observed` with stratum `unknown`.

---

## 5. Guarded Exposure Audit Metrics

1. **Stratum Exposure Share ($ES(s \mid Q, k)$):**
   $$
   ES(s \mid Q, k) = \frac{1}{k} \sum_{i=1}^k \mathbb{I}(\text{stratum}(d_i) = s)
   $$
2. **Guarded Exposure Disparity Ratio ($EDR(s \mid Q, k)$):**
   $$
   EDR(s \mid Q, k) = \begin{cases}
   \text{"not\_estimable (zero corpus share)"} & \text{if } \text{CorpusShare}(s) = 0 \\
   \frac{ES(s \mid Q, k)}{\text{CorpusShare}(s)} & \text{otherwise}
   \end{cases}
   $$
3. **Guarded Utility-Weighted Exposure ($UWE(s \mid Q, k)$):**
   $$
   UWE(s \mid Q, k) = \begin{cases}
   \text{"not\_estimable (zero exposed utility)"} & \text{if } \sum_{i=1}^k U(d_i) = 0 \\
   \frac{\sum_{i=1}^k U(d_i) \cdot \mathbb{I}(\text{stratum}(d_i) = s)}{\sum_{i=1}^k U(d_i)} & \text{otherwise}
   \end{cases}
   $$

---

## 6. Dual-Pool Long-Tail Exploration Mechanics

### Under-Exposed Candidate Definition:
A candidate $D$ in the local corpus is **under-exposed** for task $T$ iff:
1. $D \notin \text{TopK}_{\text{retrieved}}(Q)$
2. $G(D \mid T) = 1.0$ (no hard constraints violated)
3. $U_{\text{baseline}}(D \mid T) > 0.0$

### Exploration Eligibility:
Eligible for exploration additions (up to $M \le 5$ candidates) iff:
1. Candidate is under-exposed.
2. Popularity is either measured non-dominant (`medium`, `low`, `very_low`) OR `under_observed` (explicitly labeled as *under-observed exploration*).
3. Task utility $U_{\text{baseline}}(D \mid T) \ge 0.50$.
4. Operational access is not `failed` (e.g. Beans HTTP 502 excluded).

---

## 7. Hidden-Gem vs. Under-Observed Designations

| Dimension | Hidden Gem Designation | Under-Observed High-Utility Designation |
|---|---|---|
| **Popularity State** | `measured` (`low` or `very_low` stratum) | `under_observed` (`unknown` stratum) |
| **Task Utility** | $U_{\text{baseline}} \ge 0.70$ | $U_{\text{baseline}} \ge 0.70$ |
| **Hard Gating** | $G = 1.0$ (Compliant) | $G = 1.0$ (Compliant) |
| **Access Verification** | `access_feasibility.score >= 0.80` | `access_feasibility.score >= 0.80` |
| **Lineage** | Not a redundant family variant | Not a redundant family variant |
| **Label Rationale** | Verified high-utility candidate from low-visibility stratum | High-utility candidate with unverified community popularity |

---

## 8. Explicit M6 vs. M7 Boundary

| Boundary Dimension | Milestone 6 (Popularity Audit & Long-Tail Exploration) | Milestone 7 (Recommendation & Multi-Objective Ranking) |
|---|---|---|
| **Core Objective** | Audit retrieval bias; construct bounded under-exposed exploration candidate pool | Produce final diversified set recommendations with assigned roles |
| **Output Type** | Popularity audit report & augmented candidate pool | Ranked recommendation list with CLI explanation cards |
| **Role Assignment** | Tests hidden-gem *eligibility predicate* | Formally assigns recommendation roles (*Best overall*, *Hidden gem*, *Best quality*) |
| **Ranking Score** | Computes M6 exposure statistics only; M5 utility is unmodified | Evaluates multi-objective formulation: $R(D \mid Q) = \alpha \text{Fit} + \beta \text{Utility} + \gamma \text{Evidence} + \dots$ |
| **Diversity Optimization** | Filters exact family mirrors | Applies bounded GIST / submodular facility location for subset selection |
