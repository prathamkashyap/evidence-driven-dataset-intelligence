#!/usr/bin/env python3
"""Tests for Milestone 8 Google Forms generation and specification integrity."""

import json
from pathlib import Path
import subprocess
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_session_manifest.json"
PROTOCOL_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_protocol.md"
INSTRUMENT_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_human_eval_instrument.md"
JS_PATH = REPO_ROOT / "scripts" / "create_m8_google_forms.js"
SPEC_PATH = REPO_ROOT / "data" / "benchmarks" / "m8_google_forms_specification.md"


class TestM8GoogleForms(unittest.TestCase):
    """Verify integrity of M8 Google Forms artifacts and generation."""

    def test_generated_files_exist(self) -> None:
        self.assertTrue(JS_PATH.exists(), f"Missing {JS_PATH}")
        self.assertTrue(SPEC_PATH.exists(), f"Missing {SPEC_PATH}")

    def test_javascript_syntax_valid(self) -> None:
        """Ensure create_m8_google_forms.js passes node syntax check."""
        res = subprocess.run(
            ["node", "-c", str(JS_PATH)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"JS syntax check failed:\n{res.stderr}")

    def test_specification_contains_required_sections(self) -> None:
        spec_text = SPEC_PATH.read_text(encoding="utf-8")
        self.assertIn("Milestone 8 Human Evaluation: Google Forms Specification", spec_text)
        self.assertIn("Pre-Committed Presentation Schedule Matrix", spec_text)
        self.assertIn("Detailed Comparison Stimuli (All 7 Sections)", spec_text)
        self.assertIn("Response Ingestion & Transcription Procedure", spec_text)
        self.assertIn("scripts/capture_m8_human_eval_response.py", spec_text)

        # Check that all 7 comparisons are described in spec
        for i in range(1, 8):
            self.assertIn(f"Comparison {i} of 7", spec_text)
            self.assertIn(f"`comp_{i}`", spec_text)

    def test_verbatim_instrument_wording_preserved(self) -> None:
        spec_text = SPEC_PATH.read_text(encoding="utf-8")
        js_text = JS_PATH.read_text(encoding="utf-8")

        trust_wording = (
            "I trust that this card provides a reliable, credible, and verifiable representation "
            "of the dataset's characteristics and suitability for the task."
        )
        understanding_wording = (
            "I understand why this dataset was surfaced and how it connects to the specific "
            "technical requirements of the task."
        )
        actionability_wording = (
            "This card provides sufficient and relevant information for me to make an informed "
            "decision on whether to adopt, further inspect, or reject this dataset for the task."
        )

        for wording in (trust_wording, understanding_wording, actionability_wording):
            self.assertIn(wording, spec_text)
            self.assertIn(wording, js_text)

    def test_presentation_schedule_fidelity(self) -> None:
        """Verify the presentation order across raters strictly matches the manifest."""
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        spec_text = SPEC_PATH.read_text(encoding="utf-8")

        for comp in manifest["comparisons"]:
            cid = comp["comparison_id"]
            orders = comp["presentation_order"]
            self.assertIn(f"`{cid}`", spec_text)
            for rater_id, order in orders.items():
                expected_format = "Format B" if order == "B_first" else "Format A"
                # Check rater presentation schedule mentions
                self.assertIn(f"`{rater_id}`: `{order}`", spec_text)


if __name__ == "__main__":
    unittest.main()
