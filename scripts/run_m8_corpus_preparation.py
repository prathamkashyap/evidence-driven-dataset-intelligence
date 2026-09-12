#!/usr/bin/env python3
"""Run the one-time, logged M8 corpus acquisition/preparation plan.

This is not the frozen offline M8 benchmark. It may use only the fixed public endpoints
in ``configs/m8_corpus_preparation.json`` and caches every permitted response.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset_intelligence.evaluation.preparation import load_config, prepare_corpus


def main() -> int:
    config = load_config(ROOT / "configs" / "m8_corpus_preparation.json")
    summary = prepare_corpus(ROOT, config)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
