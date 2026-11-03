# Dataset–task relevance judgment rubric

**Version: proposed 1.1.** Ratings are independent human judgments planned for Phase II; none have been collected. Examples below are explicitly hypothetical and are not benchmark rows or observed judgments. Apply the rubric to the frozen packet version supplied for the task–candidate pair.

## What is being judged

Judge whether the documented dataset, as represented by its frozen packet, is a defensible candidate for the stated task. Consider objective, primary input modality, target/label or structure, population/domain, scale, and explicit task requirements. Do not use rank, popularity, system score, or presumed downstream model performance. Do not infer unobserved content from a name alone.

Record separately:

1. **Relevance grade** (`0`–`3`) only when assessable.
2. **Assessability** (`assessable` or `unassessable`) and reason.
3. **Each registered mandatory-constraint state** (`satisfied`, `violated`, `unknown`, `unassessable`, or `not_applicable`) with evidence and source, plus an explicit applicability state.
4. Short reason codes, packet version, and source references.

Do not give a numeric confidence score. A license or policy field is a source claim, not legal advice. Relevance and mandatory-constraint eligibility are different judgments: a highly relevant dataset can violate a task constraint; an unknown constraint does not by itself make relevance zero.

## Operational relevance scale

Use the lowest grade that fits the documented evidence and task. A grade of 0 requires affirmative evidence of non-relevance or a decisive mismatch; missing documentation alone is unassessable, not grade 0. A grade of 1 requires some evidenced task/domain adjacency; uncertainty alone is not grade 1.

| Grade | Operational boundary |
|---:|---|
| **3 — Strong fit** | Direct evidence supports the primary modality, central objective, target/annotation structure, and requested population. Only ordinary preprocessing or a documented, mechanical label mapping is needed. No material scope or documentation caveat remains. |
| **2 — Plausible fit** | The central modality and task/target are supported, and a straightforward task-preserving mapping is documented, but a material caveat remains: limited population or domain coverage, partial target coverage, a nontrivial but bounded label mapping, or incomplete documentation on a noncentral detail. It remains a reasonable candidate without creating missing labels or redefining the task. |
| **1 — Weak/adjacent fit** | Some task-relevant content or adjacent domain is affirmatively documented, but a major input, target, population, or structure mismatch means substantial transformation, new annotation, proxy inference, or unsupported assumptions would be needed. It is only an exploratory adjacent candidate, not a direct task solution. |
| **0 — Not relevant or contradicted** | Available evidence affirmatively shows no meaningful task relation or a decisive mismatch that cannot be repaired while preserving the task—for example, the data are from an unrelated domain and lack the required input and target. Do not use 0 solely because a source is unavailable or an important property is unknown. |

### Boundary rules

- **Grade 0 vs. 1:** choose 1 only when evidence establishes meaningful adjacency or relevant content despite the mismatch. Choose 0 when evidence establishes no meaningful relation or a decisive incompatibility with no task-preserving adaptation. A modality mismatch is not automatically 0 or 1; inspect whether relevant target/content exists and what repair would require.
- **Grade 1 vs. 2:** if the candidate requires creating missing labels, extensive manual annotation, proxy-target inference, reconstructing the dataset structure, or redefining the objective, it cannot exceed 1. Grade 2 requires the central task and target to be present or supported by a documented straightforward mapping that preserves the objective.
- **Grade 2 vs. 3:** choose 2 when partial population/target coverage, a material caveat, or incomplete documentation remains. Choose 3 only when evidence supports the requested scope and only routine preprocessing or mechanical mapping remains.
- **Ordinary preprocessing:** cleaning documented malformed records, standard tokenization, deterministic resizing/rescaling, format conversion, or a transparent mapping between documented equivalent labels. It must not manufacture supervision or change the outcome of interest.
- **Substantial transformation:** creating labels, manual annotation, inferring a target from a proxy, discarding a material part of the requested population, or changing the task objective. Do not call these ordinary preprocessing.
- **Partial population coverage:** use 2 when the dataset provides a supported and useful subset of the requested population but does not establish the full requested scope. Use 1 if the subset is too narrow to address the principal task without major assumptions; use 0 only if evidence shows the requested population/task is absent.
- **Unknown mandatory constraint:** record `unknown` (and apply the frozen eligibility policy separately). Do not infer `violated` from missing documentation or lower the relevance grade merely because the constraint is unknown.

## Assessability and missing evidence

Mark `unassessable` when neither the frozen packet nor a permitted, logged source check supports a defensible relevance grade. Use reasons such as `source_unavailable`, `insufficient_task_or_target_documentation`, `conflicting_material_claims`, or `access_blocked`. If partial evidence does support a grade, assign that grade and record its limitations; do not replace uncertainty with zero.

If evidence shows that a required target is absent, that is negative evidence and may support grade 0 or 1 depending on documented adjacency. If the packet simply fails to say whether the target exists, use unassessable or a supported partial grade; do not treat silence as proof of absence. A failed request is a provenance/access failure, not a negative fact about the dataset.

## Mandatory constraints

Assess every explicit mandatory constraint independently:

