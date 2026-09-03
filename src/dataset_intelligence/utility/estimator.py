"""TaskUtilityEstimator evaluating candidate datasets under Baselines A, B, and C."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from .components import (
    UtilityComponent,
    score_access_feasibility,
    score_governance_compatibility,
    score_modality_compatibility,
    score_quality_compatibility,
    score_structural_compatibility,
    score_target_compatibility,
    score_task_compatibility,
)
from .specification import TaskSpecification
from .uncertainty import StructuredUncertainty

ESTIMATE_VERSION = "1.0"
DEFAULT_WEIGHTS = {
    "task_compatibility": 1.0 / 7.0,
    "modality_compatibility": 1.0 / 7.0,
    "target_compatibility": 1.0 / 7.0,
    "structural_compatibility": 1.0 / 7.0,
    "quality_compatibility": 1.0 / 7.0,
    "governance_compatibility": 1.0 / 7.0,
    "access_feasibility": 1.0 / 7.0,
}


def compute_estimate_id(
    dataset_id: str,
    task_id: str,
    estimate_version: str,
    baseline_mode: str,
    components: dict[str, Any],
    composite_utility: float,
    hard_gated: bool,
) -> str:
    """Derive deterministic content-addressed identity from stable utility estimate fields."""
    comp_dict = {k: v.as_dict() if hasattr(v, "as_dict") else v for k, v in sorted(components.items())}
    payload = {
        "dataset_id": dataset_id,
        "task_id": task_id,
        "estimate_version": estimate_version,
        "baseline_mode": baseline_mode,
        "components": comp_dict,
        "composite_utility": round(composite_utility, 4),
        "hard_gated": hard_gated,
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "util_" + hashlib.sha256(canonical_bytes).hexdigest()[:24]


@dataclass(frozen=True)
class TaskUtilityEstimate:
    """Complete utility evaluation of a candidate dataset for a task specification."""

    estimate_id: str
    dataset_id: str
    task_id: str
    estimate_version: str
    baseline_mode: str
    components: dict[str, UtilityComponent]
    composite_utility: float
    hard_gated: bool
    gating_reason: str | None
    uncertainty: StructuredUncertainty
    provenance: dict[str, Any]

    def validate(self) -> None:
        if not self.estimate_id:
            raise ValueError("estimate_id cannot be blank.")
        if not self.dataset_id:
            raise ValueError("dataset_id cannot be blank.")
        if not self.task_id:
            raise ValueError("task_id cannot be blank.")
        if self.estimate_version != ESTIMATE_VERSION:
            raise ValueError(f"Unsupported estimate version: {self.estimate_version}")
        if not (0.0 <= self.composite_utility <= 1.0):
            raise ValueError(f"Composite utility must be in [0.0, 1.0], got {self.composite_utility}")
        if self.hard_gated and self.composite_utility != 0.0:
            raise ValueError("Hard-gated utility estimate must have composite_utility == 0.0")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "estimate_id": self.estimate_id,
            "dataset_id": self.dataset_id,
            "task_id": self.task_id,
            "estimate_version": self.estimate_version,
            "baseline_mode": self.baseline_mode,
            "components": {k: v.as_dict() for k, v in self.components.items()},
            "composite_utility": self.composite_utility,
            "hard_gated": self.hard_gated,
            "gating_reason": self.gating_reason,
            "uncertainty": self.uncertainty.as_dict(),
            "provenance": self.provenance,
        }


class TaskUtilityEstimator:
    """Evaluator computing TaskUtilityEstimates across Baselines A, B, and C."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        total_w = sum(self.weights.values())
        if abs(total_w - 1.0) > 1e-4:
            # Normalize to 1.0
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def check_hard_gates(
        self,
        record: Any,
        task_spec: TaskSpecification,
        m3_entries: list[Any] | None = None,
        fingerprint: Any = None,
    ) -> tuple[bool, str | None]:
        """Check if dataset violates an explicitly stated, verifiable hard constraint."""
        # 1. Modality Clash: Task explicitly requires image, and dataset is confirmed tabular-only with zero images
        req_mod = task_spec.primary_modality.lower()
        if req_mod != "unknown":
            raw_mod = record.semantics.get("modality", []) if hasattr(record, "semantics") else []
            ds_mods = set(str(m).lower() for m in (raw_mod if isinstance(raw_mod, (list, tuple)) else [raw_mod]))
            if fingerprint:
                fp_mod = getattr(fingerprint, "primary_modality", None)
                if fp_mod and fp_mod not in {"unsupported", "failed", "unknown"}:
                    ds_mods.add(fp_mod.lower())

            if ds_mods and req_mod not in ds_mods and "multimodal" not in ds_mods and "unknown" not in ds_mods:
                return True, f"Hard modality mismatch: task requires {req_mod}, dataset is confirmed {sorted(ds_mods)}."

        # 2. Prohibited License
        gov = task_spec.governance_constraints
        prohibited = [p.lower() for p in gov.get("prohibited_licenses", ())]
        if prohibited:
            raw_lic = str(record.governance.get("license_claim", "")).lower() if hasattr(record, "governance") else ""
            if raw_lic and any(p in raw_lic for p in prohibited):
                return True, f"Hard governance violation: dataset license ({raw_lic}) is prohibited ({prohibited})."

        # 3. Mandatory Public Access on Confirmed Gated Source
        acc = task_spec.access_constraints
        if acc.get("public_access_required"):
            source = record.identity.get("source_name", "") if hasattr(record, "identity") else ""
            if source == "kaggle" and not acc.get("allow_gated", False):
                return True, "Hard access violation: task requires public anonymous access, but source requires credentials."

        return False, None

    def evaluate(
        self,
        record: Any,
        task_spec: TaskSpecification,
        m3_entries: list[Any] | None = None,
        fingerprint: Any = None,
        baseline_mode: str = "baseline_c",
        evaluated_at: str = "2026-09-02T00:00:00+00:00",
        config_hash: str | None = None,
    ) -> TaskUtilityEstimate:
        """Evaluate candidate dataset against task specification."""
        dataset_id = record.internal_id if hasattr(record, "internal_id") else str(record.get("internal_id", ""))

        # Check hard gates
        is_gated, gating_reason = self.check_hard_gates(
            record=record,
            task_spec=task_spec,
            m3_entries=m3_entries if baseline_mode != "baseline_a" else None,
            fingerprint=fingerprint if baseline_mode == "baseline_c" else None,
        )

        # Evaluate individual components
        c_task = score_task_compatibility(record, task_spec, m3_entries, fingerprint, baseline_mode)
        c_mod = score_modality_compatibility(record, task_spec, m3_entries, fingerprint, baseline_mode)
        c_target = score_target_compatibility(record, task_spec, m3_entries, fingerprint, baseline_mode)
        c_struct = score_structural_compatibility(record, task_spec, m3_entries, fingerprint, baseline_mode)
        c_qual = score_quality_compatibility(record, task_spec, m3_entries, fingerprint, baseline_mode)
        c_gov = score_governance_compatibility(record, task_spec, m3_entries, fingerprint, baseline_mode)
        c_acc = score_access_feasibility(record, task_spec, m3_entries, fingerprint, baseline_mode)

        components = {
            "task_compatibility": c_task,
            "modality_compatibility": c_mod,
            "target_compatibility": c_target,
            "structural_compatibility": c_struct,
            "quality_compatibility": c_qual,
            "governance_compatibility": c_gov,
            "access_feasibility": c_acc,
        }

        # Calculate composite utility (Equal-weight linear baseline)
        if is_gated:
            composite_utility = 0.0
        else:
            raw_sum = sum(self.weights.get(k, 1.0 / 7.0) * comp.score for k, comp in components.items())
            composite_utility = round(max(0.0, min(1.0, raw_sum)), 4)

        uncertainty = StructuredUncertainty.from_components(list(components.values()))

        est_id = compute_estimate_id(
            dataset_id=dataset_id,
            task_id=task_spec.task_id,
            estimate_version=ESTIMATE_VERSION,
            baseline_mode=baseline_mode,
            components=components,
            composite_utility=composite_utility,
            hard_gated=is_gated,
        )

        provenance = {
            "evaluated_at": evaluated_at,
            "baseline_mode": baseline_mode,
            "weight_model": "equal_weight_linear_baseline",
            "weights_used": self.weights,
            "config_hash": config_hash,
        }

        estimate = TaskUtilityEstimate(
            estimate_id=est_id,
            dataset_id=dataset_id,
            task_id=task_spec.task_id,
            estimate_version=ESTIMATE_VERSION,
            baseline_mode=baseline_mode,
            components=components,
            composite_utility=composite_utility,
            hard_gated=is_gated,
            gating_reason=gating_reason,
            uncertainty=uncertainty,
            provenance=provenance,
        )
        estimate.validate()
        return estimate
