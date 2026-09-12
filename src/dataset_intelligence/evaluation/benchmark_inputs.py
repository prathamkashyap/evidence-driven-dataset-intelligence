"""Validation of frozen M8 benchmark inputs; deliberately contains no evaluation logic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_TASK_ORDER = (
    "task_sentiment_binary",
    "task_news_multiclass",
    "task_tabular_iris",
    "task_image_cifar",
    "task_tabular_diabetes",
    "task_tabular_wine",
    "task_tabular_titanic",
    "task_image_leaf_disease",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def validate_frozen_benchmark_inputs(root: Path) -> dict[str, int]:
    """Validate frozen M8 inputs without reading network state or running M7."""
    config = load_json(root / "configs/m8_evaluation.json")
    manifest = load_json(root / "data/benchmarks/m8_benchmark_manifest.json")
    labels = load_json(root / "data/benchmarks/m8_ground_truth_labels.json")
    corruption = load_json(root / "data/benchmarks/m8_corruption_fixtures.json")
    human_selection = load_json(root / "data/benchmarks/m8_human_eval_selection.json")

    if config.get("network_egress") != "forbidden":
        raise ValueError("Frozen M8 evaluation must forbid network egress.")
    if manifest.get("status") != "frozen_inputs_no_m8_evaluation_output_exists":
        raise ValueError("Manifest must not misrepresent absent M8 results as present.")
    if config.get("candidate_pool", {}).get("candidate_count") != 24:
        raise ValueError("M8 benchmark candidate pool must contain the frozen 24 records.")
    if config["candidate_pool"].get("total_cap", 0) > 60:
        raise ValueError("M8 pool cannot exceed the M0 total retrieval cap.")
    if tuple(config.get("task_order", ())) != EXPECTED_TASK_ORDER:
        raise ValueError("M8 task order differs from the preregistered order.")

    corpus = manifest.get("corpus", [])
    dataset_ids = [item.get("dataset_id") for item in corpus]
    if len(corpus) != 24 or len(set(dataset_ids)) != 24:
        raise ValueError("Manifest corpus must contain exactly 24 unique datasets.")
    if [item.get("index") for item in corpus] != list(range(1, 25)):
        raise ValueError("Manifest corpus ordering must be contiguous and fixed.")
    tasks = manifest.get("tasks", [])
    task_names = [item.get("name") for item in tasks]
    if tuple(task_names) != EXPECTED_TASK_ORDER:
        raise ValueError("Manifest task ordering differs from the preregistered order.")

    if labels.get("independence_status") != "non_independent_not_external_ground_truth_not_calibrated_probability_labels":
        raise ValueError("Option C label framing has been weakened or changed.")
    if labels.get("dataset_order") != dataset_ids:
        raise ValueError("Reference-label dataset order must match the manifest.")
    if tuple(labels.get("tasks", {}).keys()) != EXPECTED_TASK_ORDER:
        raise ValueError("Reference labels must cover each frozen task once in order.")
    for task_name, task_labels in labels["tasks"].items():
        levels = task_labels.get("reference_levels", [])
        if len(levels) != 24 or any(level not in {0, 1, 2, 3} for level in levels):
            raise ValueError(f"Invalid reference levels for {task_name}.")
        binary = task_labels.get("binary_suitability", [])
        if binary != [int(level >= 2) for level in levels]:
            raise ValueError(f"Binary suitability cutoff mismatch for {task_name}.")
        if task_labels.get("task_id") != next(item["task_id"] for item in tasks if item["name"] == task_name):
            raise ValueError(f"Reference-label task identity mismatch for {task_name}.")

    fixture_ids = {
        dataset_id
        for suite in corruption.get("suites", [])
        for dataset_id in suite.get("target_dataset_ids", [])
    }
    if not fixture_ids or not fixture_ids.issubset(set(dataset_ids)):
        raise ValueError("Corruption fixtures must target only frozen manifest datasets.")
    if human_selection.get("status") != "selection_rule_frozen_stimulus_pairs_not_yet_generated":
        raise ValueError("Human selection artifact must not claim absent stimulus pairs exist.")
    selected_tasks = human_selection.get("selected_task_order", [])
    if selected_tasks != ["task_sentiment_binary", "task_tabular_titanic", "task_image_cifar"]:
        raise ValueError("Human-study task selection differs from the frozen deterministic rule.")

    for relative_path, expected_hash in manifest.get("artifact_hashes", {}).items():
        actual_hash = sha256_file(root / relative_path)
        if actual_hash != expected_hash:
            raise ValueError(f"Frozen artifact hash mismatch: {relative_path}")
    for relative_path, expected_hash in manifest.get("frozen_m7_archival_references", {}).items():
        if relative_path == "purpose":
            continue
        if sha256_file(root / relative_path) != expected_hash:
            raise ValueError(f"Frozen M7 reference hash mismatch: {relative_path}")

    return {"dataset_count": len(corpus), "task_count": len(tasks), "label_pair_count": len(corpus) * len(tasks)}
