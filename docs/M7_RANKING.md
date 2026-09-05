# Milestone 7 — Multi-Objective Ranking, Diversification & Recommendation Roles Specification

## 1. Overview and Core Philosophy

Milestone 7 constructs the final **recommendation, diversification, and explanation system** of the dataset intelligence pipeline.

M7 treats dataset recommendation as a **set-selection problem** rather than merely sorting an isolated candidate score list. It addresses the research question:
> *"Given candidates retrieved and explored across heterogeneous repositories, their immutable evidence claims, bounded sample fingerprints, task utility estimates, operational states, and lineage linkages, how can a compact recommendation set be constructed that preserves task fit and utility while actively eliminating mirror redundancy and epistemic risk, and maintaining fully traceable explanations—without allowing popularity to bias suitability?"*

---

## 2. Fundamental Engineering Invariants

1. **Popularity-Neutral Suitability:** Popularity signals (downloads, stars, votes) and exploration origin **must not enter** candidate suitability scoring or ranking formulas.
2. **M5 Utility Invariance:** M5 task utility estimates are strictly read-only invariants ($U_{\text{M7}} \equiv U_{\text{M5}}$).
3. **M3 Evidence Immutability:** M3 categorical evidence states (`observed`, `single_source_claim`, `corroborated`, `conflicting`, `unknown`, `failed`) are preserved. Evidence support is treated as an explicit heuristic feature, never as epistemic confidence.
4. **Hard Constraints Precede Scoring:** Candidates with verified modality clashes, prohibited licenses, or fatal endpoint failures are hard-gated ($G=0$) and pruned prior to scoring.
5. **Pairwise Lineage Engine Reuse:** Family redundancy elimination reuses `detect_family_redundancy` from `src.dataset_intelligence.exploration.family` pairwise against all accepted datasets in $S^*$. `unknown_family` lineage is preserved with neutral distance ($0.5$), never treated as duplicate.
6. **Post-Selection Role Assignment:** Recommendation roles (*Best overall*, *Best data-quality*, *Best efficient option*, *Hidden gem*, *Best alternative*) are assigned strictly *after* set selection and return `None` if empirical criteria are unfulfilled.

---

## 3. Candidate-Level Signal Definitions

```text
M1 Canonical Schema        ───► S_fit(D | T)      ∈ [0.0, 1.0] (Explicit task requirement alignment)
M5 Utility Estimate        ───► S_util(D | T)     ∈ [0.0, 1.0] (M5 composite utility; read-only invariant)
M3 Evidence & M4 Probes    ───► S_evid_supp(D)    ∈ [0.0, 1.0] (Heuristic evidence-support feature)
M4 Fingerprint Diagnostics ───► S_cov(D | T)      ∈ [0.0, 1.0] (Structural completeness & volume coverage)
M3 Conflicts & M5 Gaps     ───► S_risk(D | T)     ∈ [0.0, 1.0] (Uncertainty & operational friction penalty)
```

### Heuristic Evidence-Support Feature ($S_{\text{evid\_supp}}$):
Evaluated across 5 operational facets (modality, target structure, governance, quality, access):
- Direct empirical observation in M4 / verified endpoint: **$1.0$**
- Corroborated multi-source observation in M3: **$0.8$**
- Single-source publisher claim: **$0.4$**
- Unknown / unsupported: **$0.2$**
- Failed / conflicting: **$0.0$**

$$
S_{\text{evid\_supp}}(D) = \frac{1}{5} \sum_{f=1}^5 \text{facet\_weight}(f) \in [0.0, 1.0]
$$

### Deterministic Risk Penalty ($S_{\text{risk}}$):
- Unresolved conflict in M3 ledger: $+0.35$
- Critical task requirement marked `unknown`: $+0.25$
- M4 sample-limited inference: $+0.15$
- Operational access friction (auth/gating required): $+0.15$
- Degraded sample health ($>5\%$ missing cells or $>10\%$ duplicates): $+0.10$

$$
S_{\text{risk}}(D \mid T) = \min\left(1.0, \sum p_r\right) \in [0.0, 1.0]
$$

---

## 4. Ranking Baselines & Mathematical Score Ranges

### Baseline R1: Utility-Only Naive Ranking
$$
\text{Score}_{\text{R1}}(D) = S_{\text{util}}(D \mid T) = U_{\text{baseline}}(D \mid T) \in [0.0, 1.0]
$$
- Selection: Sort descending by utility; select top-$k$. No evidence/risk weighting, no set diversification.

