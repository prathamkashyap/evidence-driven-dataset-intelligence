"""Parameter sensitivity and stability analysis for Milestone 8.

Implements normalized positive weight perturbations, independent risk-weight perturbations,
and lambda_div sweeps according to docs/M8_EVALUATION.md §6.
"""

from __future__ import annotations

from typing import Any

from dataset_intelligence.evaluation.metrics import kendall_tau, mean, set_jaccard
from dataset_intelligence.ranking.pipeline import RecommendationEngine
from dataset_intelligence.ranking.scoring import DEFAULT_SCORING_WEIGHTS

DEFAULT_POSITIVE_KEYS = ("w_fit", "w_util", "w_evid", "w_cov")


def perturb_positive_weights(
    default_weights: dict[str, float],
    target_key: str,
    delta: float,
) -> dict[str, float]:
    """Perturb one positive weight by relative delta (e.g. +0.20) and renormalize positive sum to 1.0."""
    perturbed = dict(default_weights)
    raw_val = default_weights[target_key] * (1.0 + delta)
    perturbed[target_key] = raw_val

    pos_sum = sum(perturbed[k] for k in DEFAULT_POSITIVE_KEYS)
    for k in DEFAULT_POSITIVE_KEYS:
        perturbed[k] = round(perturbed[k] / pos_sum, 6)

    # Risk weight is subtractive and kept unperturbed in this test
    perturbed["w_risk"] = default_weights.get("w_risk", 0.15)
    return perturbed


