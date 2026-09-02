# Canonical Dataset Schema (v1.0)

M1 serializes one inspectable JSON object per dataset. The record is source-independent, but it never discards source evidence. Every normalized material field can retain one or more `claims`, each with value, source URL, source field, observation time, and state. M1 creates only `single_source_claim` states; it performs no evidence resolution.

## Groups

- `identity`: source name/ID, name, canonical URL, version, family ID, and unresolved lineage.
- `semantics`: description, task, domain, modality, learning type, target, label type, tags, intended use.
- `structure`: counts, schema summary, formats, splits, and feature information.
- `governance`: license claim, policy, creators, citation, documentation, provenance and Croissant URL.
- `community_context`: downloads, stars, ratings, citations, updates and activity.
- `access`: capability-derived access information, policy status, cache status, observation time and response reference.
- `observed_content`: explicit null placeholders for later sample measurements and probes.
- `risk_uncertainty`: risk flags, missing fields, unresolved mappings and access limitations.

`internal_id` is a stable SHA-256-derived ID over source name, source dataset ID, and version. It does not merge same-named datasets across repositories. `dataset_family_id` and lineage remain null/unresolved unless a source explicitly supplies them; M1 does not infer mirrors or derivation.

Unknown is represented as `null` or an explicit unresolved/missing list. A license claim is not a compatibility conclusion, and a count claim is not an observed measurement.
