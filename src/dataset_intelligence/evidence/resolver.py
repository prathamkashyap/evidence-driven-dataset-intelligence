"""Non-numerical provisional evidence resolver."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from .ledger import EvidenceLedger, LedgerEntry
from .statuses import RESOLUTION_STATES


def compute_resolution_id(dataset_id: str, claim_type: str, evidence_entry_ids: tuple[str, ...]) -> str:
    payload = {
        "dataset_id": dataset_id,
        "claim_type": claim_type,
        "evidence_entry_ids": sorted(evidence_entry_ids),
    }
    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "res_" + hashlib.sha256(canonical_bytes).hexdigest()[:24]


def _canonical_comparable_value(val: Any) -> str:
    """Serialize value to canonical form for deterministic equality comparison."""
    if isinstance(val, str):
        return val.strip().lower()
    if isinstance(val, (list, tuple, set)):
        items = [_canonical_comparable_value(x) for x in val]
        return json.dumps(sorted(items), separators=(",", ":"))
    if isinstance(val, dict):
        return json.dumps({str(k).lower(): _canonical_comparable_value(v) for k, v in sorted(val.items())}, separators=(",", ":"))
    return json.dumps(val, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ClaimResolution:
    """Non-numerical synthesis of multiple evidence entries for a single claim type."""

    resolution_id: str
    dataset_id: str
    claim_type: str
    resolution_state: str
    evidence_entry_ids: tuple[str, ...]
    corroborating_entry_ids: tuple[str, ...]
    conflicting_entry_ids: tuple[str, ...]
    resolved_value: Any | None
    explanation: str

    def validate(self) -> None:
        if self.resolution_state not in RESOLUTION_STATES:
            raise ValueError(f"Unsupported resolution state: {self.resolution_state}")
        expected_id = compute_resolution_id(self.dataset_id, self.claim_type, self.evidence_entry_ids)
        if self.resolution_id != expected_id:
            raise ValueError(f"resolution_id mismatch: expected {expected_id}, got {self.resolution_id}")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class ProvisionalResolver:
    """Synthesizes discrete immutable evidence entries into agreement/conflict states."""

    def resolve_claim(
        self,
        dataset_id: str,
        claim_type: str,
        entries: list[LedgerEntry],
    ) -> ClaimResolution:
        all_ids = tuple(sorted(e.entry_id for e in entries))

        # Filter out operational failures or pure unknowns when evaluating value agreement
        substantive_entries = [
            e for e in entries if e.observation_state not in {"failed", "unknown"} and e.claim_value is not None
        ]

        if not substantive_entries:
            # Check if all entries were explicitly failed or unknown
            res_id = compute_resolution_id(dataset_id, claim_type, all_ids)
            explanation = "No substantive observations available for this claim."
            if any(e.observation_state == "failed" for e in entries):
                explanation = "All observations for this claim encountered operational failures."
            elif any(e.observation_state == "unsupported" for e in entries):
                explanation = "Claim property is unsupported by source capabilities."

            res = ClaimResolution(
                resolution_id=res_id,
                dataset_id=dataset_id,
                claim_type=claim_type,
                resolution_state="unknown",
                evidence_entry_ids=all_ids,
                corroborating_entry_ids=(),
                conflicting_entry_ids=(),
                resolved_value=None,
                explanation=explanation,
            )
            res.validate()
            return res

        if len(substantive_entries) == 1:
            single = substantive_entries[0]
            res_id = compute_resolution_id(dataset_id, claim_type, all_ids)
            res = ClaimResolution(
                resolution_id=res_id,
                dataset_id=dataset_id,
                claim_type=claim_type,
                resolution_state="unresolved",
                evidence_entry_ids=all_ids,
                corroborating_entry_ids=(),
                conflicting_entry_ids=(),
                resolved_value=single.claim_value,
                explanation=f"Single source observation ({single.source}: {single.evidence_type}); uncorroborated.",
            )
            res.validate()
            return res

        # Multiple substantive observations: check for value agreement vs divergence
        groups: dict[str, list[LedgerEntry]] = {}
        for entry in substantive_entries:
            key = _canonical_comparable_value(entry.claim_value)
            groups.setdefault(key, []).append(entry)

        res_id = compute_resolution_id(dataset_id, claim_type, all_ids)

        if len(groups) == 1:
            # All observations agree
            agreeing_ids = tuple(sorted(e.entry_id for e in substantive_entries))
            res = ClaimResolution(
                resolution_id=res_id,
                dataset_id=dataset_id,
                claim_type=claim_type,
                resolution_state="corroborated",
                evidence_entry_ids=all_ids,
                corroborating_entry_ids=agreeing_ids,
                conflicting_entry_ids=(),
                resolved_value=substantive_entries[0].claim_value,
                explanation=f"Corroborated across {len(agreeing_ids)} distinct observations.",
            )
            res.validate()
            return res

        # Conflicting observations present
        conflicting_ids = tuple(sorted(e.entry_id for e in substantive_entries))
        divergent_summaries = [f"{e.source}({e.claim_value!r})" for e in substantive_entries]
        res = ClaimResolution(
            resolution_id=res_id,
            dataset_id=dataset_id,
            claim_type=claim_type,
            resolution_state="conflicting",
            evidence_entry_ids=all_ids,
            corroborating_entry_ids=(),
            conflicting_entry_ids=conflicting_ids,
            resolved_value=None,
            explanation="Conflicting claims observed: " + "; ".join(divergent_summaries),
        )
        res.validate()
        return res

    def resolve_dataset(self, dataset_id: str, ledger: EvidenceLedger) -> list[ClaimResolution]:
        entries = ledger.get_entries_for_dataset(dataset_id)
        claim_types = sorted({e.claim_type for e in entries})
        resolutions = []
        for ctype in claim_types:
            c_entries = [e for e in entries if e.claim_type == ctype]
            resolutions.append(self.resolve_claim(dataset_id, ctype, c_entries))
        return resolutions

    def resolve_ledger(self, ledger: EvidenceLedger) -> dict[str, list[ClaimResolution]]:
        datasets = sorted({e.dataset_id for e in ledger})
        return {did: self.resolve_dataset(did, ledger) for did in datasets}

    def summary(self, resolutions: dict[str, list[ClaimResolution]]) -> dict[str, Any]:
        counts: dict[str, int] = {}
        total = 0
        for d_resolutions in resolutions.values():
            for r in d_resolutions:
                total += 1
                counts[r.resolution_state] = counts.get(r.resolution_state, 0) + 1

        return {
            "total_resolutions": total,
            "by_resolution_state": dict(sorted(counts.items())),
        }
