"""RecommendationCard schema and structured explanation generator for M7."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from .signals import CandidateSignals


def compute_card_id(
    task_id: str,
    dataset_id: str,
    final_rank: int,
    raw_candidate_score: float,
    assigned_role: str | None,
) -> str:
    """Compute deterministic content-addressed identity for RecommendationCard."""
    payload = {
        "task_id": task_id,
        "dataset_id": dataset_id,
        "final_rank": final_rank,
        "raw_candidate_score": round(raw_candidate_score, 4),
        "assigned_role": assigned_role or "none",
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "card_" + hashlib.sha256(canonical_bytes).hexdigest()[:24]


@dataclass(frozen=True)
class RecommendationCard:
    """Immutable, fully traceable recommendation card following Section 17 of PROJECT_SPEC."""

    card_id: str
    dataset_id: str
    dataset_name: str
    assigned_role: str | None
    final_rank: int
    raw_candidate_score: float
    component_scores: dict[str, float]
    marginal_diversity_gain: float
    task_id: str
    utility_estimate_id: str
    fingerprint_id: str | None
    popularity_profile_id: str | None
    evidence_entry_ids: list[str]
    why_it_fits: list[str]
    why_it_is_not_perfect: list[str]
    why_it_appears_here: list[str]
    operational_context: dict[str, Any]

    def validate(self) -> None:
        if not self.card_id:
            raise ValueError("card_id cannot be blank.")
        if not self.dataset_id:
            raise ValueError("dataset_id cannot be blank.")
        if self.final_rank < 1:
            raise ValueError(f"Invalid final_rank: {self.final_rank}")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def generate_structured_explanations(
    record: Any,
    task_spec: Any,
    signals: CandidateSignals,
    utility_estimate: Any,
    popularity_profile: Any | None,
    assigned_role: str | None,
    marginal_diversity: float,
) -> tuple[list[str], list[str], list[str], dict[str, Any]]:
    """Generate deterministic, grounded structured explanations without natural language hallucinations."""
    components = getattr(utility_estimate, "components", {})
    why_fits: list[str] = []
    why_imperfect: list[str] = []
    why_here: list[str] = []

    # 1. Why it fits
    task_comp = components.get("task_compatibility")
    if task_comp and getattr(task_comp, "epistemic_state", "") == "known_favorable":
        why_fits.append(f"Direct task alignment: verified {getattr(task_spec, 'task_type', 'task')} compatibility.")

    mod_comp = components.get("modality_compatibility")
    if mod_comp and getattr(mod_comp, "epistemic_state", "") == "known_favorable":
        why_fits.append(f"Modality match: verified {getattr(task_spec, 'primary_modality', 'modality')} format.")

    tgt_comp = components.get("target_compatibility")
    if tgt_comp and getattr(tgt_comp, "epistemic_state", "") == "known_favorable":
        why_fits.append("Target structure alignment: label and class structure match task requirements.")

    struct_comp = components.get("structural_compatibility")
    if struct_comp and getattr(struct_comp, "epistemic_state", "") == "known_favorable":
        why_fits.append("Structural match: feature dimensionality and sample bounds align with requirements.")

    if not why_fits:
        why_fits.append(f"Basic compatibility across task requirements (fit score: {signals.fit_score:.2f}).")

    # 2. Why it is not perfect
    for name, comp in components.items():
        state = getattr(comp, "epistemic_state", "")
        if state == "conflicting":
            why_imperfect.append(f"Unresolved conflict in {name.replace('_compatibility', '')} evidence.")
        elif state == "sample_limited_inference":
            why_imperfect.append(f"Sample-limited inference: {name.replace('_compatibility', '')} based on bounded 32-row probe.")
        elif state == "unknown":
            why_imperfect.append(f"Unmeasured evidence for {name.replace('_compatibility', '')}.")
        elif state == "failed":
            why_imperfect.append(f"Operational probe failure in {name.replace('_compatibility', '')}.")

    unres = getattr(task_spec, "unresolved_requirements", [])
    if unres:
        why_imperfect.append(f"Task specification contains unresolved requirements: {sorted(unres)}.")

    if not why_imperfect:
        why_imperfect.append("No critical defects or conflicts identified in evidence ledger.")

    # 3. Why it appears here
    if assigned_role:
        why_here.append(f"Assigned recommendation role: '{assigned_role}'.")
    if marginal_diversity > 0.5:
        why_here.append(f"High marginal diversity contribution ({marginal_diversity:.2f}) relative to preceding selections.")
    why_here.append(f"Multi-objective suitability balance: utility {signals.utility_score:.2f}, fit {signals.fit_score:.2f}, evidence support {signals.evidence_support_score:.2f}.")

    # Operational context
    gov = getattr(record, "governance", {}) if hasattr(record, "governance") else {}
    src = getattr(record, "identity", {}).get("source_name", "unknown") if hasattr(record, "identity") else "unknown"
    stratum = getattr(popularity_profile, "popularity_stratum", "unknown") if popularity_profile else "unknown"

    op_context = {
        "source_name": src,
        "license_claim": gov.get("license", "unknown"),
        "access_restriction": gov.get("access_restrictions", "unrestricted"),
        "popularity_stratum": stratum,
    }

    return why_fits, why_imperfect, why_here, op_context


def build_recommendation_card(
    record: Any,
    task_spec: Any,
    signals: CandidateSignals,
    utility_estimate: Any,
    final_rank: int,
    raw_candidate_score: float,
    marginal_diversity: float,
    assigned_role: str | None,
    popularity_profile: Any | None = None,
    fingerprint: Any | None = None,
    evidence_entry_ids: list[str] | None = None,
) -> RecommendationCard:
    """Build immutable RecommendationCard with complete provenance."""
    did = getattr(record, "internal_id", "")
    dname = getattr(record, "identity", {}).get("dataset_name", did)
    tid = getattr(task_spec, "task_id", "")
    uid = getattr(utility_estimate, "estimate_id", "")
    fid = getattr(fingerprint, "fingerprint_id", None) if fingerprint else None
    pid = getattr(popularity_profile, "profile_id", None) if popularity_profile else None
    eids = evidence_entry_ids or []

    why_fits, why_imp, why_here, op_ctx = generate_structured_explanations(
        record=record,
        task_spec=task_spec,
        signals=signals,
        utility_estimate=utility_estimate,
        popularity_profile=popularity_profile,
        assigned_role=assigned_role,
        marginal_diversity=marginal_diversity,
    )

    card_id = compute_card_id(
        task_id=tid,
        dataset_id=did,
        final_rank=final_rank,
        raw_candidate_score=raw_candidate_score,
        assigned_role=assigned_role,
    )

    card = RecommendationCard(
        card_id=card_id,
        dataset_id=did,
        dataset_name=dname,
        assigned_role=assigned_role,
        final_rank=final_rank,
        raw_candidate_score=round(raw_candidate_score, 4),
        component_scores=signals.as_dict(),
        marginal_diversity_gain=round(marginal_diversity, 4),
        task_id=tid,
        utility_estimate_id=uid,
        fingerprint_id=fid,
        popularity_profile_id=pid,
        evidence_entry_ids=sorted(eids),
        why_it_fits=why_fits,
        why_it_is_not_perfect=why_imp,
        why_it_appears_here=why_here,
        operational_context=op_ctx,
    )
    card.validate()
    return card
