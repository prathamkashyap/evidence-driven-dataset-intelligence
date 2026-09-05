# M7 Experiments — Multi-Objective Ranking, Diversification & Recommendation Roles

## Overview

This directory contains empirical artifacts produced by Milestone 7 (`scripts/run_m7_ranking.py`), comparing Baselines R1, R2, and Proposed Baseline R3 across the development tasks.

## Scope & Disclaimers

1. **Development Simulation Scope:** The evaluation operates on the 10-dataset local development corpus. It serves as a proof-of-mechanism for family-aware set selection, heuristic evidence/risk balancing, and post-selection role assignment, **not** as a statistical claim of generalized recommendation superiority.
2. **Popularity Invariance:** Popularity metrics and exploration origin do not enter candidate suitability scoring.
3. **M5 Utility Invariance:** M5 task utility estimates are preserved as read-only invariants ($U_{\text{M7}} \equiv U_{\text{M5}}$).
4. **Heuristic Evidence Weights:** Evidence support weights are configurable baseline heuristics, not calibrated probabilities.

## Generated Artifacts

- `results/ranking_comparison.json`: Task-by-task quantitative comparison across Baselines R1, R2, and R3.
- `results/recommendation_sets.jsonl`: 12 complete `RecommendationSet` outputs containing fully traceable `RecommendationCard` instances.
- `results/m7_summary.json`: Aggregated comparative metrics and runtime measurements (25.48 MiB peak RSS vs 128 MiB ceiling).
