"""Candidate-level signal extraction and pairwise attribute distance calculation for M7."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from dataset_intelligence.exploration.family import evaluate_family_linkage

FACET_WEIGHTS = {
    "observed": 1.0,
    "corroborated": 0.8,
    "single_source_claim": 0.4,
    "unsupported": 0.2,
    "unknown": 0.2,
    "failed": 0.0,
    "conflicting": 0.0,
}


def normalize_feature_tokens(record: Any) -> set[str]:
    """Extract normalized feature/column tokens from dataset schema or structure."""
    tokens: set[str] = set()
    structure = getattr(record, "structure", {}) if hasattr(record, "structure") else {}
    features = structure.get("features", [])
    if isinstance(features, list):
        for f in features:
            if isinstance(f, str):
                tokens.update(re.findall(r"[a-z0-9]+", f.lower()))
            elif isinstance(f, dict) and "name" in f:
                tokens.update(re.findall(r"[a-z0-9]+", str(f["name"]).lower()))
    return tokens


def compute_attribute_distance(rec1: Any, rec2: Any) -> float:
    """Compute normalized pairwise attribute distance between two datasets in [0.0, 1.0]."""
    did1 = getattr(rec1, "internal_id", "")
    did2 = getattr(rec2, "internal_id", "")
    if did1 and did2 and did1 == did2:
        return 0.0

    # 1. Lineage distance
    state, _ = evaluate_family_linkage(rec1, rec2)
    if state == "same_family":
        d_lineage = 0.0
    elif state == "different_family":
        d_lineage = 1.0
    else:
        d_lineage = 0.5

    # 2. Feature / schema distance
    tok1 = normalize_feature_tokens(rec1)
    tok2 = normalize_feature_tokens(rec2)
    if tok1 and tok2:
        union = tok1 | tok2
        inter = tok1 & tok2
        d_features = 1.0 - (len(inter) / len(union)) if union else 0.5
    elif not tok1 and not tok2:
        d_features = 0.5
    else:
        d_features = 0.8

    # 3. Source distance
    src1 = getattr(rec1, "identity", {}).get("source_name", "unknown")
    src2 = getattr(rec2, "identity", {}).get("source_name", "unknown")
    d_source = 0.0 if (src1 == src2 and src1 != "unknown") else 1.0

    dist = (d_lineage + d_features + d_source) / 3.0
    return round(max(0.0, min(1.0, dist)), 4)


@dataclass(frozen=True)
class CandidateSignals:
    """Orthogonal candidate-level signals synthesized from M1-M6 artifacts."""

    dataset_id: str
    task_id: str
    fit_score: float
    utility_score: float
    evidence_support_score: float
    content_coverage_score: float
    risk_penalty: float

    def validate(self) -> None:
        if not (0.0 <= self.fit_score <= 1.0):
            raise ValueError(f"fit_score out of bounds [0, 1]: {self.fit_score}")
        if not (0.0 <= self.utility_score <= 1.0):
            raise ValueError(f"utility_score out of bounds [0, 1]: {self.utility_score}")
        if not (0.0 <= self.evidence_support_score <= 1.0):
            raise ValueError(f"evidence_support_score out of bounds [0, 1]: {self.evidence_support_score}")
        if not (0.0 <= self.content_coverage_score <= 1.0):
            raise ValueError(f"content_coverage_score out of bounds [0, 1]: {self.content_coverage_score}")
        if not (0.0 <= self.risk_penalty <= 1.0):
            raise ValueError(f"risk_penalty out of bounds [0, 1]: {self.risk_penalty}")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def compute_evidence_support_feature(
    record: Any,
    utility_estimate: Any,
    evidence_entries: list[Any] | None = None,
    fingerprint: Any | None = None,
) -> float:
    """Compute M7 heuristic evidence-support feature across 5 critical operational facets.

    Explicitly designated as heuristic evidence support, NOT an epistemic confidence model.
    """
    components = getattr(utility_estimate, "components", {})

    # Facet 1: Modality verification
    mod_comp = components.get("modality_compatibility")
    mod_state = getattr(mod_comp, "epistemic_state", "unknown") if mod_comp else "unknown"
    w1 = FACET_WEIGHTS.get(mod_state, 0.2)

    # Facet 2: Target / task structure verification
    tgt_comp = components.get("target_compatibility")
    tgt_state = getattr(tgt_comp, "epistemic_state", "unknown") if tgt_comp else "unknown"
    w2 = FACET_WEIGHTS.get(tgt_state, 0.2)

    # Facet 3: Governance / license verification
    gov_comp = components.get("governance_compatibility")
    gov_state = getattr(gov_comp, "epistemic_state", "unknown") if gov_comp else "unknown"
    w3 = FACET_WEIGHTS.get(gov_state, 0.2)

    # Facet 4: Data quality / integrity verification (M4 fingerprint presence)
    if fingerprint is not None and getattr(fingerprint, "primary_modality", "") != "unsupported":
        w4 = 1.0 if getattr(fingerprint, "primary_modality", "") != "failed" else 0.0
    else:
        qual_comp = components.get("quality_compatibility")
        qual_state = getattr(qual_comp, "epistemic_state", "unknown") if qual_comp else "unknown"
        w4 = FACET_WEIGHTS.get(qual_state, 0.2)

    # Facet 5: Endpoint / access verification
    acc_comp = components.get("access_feasibility")
    acc_state = getattr(acc_comp, "epistemic_state", "unknown") if acc_comp else "unknown"
    w5 = FACET_WEIGHTS.get(acc_state, 0.2)

    avg_evid = (w1 + w2 + w3 + w4 + w5) / 5.0
    return round(max(0.0, min(1.0, avg_evid)), 4)


def compute_risk_penalty(
    record: Any,
    task_spec: Any,
    utility_estimate: Any,
    fingerprint: Any | None = None,
) -> float:
    """Compute bounded deterministic risk penalty in [0.0, 1.0]."""
    penalties: list[float] = []
    components = getattr(utility_estimate, "components", {})

    # 1. Unresolved conflicts in M3 / M5
    for comp in components.values():
        if getattr(comp, "epistemic_state", "") == "conflicting":
            penalties.append(0.35)
            break

    # 2. Critical requirement marked unknown
    unresolved = getattr(task_spec, "unresolved_requirements", []) if hasattr(task_spec, "unresolved_requirements") else []
    if "target_requirements" in unresolved or "primary_modality" in unresolved:
        penalties.append(0.25)

    # 3. M4 sample-limited inference (e.g. slice bias)
    for comp in components.values():
        if getattr(comp, "epistemic_state", "") == "sample_limited_inference":
            penalties.append(0.15)
            break

    # 4. Operational access friction (gated/auth required)
    acc_comp = components.get("access_feasibility")
    if acc_comp and getattr(acc_comp, "score", 1.0) < 0.80 and getattr(acc_comp, "epistemic_state", "") != "failed":
        penalties.append(0.15)

    # 5. Degraded sample health in M4 fingerprint
    if fingerprint is not None:
        scope = getattr(fingerprint, "sample_scope", {})
        if isinstance(scope, dict):
            dup = scope.get("duplicate_row_count", 0)
            tot = scope.get("record_count_sampled", 1)
            if tot and (dup / tot) > 0.10:
                penalties.append(0.10)

    total_risk = sum(penalties)
    return round(min(1.0, max(0.0, total_risk)), 4)


def compute_candidate_signals(
    record: Any,
    task_spec: Any,
    utility_estimate: Any,
    evidence_entries: list[Any] | None = None,
    fingerprint: Any | None = None,
    config: dict[str, Any] | None = None,
) -> CandidateSignals:
    """Synthesize orthogonal candidate signals for a dataset against a task specification."""
    components = getattr(utility_estimate, "components", {})

    # 1. Fit score: average of explicit task requirement components
    u_task = getattr(components.get("task_compatibility"), "score", 0.5)
    u_mod = getattr(components.get("modality_compatibility"), "score", 0.5)
    u_tgt = getattr(components.get("target_compatibility"), "score", 0.5)
    fit_score = round((u_task + u_mod + u_tgt) / 3.0, 4)

    # 2. Utility score: strict M5 invariant
    utility_score = round(getattr(utility_estimate, "composite_utility", 0.0), 4)

    # 3. Evidence support feature
    evid_supp = compute_evidence_support_feature(record, utility_estimate, evidence_entries, fingerprint)

    # 4. Content coverage score
    u_struct = getattr(components.get("structural_compatibility"), "score", 0.5)
    missing_ratio = 0.0
    if fingerprint is not None:
        scope = getattr(fingerprint, "sample_scope", {})
        if isinstance(scope, dict):
            missing_ratio = scope.get("missing_cell_ratio", 0.0) or 0.0
    cov_score = round(max(0.0, min(1.0, u_struct * (1.0 - missing_ratio))), 4)

    # 5. Risk penalty
    risk_score = compute_risk_penalty(record, task_spec, utility_estimate, fingerprint)

    did = getattr(record, "internal_id", "")
    tid = getattr(task_spec, "task_id", "")

    signals = CandidateSignals(
        dataset_id=did,
        task_id=tid,
        fit_score=fit_score,
        utility_score=utility_score,
        evidence_support_score=evid_supp,
        content_coverage_score=cov_score,
        risk_penalty=risk_score,
    )
    signals.validate()
    return signals
