"""Evidence foundation: immutable ledger, bounded probing, and provisional resolution."""

from .croissant import extract_croissant_claims
from .harvester import EvidenceHarvester
from .ledger import EvidenceLedger, LedgerEntry, compute_entry_id
from .probes import compute_sample_diagnostics, probe_bounded_sample
from .resolver import ClaimResolution, ProvisionalResolver, compute_resolution_id
from .statuses import (
    CROISSANT_STATUSES,
    EVIDENCE_TYPES,
    OBSERVATION_STATES,
    RESOLUTION_STATES,
)

__all__ = [
    "CROISSANT_STATUSES",
    "ClaimResolution",
    "EVIDENCE_TYPES",
    "EvidenceHarvester",
    "EvidenceLedger",
    "LedgerEntry",
    "OBSERVATION_STATES",
    "ProvisionalResolver",
    "RESOLUTION_STATES",
    "compute_entry_id",
    "compute_resolution_id",
    "compute_sample_diagnostics",
    "extract_croissant_claims",
    "probe_bounded_sample",
]
