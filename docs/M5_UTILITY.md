# Milestone 5 — Task Utility Estimation Specification

## 1. Overview and Purpose

Milestone 5 introduces **task utility estimation**, the first stage in the intelligence pipeline where dataset evidence is explicitly interpreted against a user's structured task requirements.

M5 answers:
> *"Given a structured task specification, how useful does each candidate dataset appear based on available metadata, M3 evidence, and M4 bounded content fingerprints, while preserving uncertainty and without performing final recommendation ranking?"*

---

## 2. Core Epistemic & Methodological Principles

1. **Equal-Weight Linear Baseline Assumption:** The composite scalar utility $U_{\text{baseline}}(D \mid T) = \sum_{k=1}^7 w_k u_k$ ($w_k = 1/7$) is an interpretable, transparent baseline. It is **not** claimed to be optimal, learned, or an objective probability.
2. **Categorical Provenance over Numerical Probabilities:** Epistemic states (`known_favorable`, `known_unfavorable`, `unknown`, `unsupported`, `failed`, `conflicting`, `sample_limited_inference`) are strictly categorical and never converted into arbitrary probability numbers or uncalibrated confidence scores.
3. **Preservation of the Uncollapsed Component Vector:** Every evaluation preserves the complete vector of 7 utility components (`components: dict[str, UtilityComponent]`), enabling downstream multi-objective trade-offs in M7.
4. **Separation of Governance and Access:** Legal rights (licensing, usage policies) and operational network availability (endpoints, credentials, HTTP status) are evaluated as separate components.
5. **Slice-Bias Rule in Sample Inference:** Observing 1 class in a bounded 32-record contiguous sample slice (as seen on Rotten Tomatoes in M4) is classified as `sample_limited_inference`, preventing false assumptions that the dataset is single-class.
6. **Hard Gating Restricted to Verifiable Incompatibilities:** Gating ($U=0.0$) triggers strictly on confirmed modality clash, explicitly prohibited licenses, or strict public access requirements on confirmed gated repositories.

---

## 3. TaskSpecification Data Schema

`TaskSpecification` is an immutable, frozen dataclass with schema version `"1.0"`:

```python
@dataclass(frozen=True)
class TaskSpecification:
    task_id: str                              # 'task_' + sha256(...)[:24]
    specification_version: str                # '1.0'
    task_type: str                            # 'classification', 'regression', 'unknown'
    primary_modality: str                     # 'text', 'tabular', 'image', 'multimodal', 'unknown'
    domain: str | None                        # e.g. 'movie_reviews', 'botany', 'news'
    target_requirements: dict[str, Any]       # target_type, expected_classes, class_labels
    input_constraints: dict[str, Any]         # min_tokens, max_tokens, required_features, min_features
    scale_constraints: dict[str, Any]         # min_sample_count
    governance_constraints: dict[str, Any]    # allowed_licenses, prohibited_licenses, commercial_required
    access_constraints: dict[str, Any]        # public_access_required, allow_gated
    explicit_user_constraints: dict[str, Any] # Arbitrary user-stated flags
    unresolved_requirements: tuple[str, ...]  # Explicitly models unstated requirements
    raw_query: str | None                     # Natural-language query provenance
```

---

## 4. The Seven Utility Components

