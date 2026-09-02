"""Structured, validation-friendly records for the M0 experiment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


FAILURE_CATEGORIES = frozenset({
    "authentication_or_gating", "unavailable_endpoint", "incompatible_format",
    "rate_limit", "timeout", "policy_refusal", "unknown",
})
CACHE_STATES = frozenset({"cold", "warm", "not_applicable"})
RUN_CONDITIONS = frozenset({"cold", "warm"})
PHASES = frozenset({"candidate_retrieval", "evidence_collection", "sample_acquisition", "diagnostic"})


@dataclass(frozen=True)
class MeasurementRecord:
    """One observable M0 operation; unknown values are represented as null."""

    run_id: str
    condition: str
    phase: str
    source: str
    started_at: str
    duration_ms: float
    peak_rss_bytes: int
    cache_state: str
    success: bool
    dataset_id: str | None = None
    dataset_url: str | None = None
    query_id: str | None = None
    acquisition_method: str | None = None
    records_acquired: int | None = None
    bytes_acquired: int = 0
    network_requests: int = 0
    status_code: int | None = None
    failure_category: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.phase not in PHASES:
            raise ValueError(f"Unsupported phase: {self.phase}")
        if self.condition not in RUN_CONDITIONS:
            raise ValueError(f"Unsupported run condition: {self.condition}")
        if self.cache_state not in CACHE_STATES:
            raise ValueError(f"Unsupported cache state: {self.cache_state}")
        if self.failure_category and self.failure_category not in FAILURE_CATEGORIES:
            raise ValueError(f"Unsupported failure category: {self.failure_category}")
        if self.success and self.failure_category:
            raise ValueError("Successful records cannot have a failure category.")
        if not self.success and not self.failure_category:
            raise ValueError("Unsuccessful records must include a failure category.")
        if self.duration_ms < 0 or self.peak_rss_bytes < 0 or self.bytes_acquired < 0 or self.network_requests < 0:
            raise ValueError("Measurement values cannot be negative.")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
