#!/usr/bin/env python3
"""Validate M8 benchmark inputs without generating recommendations or contacting sources."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evaluation.benchmark_inputs import validate_frozen_benchmark_inputs


if __name__ == "__main__":
    print(json.dumps(validate_frozen_benchmark_inputs(ROOT), sort_keys=True))