| Component | Evaluated Scope | Baseline Score Mapping | Epistemic Basis |
|---|---|---|---|
| **1. Task Compatibility** (`task_compatibility`) | Task alignment (`classification`, `regression`) | Exact/aligned: 1.0; Related: 1.0; Unstated: 0.5; Mismatch: 0.0 | Publisher claim or corroborated observation |
| **2. Modality Compatibility** (`modality_compatibility`) | Modality match (`text`, `tabular`, `image`) | Exact: 1.0; Unknown/multimodal: 0.5; Confirmed clash: 0.0 | Publisher claim or direct observation |
| **3. Target Compatibility** (`target_compatibility`) | Target type and class cardinality | Match: 1.0; Contiguous slice bias: 0.8; Unobserved: 0.7; Mismatch: 0.0 | Direct observation, bounded sample, or publisher claim |
| **4. Structural Compatibility** (`structural_compatibility`) | Token limits, feature counts, dimensions | Constraints met: 1.0; Unconstrained: 1.0; Exceeded/below: 0.3–0.5 | Direct observation or publisher claim |
| **5. Quality Compatibility** (`quality_compatibility`) | Sample cleanliness (nulls, duplicates, constant columns) | $1.0 - (\text{nulls} + \text{duplicates} + \text{degenerate})$; Unobserved: 0.5 | Direct observation or unstated |
| **6. Governance Compatibility** (`governance_compatibility`) | License permissiveness and restrictions | Allowed: 1.0; Permissive default: 1.0; Conflicting: 0.5; Prohibited: 0.0 | Publisher claim or corroborated resolution |
| **7. Access Feasibility** (`access_feasibility`) | Operational network and credential status | Working public: 1.0; Unknown: 0.5; Unsupported (Kaggle): 0.3; Failed (502): 0.2 | Direct observation |

---

## 5. Comparative Baselines (A, B, C)

1. **Baseline A (Metadata-Only):**
   - Naively trusts raw publisher metadata strings.
   - Ignores M3 claim conflicts, operational endpoint failures, and M4 content fingerprints.
   - Assumes unobserved quality and access are 1.0.
2. **Baseline B (Metadata + M3 Evidence):**
   - Incorporates M3 `EvidenceLedger` entries and claim resolutions.
   - Surfaces license conflicts (`conflicting`), identifies HTTP 502 errors (`failed`), and credential gating (`unsupported`).
   - Leaves data quality unobserved (neutral 0.5).
3. **Baseline C (Full Evidence-Driven Utility):**
   - Incorporates `CanonicalDataset` + `EvidenceLedger` + `DatasetFingerprint`.
   - Evaluates empirical sample cleanliness (null rates, constant features), verifies token/feature bounds, and applies the slice-bias rule to label distributions.

---

## 6. Hard-Gating Rules

Hard gating ($G=0.0 \implies \text{composite\_utility} = 0.0$) triggers **only** on verified hard constraints:
1. **Modality Clash:** `task_spec.primary_modality` is explicitly specified (e.g. `"image"`), and dataset modality is confirmed disjoint (e.g. confirmed `"tabular"` with 0 image features).
2. **Prohibited License:** `governance_constraints["prohibited_licenses"]` contains the dataset's confirmed license.
3. **Strict Public Access on Gated Source:** `access_constraints["public_access_required"] == True` on a source requiring credentials under M0 policy (e.g. Kaggle).

---

## 7. Development Reference Compatibility Rubric

- **Level 3 (High Compatibility):** Modality, task type, target structure, and feature characteristics match all specified task constraints.
- **Level 2 (Moderate Compatibility):** Modality and task match, but secondary constraints (licensing uncertainty, operational access limitation, or feature differences) exist.
- **Level 1 (Marginal / Domain Incompatible):** Modality matches, but task or domain is substantially mismatched (e.g. news topic dataset for a movie sentiment task).
- **Level 0 (Incompatible):** Hard incompatibility (modality clash or prohibited license/access).

---

## 8. Explicit M5 vs. M6 / M7 Boundary

| Dimension | Milestone 5 (Utility Estimation) | Milestone 6 (Long-Tail Exploration) | Milestone 7 (Recommendation & Diversification) |
|---|---|---|---|
| **Core Question** | "Does candidate $D$ satisfy task $T$ based on evidence?" | "Are high-utility candidates being ignored due to popularity bias?" | "What is the optimal, diverse set of datasets to recommend?" |
| **Output Type** | Standalone `TaskUtilityEstimate` per dataset | Exposure Disparity audit & dual candidate pool | Multi-objective ranking set with assigned recommendation roles |
| **Popularity Signals** | Excluded | Audited across popularity strata (downloads/stars) | Excluded from suitability; used only for context |
| **Candidate Role Assignment** | None | None | Best overall, Best efficient, Hidden gem, etc. |
| **GIST / Submodular Selection** | None | None | Evaluates set diversity and redundancy |
