"""Immutable, content-addressed evidence ledger and entries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .statuses import EVIDENCE_TYPES, OBSERVATION_STATES


def compute_entry_id(
    dataset_id: str,
    claim_type: str,
    evidence_type: str,
    source: str,
    source_field: str,
    claim_value: Any,
    procedure: str,
    sample_scope: dict[str, Any] | None = None,
    adapter_version: str = "1.0",
    raw_reference: str | None = None,
    source_url: str | None = None,
) -> str:
    """Derive deterministic content-addressed identity from stable evidence payload fields.

    observed_at is intentionally excluded so that replayed or re-observed identical
    evidence generates the exact same entry ID regardless of runtime clock.
    """
    payload = {
        "dataset_id": dataset_id,
        "claim_type": claim_type,
        "evidence_type": evidence_type,
        "source": source,
        "source_field": source_field,
        "claim_value": claim_value,
        "procedure": procedure,
        "sample_scope": sample_scope or {},
        "adapter_version": adapter_version,
        "raw_reference": raw_reference or "",
        "source_url": source_url or "",
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "ev_" + hashlib.sha256(canonical_bytes).hexdigest()[:24]


@dataclass(frozen=True)
class LedgerEntry:
    """An immutable, content-addressed evidence observation record."""

    entry_id: str
    dataset_id: str
    claim_type: str
    claim_value: Any
    evidence_type: str
    source: str
    source_field: str
    observation_state: str
    procedure: str
    adapter_version: str
    observed_at: str
    sample_scope: dict[str, Any] = field(default_factory=dict)
    source_url: str | None = None
    raw_reference: str | None = None

    @classmethod
    def create(
        cls,
        *,
        dataset_id: str,
        claim_type: str,
        claim_value: Any,
        evidence_type: str,
        source: str,
        source_field: str,
        observation_state: str,
        procedure: str,
        observed_at: str,
        adapter_version: str = "1.0",
        sample_scope: dict[str, Any] | None = None,
        source_url: str | None = None,
        raw_reference: str | None = None,
    ) -> LedgerEntry:
        scope = sample_scope or {}
        entry_id = compute_entry_id(
            dataset_id=dataset_id,
            claim_type=claim_type,
            evidence_type=evidence_type,
            source=source,
            source_field=source_field,
            claim_value=claim_value,
            procedure=procedure,
            sample_scope=scope,
            adapter_version=adapter_version,
            raw_reference=raw_reference,
            source_url=source_url,
        )
        entry = cls(
            entry_id=entry_id,
            dataset_id=dataset_id,
            claim_type=claim_type,
            claim_value=claim_value,
            evidence_type=evidence_type,
            source=source,
            source_field=source_field,
            observation_state=observation_state,
            procedure=procedure,
            adapter_version=adapter_version,
            observed_at=observed_at,
            sample_scope=scope,
            source_url=source_url,
            raw_reference=raw_reference,
        )
        entry.validate()
        return entry

    def validate(self) -> None:
        if not self.entry_id:
            raise ValueError("entry_id cannot be blank.")
        expected_id = compute_entry_id(
            dataset_id=self.dataset_id,
            claim_type=self.claim_type,
            evidence_type=self.evidence_type,
            source=self.source,
            source_field=self.source_field,
            claim_value=self.claim_value,
            procedure=self.procedure,
            sample_scope=self.sample_scope,
            adapter_version=self.adapter_version,
            raw_reference=self.raw_reference,
            source_url=self.source_url,
        )
        if self.entry_id != expected_id:
            raise ValueError(f"entry_id mismatch: expected {expected_id}, got {self.entry_id}")
        if self.observation_state not in OBSERVATION_STATES:
            raise ValueError(f"Unsupported observation state: {self.observation_state}")
        if self.evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"Unsupported evidence type: {self.evidence_type}")
        if not self.dataset_id or not self.claim_type or not self.source:
            raise ValueError("dataset_id, claim_type, and source cannot be blank.")
        if not self.observed_at:
            raise ValueError("observed_at timestamp is mandatory for provenance.")
        if not self.adapter_version:
            raise ValueError("adapter_version is mandatory.")
        for k, v in self.sample_scope.items():
            if isinstance(v, (int, float)) and v < 0:
                raise ValueError(f"Sample scope field '{k}' cannot be negative: {v}")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class EvidenceLedger:
    """An append-only repository of immutable LedgerEntry records."""

    def __init__(self, entries: list[LedgerEntry] | None = None) -> None:
        self._entries: list[LedgerEntry] = []
        self._by_id: dict[str, LedgerEntry] = {}
        if entries:
            for entry in entries:
                self.add_entry(entry)

    def add_entry(self, entry: LedgerEntry) -> None:
        entry.validate()
        if entry.entry_id in self._by_id:
            # Idempotent re-addition of identical evidence assertion
            return
        self._entries.append(entry)
        self._by_id[entry.entry_id] = entry

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def get_entries_for_dataset(self, dataset_id: str) -> list[LedgerEntry]:
        return [e for e in self._entries if e.dataset_id == dataset_id]

    def get_claims(self, dataset_id: str, claim_type: str) -> list[LedgerEntry]:
        return [e for e in self._entries if e.dataset_id == dataset_id and e.claim_type == claim_type]

    def export_jsonl(self, path: Path | str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(entry.as_dict(), sort_keys=True) + "\n" for entry in self._entries]
        target.write_text("".join(lines), encoding="utf-8")

    @classmethod
    def from_jsonl(cls, path: Path | str) -> EvidenceLedger:
        target = Path(path)
        if not target.is_file():
            return cls([])
        entries = []
        for line in target.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            entry = LedgerEntry(**data)
            entry.validate()
            entries.append(entry)
        return cls(entries)

    def summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_state: dict[str, int] = {}
        by_source: dict[str, int] = {}
        dataset_ids: set[str] = set()

        for entry in self._entries:
            by_type[entry.evidence_type] = by_type.get(entry.evidence_type, 0) + 1
            by_state[entry.observation_state] = by_state.get(entry.observation_state, 0) + 1
            by_source[entry.source] = by_source.get(entry.source, 0) + 1
            dataset_ids.add(entry.dataset_id)

        return {
            "total_entries": len(self._entries),
            "unique_datasets": len(dataset_ids),
            "by_evidence_type": dict(sorted(by_type.items())),
            "by_observation_state": dict(sorted(by_state.items())),
            "by_source": dict(sorted(by_source.items())),
        }
