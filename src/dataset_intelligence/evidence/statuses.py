"""Observation states, resolution states, and evidence categories for M3."""

from __future__ import annotations

# Observation-level states describing an individual evidence observation
OBSERVATION_STATES = frozenset({
    "observed",              # Directly measured or verified through bounded probing/parsing
    "single_source_claim",   # Asserted by a publisher/card without independent verification
    "unsupported",           # Operation/path is formally unsupported by policy/capability
    "failed",                # Supported operation encountered an operational/network failure
    "unknown",               # Expected property was unstated, missing, or unobserved
})

# Cross-evidence resolution states describing agreement/disagreement across observations
RESOLUTION_STATES = frozenset({
    "unresolved",            # Single source claim or inconclusive evidence without corroboration/conflict
    "corroborated",          # Multiple independent sources agree, or claim matches direct observation
    "conflicting",           # Two or more observations assert incompatible/contradictory values
    "unknown",               # No evidence exists or all observations are unknown/failed
})

# Croissant metadata availability and extraction statuses
CROISSANT_STATUSES = frozenset({
    "available_and_parsed",       # Croissant JSON-LD present, fetched, and parsed into claims
    "referenced_but_unavailable",  # croissant_url present but fetch/resource unavailable
    "absent",                     # Record has no Croissant metadata referenced (croissant_url is null)
    "parse_failed",               # Croissant JSON-LD was fetched/provided but parsing failed
})

# Categories of evidence tracked in the ledger
EVIDENCE_TYPES = frozenset({
    "metadata_claim",        # Standard repository/publisher metadata fields
    "documentation_claim",   # Dataset card, README, intended use, limitations
    "croissant_claim",       # Standards-aligned Croissant JSON-LD claims
    "access_probe",          # Operational reachability, policy, and capability observations
    "content_observation",   # Bounded sample diagnostics (rows, columns, nulls, duplicates)
})
