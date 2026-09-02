# M1 Source Adapter Contract

Each adapter isolates native payloads from the canonical schema. It exposes discovery and metadata endpoint declarations, `normalize`, `identify`, `capability_report`, and `access_policy`. Normalizers receive a raw snapshot plus `observed_at`, emit a versioned canonical record, and preserve a raw-response reference in provenance. Future network acquisition must cache allowed source responses in `data/raw`; fixture-based M1 builds do not issue network requests.

| Source | Discovery | Metadata | Sample access in M1 | M0-informed limitation |
|---|---|---|---|---|
| Hugging Face | Public API search | Public dataset endpoint | Conditional Viewer rows | Viewer availability can fail; M0 saw Beans HTTP 502. |
| OpenML | Public catalog snapshot | Public REST dataset endpoint | Conditional metadata-linked bounded stream | No quality/utility inference. |
| UCI | Not implemented | Controlled seed/catalog landing URL | Conditional public bounded flat-file route | No documented programmatic discovery endpoint was established in M0. |
| Kaggle | Public metadata search | Public metadata endpoint | `unsupported_or_policy_limited` | Metadata-only without credentials; no download workaround. |

Capabilities are operational metadata, not rank signals. M1 does not call sources during unit tests. The committed development corpus is generated from sanitized public-response fixtures, while later live snapshot fetching must retain source URL, observation time, adapter version, cache state, and request/response identifiers without credentials, tokens, cookies, or private headers.
