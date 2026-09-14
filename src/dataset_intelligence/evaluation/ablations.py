"""M8-only ablations that leave the frozen M7 implementation untouched."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from dataset_intelligence.ranking.diversification import compute_set_diversity
from dataset_intelligence.ranking.explanation import RecommendationCard, build_recommendation_card
from dataset_intelligence.ranking.pipeline import (
    DEFAULT_PIPELINE_CONFIG,
    RecommendationSet,
    compute_same_family_redundancy_count,
)
from dataset_intelligence.ranking.roles import assign_recommendation_roles
from dataset_intelligence.ranking.scoring import (
    score_candidate_r1,
    score_candidate_r2,
    score_candidate_r3,
)
from dataset_intelligence.ranking.signals import (
    CandidateSignals,
    compute_attribute_distance,
    compute_candidate_signals,
)
from dataset_intelligence.retrieval.bm25 import BM25Index
from dataset_intelligence.retrieval.dense import (
    DenseIndex,
    SentenceTransformersEncoder,
    TestDenseEncoder,
)
from dataset_intelligence.retrieval.documents import build_retrieval_document
from dataset_intelligence.retrieval.fusion import reciprocal_rank_fusion
from dataset_intelligence.retrieval.query import normalize_query


def select_farthest_first_without_family_check(
    candidates: list[Any],
    signals_by_id: dict[str, CandidateSignals],
    *,
    target_k: int,
    lambda_div: float,
) -> list[tuple[Any, float, float]]:
    """R7: the M7 greedy loop with exactly one deletion: family exclusion.

    Candidate score, attribute distance, k, ordering, and tie breaking match the
    frozen R3 selector. This function exists in M8 rather than changing M7.
    """
    selected: list[tuple[Any, float, float]] = []
    selected_records: list[Any] = []
    selected_ids: set[str] = set()
    while len(selected) < max(1, target_k):
        best_candidate: Any = None
        best_cand_score = -1.0
        best_marginal_div = 0.0
        best_marginal_gain = float("-inf")
        for candidate in candidates:
            dataset_id = getattr(candidate, "internal_id", "")
            if dataset_id in selected_ids:
                continue
            signals = signals_by_id.get(dataset_id)
            if signals is None:
                continue
            candidate_score = score_candidate_r3(signals)
            marginal_diversity = 1.0 if not selected_records else min(
                compute_attribute_distance(candidate, selected_record) for selected_record in selected_records
            )
            marginal_gain = candidate_score + lambda_div * marginal_diversity
            candidate_key = (round(marginal_gain, 6), round(candidate_score, 6), dataset_id)
            best_key = (
                round(best_marginal_gain, 6),
                round(best_cand_score, 6),
                getattr(best_candidate, "internal_id", "") if best_candidate else "",
            )
            if best_candidate is None or candidate_key > best_key:
                best_candidate = candidate
                best_cand_score = candidate_score
                best_marginal_div = marginal_diversity
                best_marginal_gain = marginal_gain
        if best_candidate is None:
            break
        selected_ids.add(getattr(best_candidate, "internal_id", ""))
        selected_records.append(best_candidate)
        selected.append((best_candidate, best_cand_score, round(best_marginal_div, 4)))
    return selected


def recommend_rung_7(
    task_spec: Any,
    candidate_records: list[Any],
    utility_estimates: dict[str, Any],
    popularity_profiles: dict[str, Any],
    fingerprints: dict[str, Any] | None = None,
    evidence_entries: dict[str, list[Any]] | None = None,
    target_k: int = 3,
    config: dict[str, Any] | None = None,
) -> RecommendationSet:
    """Execute Rung 7 (Farthest-First without Family Check) as a RecommendationSet.

    Strictly controlled against M7 R3: identical hard gating, candidate signals,
    intrinsic score, attribute distance, target_k, lambda_div, and role assignment.
    Only family-aware mirror exclusion is omitted.
    """
    cfg = config or dict(DEFAULT_PIPELINE_CONFIG)
    fp_dict = fingerprints or {}
    evid_dict = evidence_entries or {}
    k = max(1, target_k)
    lambda_div = cfg.get("lambda_div", 0.20)

    # 1. Hard Gating (identical to M7 RecommendationEngine)
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

    # 2. Candidate Signals (identical to M7)
    signals_by_id: dict[str, CandidateSignals] = {}
    for rec in eligible_records:
        did = getattr(rec, "internal_id", "")
        u_est = utility_estimates[did]
        signals_by_id[did] = compute_candidate_signals(
            record=rec,
            task_spec=task_spec,
            utility_estimate=u_est,
            evidence_entries=evid_dict.get(did),
            fingerprint=fp_dict.get(did),
            config=cfg,
        )

    # 3. Selection via Farthest-First Traversal (no family check)
    selected_tuples = select_farthest_first_without_family_check(
        candidates=eligible_records,
        signals_by_id=signals_by_id,
        target_k=k,
        lambda_div=lambda_div,
    )

    # 4. Role Assignment (identical to M7)
    role_assignments = assign_recommendation_roles(
        selected_tuples=selected_tuples,
        signals_by_id=signals_by_id,
        utility_estimates_by_id=utility_estimates,
        popularity_profiles_by_id=popularity_profiles,
        fingerprints_by_id=fp_dict,
        config=cfg,
    )

    # 5. Recommendation Cards (identical to M7)
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
            evidence_entry_ids=[getattr(e, "entry_id", str(e)) for e in evid_dict.get(did, [])],
        )
        cards.append(card)

    # 6. Set-level Metrics
    selected_records = [t[0] for t in selected_tuples]
    selected_ids = tuple(getattr(r, "internal_id", "") for r in selected_records)
    utilities = [signals_by_id[did].utility_score for did in selected_ids if did in signals_by_id]
    mean_utility = round(sum(utilities) / len(utilities), 4) if utilities else 0.0
    set_div = compute_set_diversity(selected_records)
    red_count = compute_same_family_redundancy_count(selected_records)

    tid = getattr(task_spec, "task_id", "")
    payload = {
        "task_id": tid,
        "baseline_mode": "rung_7_farthest_first_no_family",
        "selected_dataset_ids": list(selected_ids),
    }
    set_id = "rec_" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]

    provenance = {
        "target_k": k,
        "lambda_div": lambda_div,
        "eligible_candidates_count": len(eligible_records),
        "excluded_gated_count": len(excluded_gated),
        "ablation_rung": 7,
        "family_check_active": False,
    }

    return RecommendationSet(
        set_id=set_id,
        task_id=tid,
        baseline_mode="rung_7_farthest_first_no_family",
        cards=tuple(cards),
        selected_dataset_ids=selected_ids,
        mean_set_utility=mean_utility,
        set_diversity_score=set_div,
        same_family_redundancy_count=red_count,
        excluded_gated_candidates=excluded_gated,
        provenance=provenance,
    )


def execute_ablation_rung(
    rung_id: int,
    task_spec: Any,
    candidate_records: list[Any],
    utility_estimates: dict[str, Any],
    popularity_profiles: dict[str, Any],
    fingerprints: dict[str, Any] | None = None,
    evidence_entries: dict[str, list[Any]] | None = None,
    target_k: int = 3,
    config: dict[str, Any] | None = None,
    retrieval_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a single ablation rung (0 through 8) on a task.

    Returns a structured dictionary with rung metadata and set-level measurements.
    """
    records_by_id = {getattr(r, "internal_id", ""): r for r in candidate_records}
    k = max(1, target_k)
    rung_names = {
        0: "rung_0_corpus_order",
        1: "rung_1_bm25_only",
        2: "rung_2_dense_only",
        3: "rung_3_hybrid_rrf",
        4: "rung_4_hybrid_hard_gating",
        5: "rung_5_utility_only",
        6: "rung_6_multiobjective_linear",
        7: "rung_7_farthest_first_no_family",
        8: "rung_8_full_system",
    }
    rung_name = rung_names.get(rung_id, f"rung_{rung_id}")

    if rung_id == 0:
        # Rung 0: Corpus order / arbitrary baseline. Takes first k in candidate pool order.
        selected_ids = [getattr(r, "internal_id", "") for r in candidate_records[:k]]

    elif rung_id in (1, 2, 3, 4):
        # Retrieval-based rungs
        ctx = retrieval_context or {}
        bm25_index = ctx.get("bm25_index")
        dense_index = ctx.get("dense_index")
        documents = ctx.get("documents", [])

        if bm25_index is None or dense_index is None:
            # Build on the fly from candidate records
            docs = [build_retrieval_document(r.as_dict() if hasattr(r, "as_dict") else r) for r in candidate_records]
            bm25_index = BM25Index(docs)
            encoder = ctx.get("encoder") or TestDenseEncoder()
            dense_vectors = encoder.encode([d["text"] for d in docs])
            dense_index = DenseIndex(docs, dense_vectors, encoder)

        query_text = getattr(task_spec, "raw_query", "") or getattr(task_spec, "task_type", "")
        q = normalize_query(getattr(task_spec, "task_id", "q"), query_text)

        if rung_id == 1:
            # BM25-only
            bm25_pairs = bm25_index.search(q.keywords, len(candidate_records))
            selected_ids = [doc["dataset_id"] for doc, _ in bm25_pairs[:k]]

        elif rung_id == 2:
            # Dense-only
            dense_pairs = dense_index.search(q.normalized_text, len(candidate_records))
            selected_ids = [doc["dataset_id"] for doc, _ in dense_pairs[:k]]

        elif rung_id == 3:
            # Hybrid RRF (no gating)
            bm25_rows = [{"dataset_id": doc["dataset_id"], "source": doc.get("source", "unknown"), "rank": rank, "score": score} for rank, (doc, score) in enumerate(bm25_index.search(q.keywords, len(candidate_records)), 1)]
            dense_rows = [{"dataset_id": doc["dataset_id"], "source": doc.get("source", "unknown"), "rank": rank, "score": score} for rank, (doc, score) in enumerate(dense_index.search(q.normalized_text, len(candidate_records)), 1)]
            fused = reciprocal_rank_fusion({"bm25": bm25_rows, "dense": dense_rows}, len(candidate_records), rrf_k=60)
            selected_ids = [row["dataset_id"] for row in fused[:k]]

        elif rung_id == 4:
            # Hybrid + Hard Gating
            bm25_rows = [{"dataset_id": doc["dataset_id"], "source": doc.get("source", "unknown"), "rank": rank, "score": score} for rank, (doc, score) in enumerate(bm25_index.search(q.keywords, len(candidate_records)), 1)]
            dense_rows = [{"dataset_id": doc["dataset_id"], "source": doc.get("source", "unknown"), "rank": rank, "score": score} for rank, (doc, score) in enumerate(dense_index.search(q.normalized_text, len(candidate_records)), 1)]
            fused = reciprocal_rank_fusion({"bm25": bm25_rows, "dense": dense_rows}, len(candidate_records), rrf_k=60)
            # Filter out hard-gated candidates
            eligible_fused = []
            for row in fused:
                did = row["dataset_id"]
                u_est = utility_estimates.get(did)
                if u_est and getattr(u_est, "hard_gated", False):
                    continue
                eligible_fused.append(row)
            selected_ids = [row["dataset_id"] for row in eligible_fused[:k]]

    elif rung_id in (5, 6, 8):
        from dataset_intelligence.ranking.pipeline import RecommendationEngine

        mode_map = {
            5: "r1_utility_only",
            6: "r2_multiobjective_linear",
            8: "r3_diversified_set",
        }
        engine = RecommendationEngine(config=config)
        rec_set = engine.recommend(
            task_spec=task_spec,
            candidate_records=candidate_records,
            utility_estimates=utility_estimates,
            popularity_profiles=popularity_profiles,
            fingerprints=fingerprints,
            evidence_entries=evidence_entries,
            baseline_mode=mode_map[rung_id],
            target_k=k,
        )
        selected_ids = list(rec_set.selected_dataset_ids)

    elif rung_id == 7:
        rec_set = recommend_rung_7(
            task_spec=task_spec,
            candidate_records=candidate_records,
            utility_estimates=utility_estimates,
            popularity_profiles=popularity_profiles,
            fingerprints=fingerprints,
            evidence_entries=evidence_entries,
            target_k=k,
            config=config,
        )
        selected_ids = list(rec_set.selected_dataset_ids)

    else:
        raise ValueError(f"Unsupported ablation rung_id: {rung_id}")

    # Compute standard set-level metrics
    selected_recs = [records_by_id[did] for did in selected_ids if did in records_by_id]
    u_vals = [
        getattr(utility_estimates.get(did), "composite_utility", 0.0)
        for did in selected_ids
        if did in utility_estimates
    ]
    mean_u = round(sum(u_vals) / len(u_vals), 4) if u_vals else 0.0
    set_div = compute_set_diversity(selected_recs)
    red_count = compute_same_family_redundancy_count(selected_recs)

    return {
        "rung_id": rung_id,
        "rung_name": rung_name,
        "task_id": getattr(task_spec, "task_id", ""),
        "selected_dataset_ids": selected_ids,
        "mean_set_utility": mean_u,
        "set_diversity_score": set_div,
        "same_family_redundancy_count": red_count,
    }
