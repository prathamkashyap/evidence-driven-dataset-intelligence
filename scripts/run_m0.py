#!/usr/bin/env python3
"""Run M0's bounded public-access measurement experiment."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.m0.runner import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset-cache", action="store_true", help="Clear only experiments/m0/cache before the cold run.")
    args = parser.parse_args()
    result_dir = run(ROOT / "configs" / "m0_compute_budget.json", reset_cache=args.reset_cache)
    print(f"M0 complete. Structured records: {result_dir / 'records.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
