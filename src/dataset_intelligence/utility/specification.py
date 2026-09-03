"""Structured, versioned specification of user task requirements."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any

SPECIFICATION_VERSION = "1.0"
SUPPORTED_TASK_TYPES = frozenset({
    "classification", "regression", "clustering", "detection", "unknown"
})
SUPPORTED_MODALITIES = frozenset({
    "text", "tabular", "image", "multimodal", "unknown"
})


def compute_task_id(
    specification_version: str,
    task_type: str,
    primary_modality: str,
    domain: str | None,
    target_requirements: dict[str, Any],
    input_constraints: dict[str, Any],
    scale_constraints: dict[str, Any],
    governance_constraints: dict[str, Any],
    access_constraints: dict[str, Any],
    explicit_user_constraints: dict[str, Any],
    unresolved_requirements: tuple[str, ...] | list[str],
) -> str:
    """Derive deterministic content-addressed identity from stable task specification fields."""
    payload = {
        "specification_version": specification_version,
        "task_type": task_type,
        "primary_modality": primary_modality,
        "domain": domain,
        "target_requirements": target_requirements,
        "input_constraints": input_constraints,
        "scale_constraints": scale_constraints,
        "governance_constraints": governance_constraints,
        "access_constraints": access_constraints,
        "explicit_user_constraints": explicit_user_constraints,
        "unresolved_requirements": sorted(unresolved_requirements),
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "task_" + hashlib.sha256(canonical_bytes).hexdigest()[:24]


@dataclass(frozen=True)
class TaskSpecification:
    """Structured, versioned specification of user task requirements."""

    task_id: str
    specification_version: str
    task_type: str
    primary_modality: str
    domain: str | None
    target_requirements: dict[str, Any]
    input_constraints: dict[str, Any]
    scale_constraints: dict[str, Any]
    governance_constraints: dict[str, Any]
    access_constraints: dict[str, Any]
    explicit_user_constraints: dict[str, Any]
    unresolved_requirements: tuple[str, ...]
    raw_query: str | None

    @classmethod
    def create(
        cls,
        *,
        task_type: str = "unknown",
        primary_modality: str = "unknown",
        domain: str | None = None,
        target_requirements: dict[str, Any] | None = None,
        input_constraints: dict[str, Any] | None = None,
        scale_constraints: dict[str, Any] | None = None,
        governance_constraints: dict[str, Any] | None = None,
        access_constraints: dict[str, Any] | None = None,
        explicit_user_constraints: dict[str, Any] | None = None,
        unresolved_requirements: tuple[str, ...] | list[str] | None = None,
        raw_query: str | None = None,
        specification_version: str = SPECIFICATION_VERSION,
    ) -> TaskSpecification:
        targets = target_requirements or {}
        inputs = input_constraints or {}
        scale = scale_constraints or {}
        gov = governance_constraints or {}
        acc = access_constraints or {}
        user_c = explicit_user_constraints or {}
        unresolved = tuple(sorted(unresolved_requirements or ()))

        tid = compute_task_id(
            specification_version=specification_version,
            task_type=task_type,
            primary_modality=primary_modality,
            domain=domain,
            target_requirements=targets,
            input_constraints=inputs,
            scale_constraints=scale,
            governance_constraints=gov,
            access_constraints=acc,
            explicit_user_constraints=user_c,
            unresolved_requirements=unresolved,
        )

        spec = cls(
            task_id=tid,
            specification_version=specification_version,
            task_type=task_type,
            primary_modality=primary_modality,
            domain=domain,
            target_requirements=targets,
            input_constraints=inputs,
            scale_constraints=scale,
            governance_constraints=gov,
            access_constraints=acc,
            explicit_user_constraints=user_c,
            unresolved_requirements=unresolved,
            raw_query=raw_query,
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if not self.task_id:
            raise ValueError("task_id cannot be blank.")
        if self.specification_version != SPECIFICATION_VERSION:
            raise ValueError(f"Unsupported specification version: {self.specification_version}")
        if self.task_type not in SUPPORTED_TASK_TYPES:
            raise ValueError(f"Unsupported task type: {self.task_type}")
        if self.primary_modality not in SUPPORTED_MODALITIES:
            raise ValueError(f"Unsupported primary modality: {self.primary_modality}")

        expected_id = compute_task_id(
            specification_version=self.specification_version,
            task_type=self.task_type,
            primary_modality=self.primary_modality,
            domain=self.domain,
            target_requirements=self.target_requirements,
            input_constraints=self.input_constraints,
            scale_constraints=self.scale_constraints,
            governance_constraints=self.governance_constraints,
            access_constraints=self.access_constraints,
            explicit_user_constraints=self.explicit_user_constraints,
            unresolved_requirements=self.unresolved_requirements,
        )
        if self.task_id != expected_id:
            raise ValueError(f"task_id mismatch: expected {expected_id}, got {self.task_id}")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
