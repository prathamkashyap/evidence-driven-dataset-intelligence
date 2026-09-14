#!/usr/bin/env python3
"""Run Milestone 8 offline frozen benchmark evaluation harness.

Operates strictly as a read-only client of frozen M0-M7 modules and frozen M8 inputs.
Zero network egress.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evaluation.benchmark_inputs import validate_frozen_benchmark_inputs
from dataset_intelligence.evaluation.harness import M8EvaluationHarness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run M8 offline benchmark evaluation.")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate frozen benchmark inputs without executing evaluation.",
    )
    parser.add_argument(
        "--write-results",
        action="store_true",
        help="Execute evaluation and write results to experiments/m8/results.",
    )
    args = parser.parse_args()

    # 1. Always validate inputs first
    counts = validate_frozen_benchmark_inputs(ROOT)
    print(f"Frozen M8 inputs validated: {counts['dataset_count']} datasets, {counts['task_count']} tasks, {counts['label_pair_count']} labels.")

    if args.check_only:
        print("Check-only mode complete. No evaluation executed.")
        return 0

    if not args.write_results:
        print("Dry run complete. Use --write-results to run evaluation and write artifacts.")
        return 0

    # 2. Execute evaluation harness in memory
    print("Executing M8 evaluation harness...")
    harness = M8EvaluationHarness(ROOT)
    results = harness.evaluate_all()

    # 3. Write results to output directory
    config = harness.config
    out_dir = ROOT / config.get("output_directory", "experiments/m8/results")
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "m8_summary.json"
    summary_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"M8 evaluation summary written to: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
