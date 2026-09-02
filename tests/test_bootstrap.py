"""Checks for M0 bootstrap structure and configuration only."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_bootstrap.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_bootstrap", VALIDATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BootstrapValidationTests(unittest.TestCase):
    def test_bootstrap_configuration_is_valid(self) -> None:
        self.assertEqual(load_validator().validate(), [])

    def test_m0_does_not_add_runtime_dependencies(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("dependencies = []", pyproject)


if __name__ == "__main__":
    unittest.main()
