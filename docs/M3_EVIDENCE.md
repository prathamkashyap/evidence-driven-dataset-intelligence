# Milestone 3 — Evidence System Specification

## 1. Overview and Purpose

Milestone 3 establishes the evidence foundation for the dataset recommendation pipeline. It transitions the system from **candidate retrieval** (M2) to **systematic evidence acquisition and tracking**.

M3 answers:
> *"For each retrieved candidate, what evidence do we actually have, where did it come from, when was it observed, what does it claim or measure, and what remains unknown or contradictory?"*

M3 does **not** decide which dataset is best or rank candidates.

## 2. Core Epistemic Principles

1. **Evidence over assertion:** Source claims are recorded as claims, not ground truth facts.
2. **Immutability of evidence:** Once a `LedgerEntry` is recorded, it is never modified. Later agreement or conflict is captured in a separate resolution layer.
3. **Traceable provenance:** Every observation preserves source identity, adapter version, observation timestamp, native field origin, and raw reference pointer.
4. **Unknown as a first-class state:** Missing evidence is modeled explicitly and is never treated as neutral positive evidence or silently filled with defaults.
5. **Operational isolation:** `failed` and `unsupported` access are distinct states. They are recorded as operational realities, never converted into negative quality evidence.
6. **Bounded inspection:** Content probing adheres strictly to M0 empirical limits (max 32 records, 64 MiB hard cap). Full downloads are strictly barred.
7. **Non-numerical resolution:** The provisional resolver identifies categorical agreement (`corroborated`), disagreement (`conflicting`), single-source assertions (`unresolved`), and absence (`unknown`) without computing confidence scores, belief masses, or weights.
8. **No legal claims:** Governance claims (licenses) are recorded as publisher statements, not verified legal clearance.

## 3. Evidence Data Model

Evidence entries belong to five distinct categories:

- `metadata_claim`: Normalized publisher metadata (e.g. `dataset_name`, `description`, `task`, `modality`, `sample_count`, `class_count`, `license`, `version_id`).
- `documentation_claim`: Semi-structured documentation references (dataset card links, README references, citation strings).
- `croissant_claim`: Standards-aligned Croissant JSON-LD claims (distributions, recordSets, declared license).
- `access_probe`: Operational capability and policy status observations derived from source adapters.
- `content_observation`: Empirical diagnostics derived from bounded sample inspection (rows observed, column names/types, null rate, duplicate rate, sample hash).

## 4. Observation States vs. Resolution States

To guarantee ledger immutability, individual observation states are strictly separated from cross-evidence resolution states:

### Observation States (`LedgerEntry.observation_state`)
Describes an individual observation at harvest time:
- `observed`: Directly measured or verified through bounded probing or parser execution.
- `single_source_claim`: Asserted by a publisher/metadata endpoint without direct independent verification.
- `unsupported`: Path/operation is formally disallowed by adapter capability or platform policy.
- `failed`: Supported operation was attempted but failed operationally (e.g. HTTP 502, network timeout).
- `unknown`: Expected property was unstated or absent in the source.

### Resolution States (`ClaimResolution.resolution_state`)
Describes the relationship between multiple entries for a single `(dataset_id, claim_type)`:
- `corroborated`: Two or more independent observations assert equivalent values.
- `conflicting`: Two or more observations assert incompatible/divergent values.
- `unresolved`: Exactly one substantive observation exists; uncorroborated.
- `unknown`: No observations exist or all observations failed/are unknown.

## 5. Deterministic Identity and Replay

Evidence entry IDs are content-addressed:
```python
entry_id = "ev_" + sha256(canonical_json({
    dataset_id, claim_type, evidence_type, source, source_field,
    claim_value, procedure, sample_scope, adapter_version,
    raw_reference, source_url
}))[:24]
```

`observed_at` is excluded from the hash so that re-running identical fixtures or replays produces identical entry IDs across environments. Separate observation runs are tracked via run manifests and summary records, preserving exact temporal provenance without contaminating content identity.

## 6. Croissant Standard Integration

Croissant metadata extraction is optional and non-fatal, recognizing four explicit situations:
- `available_and_parsed`: Croissant JSON-LD present, fetched, and parsed.
- `referenced_but_unavailable`: A `croissant_url` was declared, but resource was unreachable.
- `absent`: No Croissant URL was declared (`croissant_url: null`).
- `parse_failed`: Resource exists but contains malformed JSON-LD syntax.

The parser uses the standard Python `json` library, requiring no heavy external dependencies.

## 7. Bounded Content Probes

Content inspection reuses M0 limits:
- Maximum 32 records
- Soft target: 1 MiB
- Hard cap: 64 MiB
- Capabilities:
  - Hugging Face: public Dataset Viewer `/rows` endpoint (JSON rows).
  - OpenML: public ARFF stream (first 32 data records).
  - UCI: public flat-file stream (first 32 non-empty lines).
  - Kaggle: unsupported under M0 policy (requires credentials).
- Diagnostics extracted:
  - `records_observed`: $\le 32$
  - `column_names`: list of observed features
  - `column_types`: dominant data types
  - `null_rate`: cell missingness in sample
  - `duplicate_rate`: exact row duplicates in 32-record slice
  - `sample_sha256`: content hash

## 8. Explicit Non-Goals for M3

M3 explicitly does NOT implement:
- Dempster–Shafer belief/plausibility combination
- Numerical evidence scoring or confidence weights
- Downstream task probes or linear/logistic utility estimates
- Cleanlab confident learning or label noise estimation
- Popularity adjustments or long-tail exploration
- Diversified recommendation set selection
- Final candidate ranking or recommendation cards
