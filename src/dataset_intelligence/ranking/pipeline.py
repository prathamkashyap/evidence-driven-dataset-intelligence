"""Unified RecommendationEngine orchestrating hard gating, multi-objective scoring, diversification, and card generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from dataset_intelligence.exploration.family import evaluate_family_linkage
from .diversification import compute_set_diversity, select_diversified_set
from .explanation import RecommendationCard, build_recommendation_card
from .roles import assign_recommendation_roles
from .scoring import score_candidate_r1, score_candidate_r2, score_candidate_r3
from .signals import CandidateSignals, compute_candidate_signals

DEFAULT_PIPELINE_CONFIG = {
    "target_k": 3,
    "lambda_div": 0.20,
    "baseline_mode": "r3_diversified_set",
}


@dataclass(frozen=True)
class RecommendationSet:
    """Immutable recommendation set output with cards and set-level metrics."""

    set_id: str
    task_id: str
    baseline_mode: str
    cards: tuple[RecommendationCard, ...]
    selected_dataset_ids: tuple[str, ...]
    mean_set_utility: float
    set_diversity_score: float
    same_family_redundancy_count: int
    excluded_gated_candidates: dict[str, str]
    provenance: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "set_id": self.set_id,
            "task_id": self.task_id,
            "baseline_mode": self.baseline_mode,
            "cards": [c.as_dict() for c in self.cards],
            "selected_dataset_ids": list(self.selected_dataset_ids),
            "mean_set_utility": self.mean_set_utility,
            "set_diversity_score": self.set_diversity_score,
            "same_family_redundancy_count": self.same_family_redundancy_count,
            "excluded_gated_candidates": self.excluded_gated_candidates,
            "provenance": self.provenance,
        }


def compute_same_family_redundancy_count(records: list[Any]) -> int:
    """Count number of pairs in records sharing confirmed same_family lineage."""
    n = len(records)
    redundancy_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            state, _ = evaluate_family_linkage(records[i], records[j])
            if state == "same_family":
                redundancy_count += 1
    return redundancy_count


class RecommendationEngine:
    """Orchestrator for M7 dataset ranking, diversification, and recommendation card emission."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or dict(DEFAULT_PIPELINE_CONFIG)

    def recommend(
        self,
        task_spec: Any,
        candidate_records: list[Any],
        utility_estimates: dict[str, Any],
        popularity_profiles: dict[str, Any],
        fingerprints: dict[str, Any] | None = None,
        evidence_entries: dict[str, list[Any]] | None = None,
        baseline_mode: str = "r3_diversified_set",
        target_k: int = 3,
    ) -> RecommendationSet:
        fp_dict = fingerprints or {}
        evid_dict = evidence_entries or {}
        k = max(1, target_k)

        # 1. Hard Gating: Prune fatal incompatibilities before scoring
        eligible_records: list[Any] = []
        excluded_gated: dict[str, str] = {}

        for rec in candidate_records:
            did = getattr(rec, "internal_id", "")
            u_est = utility_estimates.get(did)
            if not u_est:
                excluded_gated[did] = "missing_utility_estimate"
                continue

            if getattr(u_est, "hard_gated", False):
                reason = "hard_constraint_violation"
                # Extract detailed reason from components
                for cname, comp in getattr(u_est, "components", {}).items():
                    if getattr(comp, "score", 1.0) == 0.0 and getattr(comp, "epistemic_state", "") in {
                        "known_unfavorable",
                        "failed",
                    }:
                        reason = f"hard_gate:{cname}"
                        break
                excluded_gated[did] = reason
                continue

            eligible_records.append(rec)

        # 2. Compute candidate signals for eligible candidates
        signals_by_id: dict[str, CandidateSignals] = {}
        for rec in eligible_records:
            did = getattr(rec, "internal_id", "")
            u_est = utility_estimates[did]
            fp = fp_dict.get(did)
            evid = evid_dict.get(did)
            signals_by_id[did] = compute_candidate_signals(
                record=rec,
                task_spec=task_spec,
                utility_estimate=u_est,
                evidence_entries=evid,
                fingerprint=fp,
                config=self.config,
            )

        # 3. Baseline Selection Execution
        selected_tuples: list[tuple[Any, float, float]] = []  # (record, raw_score, marginal_div)

        if baseline_mode == "r1_utility_only":
            # Sort descending by M5 utility
            scored_candidates = [
                (rec, score_candidate_r1(signals_by_id[getattr(rec, "internal_id", "")]))
                for rec in eligible_records
            ]
            scored_candidates.sort(
                key=lambda x: (x[1], getattr(x[0], "internal_id", "")),
                reverse=True,
            )
            for rec, score in scored_candidates[:k]:
                selected_tuples.append((rec, score, 1.0))

        elif baseline_mode == "r2_multiobjective_linear":
            # Sort descending by candidate multi-objective score (no diversification)
            scored_candidates = [
                (rec, score_candidate_r2(signals_by_id[getattr(rec, "internal_id", "")]))
                for rec in eligible_records
            ]
            scored_candidates.sort(
                key=lambda x: (x[1], getattr(x[0], "internal_id", "")),
                reverse=True,
            )
            for rec, score in scored_candidates[:k]:
                selected_tuples.append((rec, score, 1.0))

        elif baseline_mode == "r3_diversified_set":
            # Family-aware bounded greedy diversity selection
            selected_tuples = select_diversified_set(
                candidates=eligible_records,
                signals_by_id=signals_by_id,
                target_k=k,
                lambda_div=self.config.get("lambda_div", 0.20),
                config=self.config,
            )
        else:
            raise ValueError(f"Unsupported baseline mode: {baseline_mode}")

        # 4. Recommendation Role Assignment (Post-Selection)
        role_assignments = assign_recommendation_roles(
            selected_tuples=selected_tuples,
            signals_by_id=signals_by_id,
            utility_estimates_by_id=utility_estimates,
            popularity_profiles_by_id=popularity_profiles,
            fingerprints_by_id=fp_dict,
            config=self.config,
        )

        # 5. Build RecommendationCards
        cards: list[RecommendationCard] = []
        for rank_idx, (rec, raw_score, marginal_div) in enumerate(selected_tuples):
            did = getattr(rec, "internal_id", "")
            card = build_recommendation_card(
                record=rec,
                task_spec=task_spec,
                signals=signals_by_id[did],
                utility_estimate=utility_estimates[did],
                final_rank=rank_idx + 1,
                raw_candidate_score=raw_score,
                marginal_diversity=marginal_div,
                assigned_role=role_assignments.get(did),
                popularity_profile=popularity_profiles.get(did),
                fingerprint=fp_dict.get(did),
                evidence_entry_ids=[
                    getattr(e, "entry_id", str(e)) for e in evid_dict.get(did, [])
                ],
            )
            cards.append(card)

        # 6. Compute Set-Level Metrics
        selected_records = [t[0] for t in selected_tuples]
        selected_ids = tuple(getattr(r, "internal_id", "") for r in selected_records)
        utilities = [signals_by_id[did].utility_score for did in selected_ids if did in signals_by_id]
        mean_utility = round(sum(utilities) / len(utilities), 4) if utilities else 0.0
        set_div = compute_set_diversity(selected_records)
        red_count = compute_same_family_redundancy_count(selected_records)

        tid = getattr(task_spec, "task_id", "")
        payload = {
            "task_id": tid,
            "baseline_mode": baseline_mode,
            "selected_dataset_ids": list(selected_ids),
        }
        set_id = "rec_" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]

        provenance = {
            "target_k": k,
            "lambda_div": self.config.get("lambda_div", 0.20),
            "eligible_candidates_count": len(eligible_records),
            "excluded_gated_count": len(excluded_gated),
        }

        return RecommendationSet(
            set_id=set_id,
            task_id=tid,
            baseline_mode=baseline_mode,
            cards=tuple(cards),
            selected_dataset_ids=selected_ids,
            mean_set_utility=mean_utility,
            set_diversity_score=set_div,
            same_family_redundancy_count=red_count,
            excluded_gated_candidates=excluded_gated,
            provenance=provenance,
        )
