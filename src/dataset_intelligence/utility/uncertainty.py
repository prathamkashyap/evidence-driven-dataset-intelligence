"""Categorical epistemic states and structured uncertainty representation.

Excludes arbitrary numerical confidence probabilities and uncertainty mass,
preserving exact qualitative reasons for uncertainty.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

EPISTEMIC_STATES = frozenset({
    "known_favorable",
    "known_unfavorable",
    "unknown",
    "unsupported",
    "failed",
    "conflicting",
    "sample_limited_inference",
})

EVIDENCE_BASES = frozenset({
    "direct_observation",
    "publisher_claim",
    "corroborated_observation",
    "bounded_sample",
    "unstated",
})


@dataclass(frozen=True)
class StructuredUncertainty:
    """Non-numerical structured uncertainty profile across evaluated dimensions."""

    uncertainty_states: tuple[str, ...]
    uncertainty_reasons: tuple[str, ...]
    is_sample_limited: bool
    has_unsupported_evidence: bool
    has_failed_evidence: bool
    has_conflicting_evidence: bool

    @classmethod
    def from_components(
        cls,
        components: list[Any] | tuple[Any, ...],
    ) -> StructuredUncertainty:
        states: set[str] = set()
        reasons: list[str] = []
        sample_limited = False
        unsupported = False
        failed = False
        conflicting = False

        for comp in components:
            state = getattr(comp, "epistemic_state", "unknown")
            states.add(state)
            name = getattr(comp, "component_name", "unknown_component")
            explanation = getattr(comp, "explanation", "")

            if state == "sample_limited_inference":
                sample_limited = True
                reasons.append(f"{name}: inference derived from bounded sample slice.")
            elif state == "unsupported":
                unsupported = True
                reasons.append(f"{name}: operational access unsupported under current policy.")
            elif state == "failed":
                failed = True
                reasons.append(f"{name}: operational access failed.")
            elif state == "conflicting":
                conflicting = True
                reasons.append(f"{name}: conflicting evidence observed.")
            elif state == "unknown":
                reasons.append(f"{name}: property unstated in metadata and unobserved in sample.")

        return cls(
            uncertainty_states=tuple(sorted(states)),
            uncertainty_reasons=tuple(sorted(reasons)),
            is_sample_limited=sample_limited,
            has_unsupported_evidence=unsupported,
            has_failed_evidence=failed,
            has_conflicting_evidence=conflicting,
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