### Baseline R2: Linear Multi-Objective (Candidate-Level Only)
$$
\text{Score}_{\text{R2}}(D) = 0.35 S_{\text{fit}} + 0.35 S_{\text{util}} + 0.15 S_{\text{evid\_supp}} + 0.15 S_{\text{cov}} - 0.15 S_{\text{risk}}
$$
- **Raw Score Range:** $[-0.15, 1.00]$
- Selection: Sort descending by $\text{Score}_{\text{R2}}(D)$; select top-$k$.

### Proposed Baseline R3: Diversified Multi-Objective Set Selection
- Candidate Intrinsic Score:
  $$
  \text{Score}_{\text{cand\_R3}}(D) = 0.35 S_{\text{fit}} + 0.35 S_{\text{util}} + 0.15 S_{\text{evid\_supp}} + 0.15 S_{\text{cov}} - 0.15 S_{\text{risk}} \in [-0.15, 1.00]
  $$
- Set-Level Objective:
  $$
  \mathcal{F}(S) = \sum_{d \in S} \text{Score}_{\text{cand\_R3}}(d) + \lambda_{\text{div}} \cdot \text{Diversity}(S) - \lambda_{\text{red}} \cdot \text{Redundancy}(S)
  $$
- Selection: Family-Aware Bounded Greedy Diversity Selection with $\lambda_{\text{div}} = 0.20$ and hard same-family mirror exclusion.

---

## 5. Pairwise Attribute Distance & Diversification Algorithm

### Attribute Distance $\text{Dist}(d_i, d_j) \in [0.0, 1.0]$:
$$
\text{Dist}(d_i, d_j) = \frac{1}{3} d_{\text{lineage}}(d_i, d_j) + \frac{1}{3} d_{\text{features}}(d_i, d_j) + \frac{1}{3} d_{\text{source}}(d_i, d_j)
$$
Where:
- $d_{\text{lineage}} = 0.0$ if `same_family`, $1.0$ if `different_family`, $0.5$ if `unknown_family`.
- $d_{\text{features}} = 1.0 - \text{Jaccard}(\text{tokens}_i, \text{tokens}_j)$ (or $0.5$ if both unmeasured).
- $d_{\text{source}} = 0.0$ if same source else $1.0$.

### Selection Algorithm:
In each round $t \le k$:
1. For each candidate $D \in C \setminus S^*$:
   - Check pairwise redundancy: `is_redundant, _, _ = detect_family_redundancy(D, S*)`. If `is_redundant`, skip $D$.
   - Compute marginal diversity: $\text{marginal\_div} = \min_{s \in S^*} \text{Dist}(D, s)$ (or $1.0$ if $S^* = \emptyset$).
   - Compute marginal gain: $\text{gain} = \text{Score}_{\text{cand\_R3}}(D) + \lambda_{\text{div}} \cdot \text{marginal\_div}$.
2. Greedily select candidate maximizing marginal gain (tie-breaking deterministically by candidate score and dataset ID).

---

## 6. Post-Selection Recommendation Roles Taxonomy

| Role | Assignment Logic | Fallback |
|---|---|---|
| **Best overall** | Highest candidate intrinsic score in $S^*$ | Assigned to Rank 1 |
| **Best data-quality profile** | Highest M4 quality score ($\ge 0.70$) with clean sample diagnostics in $S^* \setminus \{d_{\text{overall}}\}$ | `None` |
| **Best efficient option** | Grounded access baseline (`access_feasibility.score >= 0.80`, `epistemic_state == "known_favorable"`, $U \ge 0.50$) + relative comparison of present/comparable operational measurements | `None` |
| **Hidden gem** | Inherits strict M6 measured hidden-gem predicate (measured low/very-low popularity, $U \ge 0.70$, verified access/quality, non-redundant) | `None` |
| **Best alternative** | Maximum attribute distance from $d_{\text{overall}}$ ($\ge 0.30$) among unassigned candidates | `None` |

---

## 7. RecommendationCard & Explanation Model

Every recommended dataset outputs an immutable `RecommendationCard` recording:
- Identifiers: `card_id`, `dataset_id`, `dataset_name`, `task_id`.
- Scores: `final_rank`, `raw_candidate_score`, `component_scores`, `marginal_diversity_gain`.
- Role: `assigned_role`.
- Artifact Provenance: `utility_estimate_id`, `fingerprint_id`, `popularity_profile_id`, `evidence_entry_ids`.
- Categorical Explanations: `why_it_fits`, `why_it_is_not_perfect`, `why_it_appears_here`, `operational_context`.
- Grounded guarantee: Zero ungrounded text or hallucinated claims.