- `satisfied`: evidence supports meeting the stated requirement;
- `violated`: evidence directly establishes a mismatch;
- `unknown`: the constraint applies, but evidence establishes neither outcome or contains unresolved conflict;
- `unassessable`: the constraint applies, but permitted evidence is insufficient to make a state judgment. Preserve this separately from `unknown`; both follow the preregistered unknown policy for eligibility;
- `not_applicable`: permitted evidence establishes that a preregistered conditional requirement does not apply to this candidate. This is not available for a task constraint registered as always applicable. Record the conditional rule and supporting applicability provenance. Do not use it to bypass a mandatory requirement.

Examples include required modality, target format, anonymous access, a stated license condition, or minimum sample scale. Keep conflicting source claims visible. `unknown` is not a confirmed violation; eligibility is derived separately under the task's predeclared policy. Do not turn a license claim into a legal conclusion.

## Hypothetical calibration examples

These examples are invented solely to clarify boundaries; they are not Phase I records, M8 candidates, calibration judgments, or benchmark labels.

| Hypothetical task and packet | Proposed judgment | Boundary rationale |
|---|---|---|
| Predict sentiment labels from customer-review text. Packet documents labeled reviews, the sentiment target, and broad population coverage; routine tokenization is needed. | **3 / assessable** | Direct input/target match; ordinary preprocessing only. |
| Predict sentiment labels from customer-review text. Packet documents labeled reviews, but only one language/region is covered while the task requests a broader population. | **2 / assessable** | Relevant supported subset, but material scope limitation. |
| Predict sentiment labels from customer-review text. Packet documents relevant review text but no labels; the target would require new human annotation. | **1 / assessable** | Relevant content exists, but substantial new labels are needed. |
| Predict sentiment labels from customer-review text. Packet confirms the candidate contains only unlabeled landscape photographs and no review or sentiment material. | **0 / assessable** | Evidence affirmatively establishes a decisive task/input mismatch. |
| Predict disease class from leaf photographs. Packet confirms leaf images and documented disease labels, but covers one crop while the task requests all major crops. | **2 / assessable** | Supported task and target for a limited population; not full scope. |
| Predict disease class from leaf photographs. Packet confirms relevant plant images but no disease labels or supported proxy; new annotation is required. | **1 / assessable** | Adjacent evidence, but target construction would be substantial. |
| Predict disease class from leaf photographs. The source is unavailable and the packet contains only a dataset title with no modality or target details. | **No grade / unassessable** | Missing evidence cannot establish either fit or mismatch. |
| Predict disease class from leaf photographs. Packet documents labeled leaf images, the full requested population, and the target; only routine resizing is needed, but the source does not state whether its license permits the task's explicitly required commercial use. | **3 / assessable; constraint `unknown`** | Relevance is directly supported; the separate license requirement remains unknown. |

Calibration sets must include cases that test these boundaries, including positive adjacency versus unrelated data, present labels versus missing labels, partial population coverage, missing documentation, and unknown mandatory constraints. Calibration composition and acceptance criteria are specified in [`INDEPENDENT_RELEVANCE_BENCHMARK.md`](INDEPENDENT_RELEVANCE_BENCHMARK.md). Do not create benchmark-like labels or add calibration cases to a benchmark split.

## Supplementary source checks and packet corrections

Assessors may consult only public sources listed in the frozen source registry. For each check, log the URI, source type, access/retrieval time, version or hash, exact supporting claim/observation, and reason, linked to the pair and pseudonymous assessor ID. Do not search for rankings, model outputs, or other assessor responses.

If a material packet omission or error is found, submit a packet-correction request without editing the first-pass judgment. A separate packet custodian verifies and versions the correction, then distributes the same corrected packet to both assessors without disclosing who raised it or any rating. Any future annotation records should represent each packet/rubric-specific round separately; original first-pass records are immutable, and revised ratings by the same two assessors are new records linked to the corrected round. Supersede only an unfinished round, record the correction reason and approved review, and select one current round per pair. A finalized pair cannot be silently reopened by a later packet correction; reopening requires a protocol amendment and is outside this proposed lifecycle. Adjudication resolves only the two first-pass judgments in the same current round. A pair may be finalized while other pairs remain in annotation. For held-out test pairs, the custodian must prevent any label or outcome feedback from reaching developers before authorized one-shot evaluation.

## Training, adjudication, and records

Calibration uses the separate nonbenchmark cases defined in the benchmark protocol. Record first-pass labels unchanged. For benchmark pairs, any grade disagreement, assessability disagreement, or applicable constraint-state disagreement triggers a separate third-adjudicator record. The adjudicator sees both rationales but remains blind to methods, ranks, scores, native gate decisions, and hypothesis direction. Preserve all original judgments and the final adjudication; do not overwrite, downgrade, or silently discard disagreements.

Record rubric version, task/pair/candidate IDs, packet version, pseudonymous assessor ID, assessability, grade or null, each applicable constraint state, reason codes, sources consulted, and the required provenance. Do not collect names or unnecessary personal data. Reliability summaries use the untouched first-pass labels and are reported separately from adjudicated values.
