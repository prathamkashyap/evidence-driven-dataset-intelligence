"""Offline tests for the bounded M8 corpus-preparation client."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evaluation.preparation import EXPECTED_TARGET_IDS, load_config, parse_arff_rows, parse_hf_rows


class M8PreparationTests(unittest.TestCase):
    def test_fixed_config_target_order_and_m0_bounds(self) -> None:
        config = load_config(ROOT / "configs" / "m8_corpus_preparation.json")
        self.assertEqual(tuple(item["id"] for item in config["targets"]), EXPECTED_TARGET_IDS)
        self.assertEqual(config["sample_limits"]["max_records"], 32)
        self.assertEqual(config["sample_limits"]["hard_cap_bytes"], 64 * 1024 * 1024)

    def test_config_rejects_target_reordering(self) -> None:
        config = json.loads((ROOT / "configs" / "m8_corpus_preparation.json").read_text())
        config["targets"][0], config["targets"][1] = config["targets"][1], config["targets"][0]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                load_config(path)

    def test_bounded_local_parsers(self) -> None:
        arff = b"@RELATION demo\n@ATTRIBUTE a NUMERIC\n@ATTRIBUTE class {yes,no}\n@DATA\n1,yes\n2,no\n"
        self.assertEqual(parse_arff_rows(arff, max_records=1), [{"a": 1, "class": "yes"}])
        rows = json.dumps({"rows": [{"row": {"text": "a", "label": 0}}, {"row": {"text": "b", "label": 1}}]}).encode()
        self.assertEqual(parse_hf_rows(rows, max_records=1), [{"text": "a", "label": 0}])

    def test_prepared_benchmark_artifact_contract(self) -> None:
        """The acquisition output must be complete without consulting a live source."""
        def load(relative: str) -> list[dict]:
            return [json.loads(line) for line in (ROOT / relative).read_text().splitlines() if line.strip()]

        corpus = load("experiments/m8/corpus/benchmark_corpus.jsonl")
        ledger = load("experiments/m8/evidence/benchmark_evidence_ledger.jsonl")
        fingerprints = load("experiments/m8/fingerprints/benchmark_fingerprints.jsonl")
        estimates = load("experiments/m8/utility/benchmark_utility_estimates.jsonl")
        dataset_ids = {record["internal_id"] for record in corpus}

        self.assertEqual(len(corpus), 24)
        self.assertEqual({entry["dataset_id"] for entry in ledger}, dataset_ids)
        self.assertEqual({item["dataset_id"] for item in fingerprints}, dataset_ids)
        self.assertEqual({item["dataset_id"] for item in estimates}, dataset_ids)
        self.assertEqual(len(estimates), len(corpus) * 8)
        self.assertTrue(all(item["baseline_mode"] == "baseline_c" for item in estimates))
        exclusions = (ROOT / "data/benchmarks/m8_corpus_exclusions.md").read_text()
        self.assertIn("kaggle_heart_disease_uci", exclusions)


if __name__ == "__main__":
    unittest.main()
