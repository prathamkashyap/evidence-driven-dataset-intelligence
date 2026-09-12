"""Offline validation tests for the frozen M8 benchmark definition."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evaluation.benchmark_inputs import validate_frozen_benchmark_inputs


class M8BenchmarkInputTests(unittest.TestCase):
    def test_frozen_input_contract(self) -> None:
        self.assertEqual(
            validate_frozen_benchmark_inputs(ROOT),
            {"dataset_count": 24, "task_count": 8, "label_pair_count": 192},
        )

    def test_label_matrix_has_only_declared_reference_levels(self) -> None:
        labels = json.loads((ROOT / "data/benchmarks/m8_ground_truth_labels.json").read_text())
        self.assertIn("non_independent", labels["independence_status"])
        for values in labels["tasks"].values():
            self.assertEqual(len(values["reference_levels"]), 24)
            self.assertTrue(all(level in {0, 1, 2, 3} for level in values["reference_levels"]))

    def test_manifest_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = json.loads((ROOT / "data/benchmarks/m8_benchmark_manifest.json").read_text())
            required_paths = [
                "configs/m8_evaluation.json", "data/benchmarks/m8_benchmark_manifest.json",
                "data/benchmarks/m8_ground_truth_labels.json", "data/benchmarks/m8_corruption_fixtures.json",
                "data/benchmarks/m8_human_eval_selection.json",
                *manifest["artifact_hashes"].keys(),
                *(key for key in manifest["frozen_m7_archival_references"] if key != "purpose"),
            ]
            for relative in set(required_paths):
                source = ROOT / relative
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            labels = root / "data/benchmarks/m8_ground_truth_labels.json"
            labels.write_text(labels.read_text() + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_frozen_benchmark_inputs(root)


if __name__ == "__main__":
    unittest.main()