def evaluate_parameter_sensitivity(
    task_specs: dict[str, Any],
    candidate_records: list[Any],
    utility_estimates_by_task: dict[str, dict[str, Any]],
    popularity_profiles: dict[str, Any],
    fingerprints: dict[str, Any],
    evidence_entries: dict[str, list[Any]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run full sensitivity protocol across tasks and perturbations."""
    cfg = config or {}
    sens_cfg = cfg.get("sensitivity", {})
    rel_deltas = sens_cfg.get("positive_weight_relative_perturbations", [-0.20, 0.20])
    risk_weights = sens_cfg.get("risk_weights", [0.12, 0.15, 0.18])
    lambda_div_values = sens_cfg.get("lambda_div_values", [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40])
    target_k = cfg.get("target_k", 3)
    default_weights = dict(cfg.get("scoring_weights") or DEFAULT_SCORING_WEIGHTS)
    default_lambda = cfg.get("lambda_div", 0.20)

    # Pre-compute default recommendation sets under R3
    engine_default = RecommendationEngine(config=cfg)
    default_sets: dict[str, Any] = {}
    for task_name, spec in task_specs.items():
        tid = getattr(spec, "task_id", "")
        rec_set = engine_default.recommend(
            task_spec=spec,
            candidate_records=candidate_records,
            utility_estimates=utility_estimates_by_task.get(tid, {}),
            popularity_profiles=popularity_profiles,
            fingerprints=fingerprints,
            evidence_entries=evidence_entries,
            baseline_mode="r3_diversified_set",
            target_k=target_k,
        )
        default_sets[task_name] = rec_set

    # 1. Positive weight perturbations
    positive_results: list[dict[str, Any]] = []
    jaccard_scores: list[float] = []
    tau_scores: list[float] = []

    for weight_key in DEFAULT_POSITIVE_KEYS:
        for delta in rel_deltas:
            new_weights = perturb_positive_weights(default_weights, weight_key, delta)
            perturbed_cfg = dict(cfg)
            perturbed_cfg["scoring_weights"] = new_weights
            engine = RecommendationEngine(config=perturbed_cfg)

            task_comparisons: dict[str, Any] = {}
            for task_name, spec in task_specs.items():
                tid = getattr(spec, "task_id", "")
                rec_set = engine.recommend(
                    task_spec=spec,
                    candidate_records=candidate_records,
                    utility_estimates=utility_estimates_by_task.get(tid, {}),
                    popularity_profiles=popularity_profiles,
                    fingerprints=fingerprints,
                    evidence_entries=evidence_entries,
                    baseline_mode="r3_diversified_set",
                    target_k=target_k,
                )
                def_ids = list(default_sets[task_name].selected_dataset_ids)
                pert_ids = list(rec_set.selected_dataset_ids)
                j = set_jaccard(def_ids, pert_ids)
                tau = kendall_tau(def_ids, pert_ids)
                if j is not None:
                    jaccard_scores.append(j)
                if tau is not None:
                    tau_scores.append(tau)
                task_comparisons[task_name] = {
                    "default_ids": def_ids,
                    "perturbed_ids": pert_ids,
                    "jaccard": j,
                    "kendall_tau": tau,
                }

            positive_results.append({
                "perturbed_weight": weight_key,
                "relative_delta": delta,
                "weights_used": new_weights,
                "mean_jaccard": mean([c["jaccard"] for c in task_comparisons.values() if c["jaccard"] is not None]),
                "mean_kendall_tau": mean([c["kendall_tau"] for c in task_comparisons.values() if c["kendall_tau"] is not None]),
                "tasks": task_comparisons,
            })

    # 2. Risk weight perturbations
    risk_results: list[dict[str, Any]] = []
    for r_weight in risk_weights:
        new_weights = dict(default_weights)
        new_weights["w_risk"] = r_weight
        perturbed_cfg = dict(cfg)
        perturbed_cfg["scoring_weights"] = new_weights
        engine = RecommendationEngine(config=perturbed_cfg)

        task_comparisons = {}
        for task_name, spec in task_specs.items():
            tid = getattr(spec, "task_id", "")
            rec_set = engine.recommend(
                task_spec=spec,
                candidate_records=candidate_records,
                utility_estimates=utility_estimates_by_task.get(tid, {}),
                popularity_profiles=popularity_profiles,
                fingerprints=fingerprints,
                evidence_entries=evidence_entries,
                baseline_mode="r3_diversified_set",
                target_k=target_k,
            )
            def_ids = list(default_sets[task_name].selected_dataset_ids)
            pert_ids = list(rec_set.selected_dataset_ids)
            j = set_jaccard(def_ids, pert_ids)
            tau = kendall_tau(def_ids, pert_ids)
            if j is not None:
                jaccard_scores.append(j)
            if tau is not None:
                tau_scores.append(tau)
            task_comparisons[task_name] = {
                "default_ids": def_ids,
                "perturbed_ids": pert_ids,
                "jaccard": j,
                "kendall_tau": tau,
            }

        risk_results.append({
            "w_risk": r_weight,
            "mean_jaccard": mean([c["jaccard"] for c in task_comparisons.values() if c["jaccard"] is not None]),
            "mean_kendall_tau": mean([c["kendall_tau"] for c in task_comparisons.values() if c["kendall_tau"] is not None]),
            "tasks": task_comparisons,
        })

    # 3. Lambda_div sweep
    lambda_results: list[dict[str, Any]] = []
    for l_val in lambda_div_values:
        perturbed_cfg = dict(cfg)
        perturbed_cfg["lambda_div"] = l_val
        engine = RecommendationEngine(config=perturbed_cfg)

        task_comparisons = {}
        u_vals: list[float] = []
        div_vals: list[float] = []
        red_counts: list[int] = []

        for task_name, spec in task_specs.items():
            tid = getattr(spec, "task_id", "")
            rec_set = engine.recommend(
                task_spec=spec,
                candidate_records=candidate_records,
                utility_estimates=utility_estimates_by_task.get(tid, {}),
                popularity_profiles=popularity_profiles,
                fingerprints=fingerprints,
                evidence_entries=evidence_entries,
                baseline_mode="r3_diversified_set",
                target_k=target_k,
            )
            def_ids = list(default_sets[task_name].selected_dataset_ids)
            pert_ids = list(rec_set.selected_dataset_ids)
            j = set_jaccard(def_ids, pert_ids)
            tau = kendall_tau(def_ids, pert_ids)
            u_vals.append(rec_set.mean_set_utility)
            div_vals.append(rec_set.set_diversity_score)
            red_counts.append(rec_set.same_family_redundancy_count)

            task_comparisons[task_name] = {
                "selected_ids": pert_ids,
                "jaccard_vs_default": j,
                "kendall_tau_vs_default": tau,
                "mean_utility": rec_set.mean_set_utility,
                "set_diversity": rec_set.set_diversity_score,
                "redundancy_count": rec_set.same_family_redundancy_count,
            }

        lambda_results.append({
            "lambda_div": l_val,
            "mean_utility": mean(u_vals),
            "mean_diversity": mean(div_vals),
            "total_redundancy": sum(red_counts),
            "mean_jaccard_vs_default": mean([c["jaccard_vs_default"] for c in task_comparisons.values() if c["jaccard_vs_default"] is not None]),
            "tasks": task_comparisons,
        })

    # Overall Stability Assessment
    overall_mean_jaccard = mean(jaccard_scores) or 0.0
    overall_mean_tau = mean(tau_scores) or 0.0
    jaccard_criterion = overall_mean_jaccard >= sens_cfg.get("mean_jaccard_minimum", 0.80)
    tau_criterion = overall_mean_tau >= sens_cfg.get("kendall_tau_minimum", 0.75)
    stable = jaccard_criterion and tau_criterion

    return {
        "status": "stable" if stable else "unstable",
        "overall_mean_jaccard": round(overall_mean_jaccard, 4),
        "overall_mean_kendall_tau": round(overall_mean_tau, 4),
        "jaccard_criterion_met": jaccard_criterion,
        "kendall_tau_criterion_met": tau_criterion,
        "stability_criteria_met": stable,
        "positive_weight_perturbations": positive_results,
        "risk_weight_perturbations": risk_results,
        "lambda_div_sweep": lambda_results,
    }
