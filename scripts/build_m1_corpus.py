#!/usr/bin/env python3
"""Build the deterministic M1 canonical development corpus from public fixtures."""
from __future__ import annotations
import json, sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dataset_intelligence.ingestion.adapters import ADAPTERS  # noqa: E402

def main() -> int:
    config = json.loads((ROOT / "configs" / "m1_ingestion.json").read_text())
    fixtures = json.loads((ROOT / config["fixture_corpus"]).read_text())
    observed_at = "2026-09-02T00:00:00+00:00"
    records = [ADAPTERS[item["source"]]().normalize(item["raw"], observed_at).as_dict() for item in fixtures]
    output = ROOT / config["output_corpus"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records))
    print(f"Wrote {len(records)} canonical records to {output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
