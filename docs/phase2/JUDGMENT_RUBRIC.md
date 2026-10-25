# Dataset–task relevance judgment rubric

**Version: proposed 1.0.** Ratings are independent human judgments planned for Phase II; none have been collected. The hypothetical examples below teach the rubric and are not benchmark rows or observed judgments.

## What is being judged

Judge whether the documented dataset, as frozen in its source packet, is a defensible candidate for the stated task. Consider task objective, input modality, target/label or structure, population/domain, scale and explicit requirements. Judge relevance from cited dataset/task evidence, not from rank, popularity, presumed model performance, or the Phase I utility score. Do not infer unseen contents from a name alone.

Record three separate outputs:

1. **Relevance grade** (`0`–`3`) when enough evidence exists.
2. **Assessability** (`assessable` or `unassessable`) and reason. Unassessable is missing evidence, not a relevance grade.
3. **Mandatory-constraint state** for each task constraint (`satisfied`, `violated`, `unknown`, `not_applicable`) with evidence and source.

Also record a short reason code and source references. Do not provide a numeric confidence rating; uncertainty is captured through assessability, constraint, and evidence fields.

## Ordinal relevance scale

| Grade | Operational definition |
|---:|---|
| **3 — Strong fit** | Direct documentation or bounded, permitted observation supports the requested modality and central task/target. The dataset can plausibly be used for the stated task with ordinary preprocessing; no material mismatch is found. |
| **2 — Plausible fit** | The central task and modality align, but a material caveat remains (for example, target/label mapping needs work, documentation is incomplete, or the dataset covers only part of the requested population). It remains a reasonable candidate for further inspection. |
| **1 — Weak/adjacent fit** | There is some domain or concept overlap, but a major task, target, modality, population, or structural mismatch means substantial transformation or unsupported assumptions would be needed. Do not award 1 for uncertainty alone. |
| **0 — Not relevant or contradicted** | Available evidence shows that the dataset does not address the task or has a decisive task/modality/target mismatch. Use only when evidence supports a negative relevance judgment, not merely because documentation is missing. |

The scale is ordinal. Do not interpret a one-grade difference as a fixed amount of utility. nDCG uses prespecified graded gains only as a ranking metric.

## Assessability and evidence state

Choose `unassessable` if neither the frozen packet nor a permitted, logged source check supports a defensible grade. Select a reason such as `source_unavailable`, `insufficient_task_or_target_documentation`, `conflicting_material_claims`, or `access_blocked`. Keep any known conflict or access failure in provenance. If partial evidence supports a judgment, assign the grade and mark the limiting evidence in the rationale; do not replace uncertainty with a zero.

## Mandatory constraints

Assess each explicit constraint independently of relevance:

- `satisfied`: evidence supports meeting the stated requirement;
- `violated`: evidence directly establishes a mismatch;
- `unknown`: evidence does not establish either outcome or contains unresolved conflict;
- `not_applicable`: the task has no such requirement.

Examples include a required modality, a required target format, anonymous access, a specific license condition, or an explicit minimum sample scale. A publisher license field is a source claim, not legal advice. Assessors record what the source says and whether it meets the task's stated condition; they do not make a legal determination.

## Hypothetical training examples

These are invented, generic rubric examples only. They are not records from M8 or Phase II.

| Hypothetical task and source packet | Grade / state | Why |
|---|---|---|
| “Classify plant disease from leaf photographs”; dataset documentation explicitly describes labeled leaf images and the same disease target. | 3 / assessable | Direct task, modality, and target alignment. |
| Same task; packet confirms plant images and disease labels, but covers only one crop and does not establish the requested multi-crop scope. | 2 / assessable | Core task fits, with a material population limitation. |
| Same task; packet mentions plant health but describes only tabular soil chemistry and no image or disease target. | 1 / assessable | Domain adjacency, but major input/target mismatch. |
| Same task; documentation explicitly states the records are unlabeled landscape photographs. | 0 / assessable | Available evidence contradicts the required input/target combination. |
| Same task; source and documentation are unavailable and the only evidence is the dataset name “Plant Health.” | no grade / unassessable | Missing evidence cannot support either a positive or negative relevance claim. |

## Reasons and source recording

Use concise codes where applicable: `task_match`, `modality_match`, `target_match`, `domain_match`, `scale_match`, `partial_scope`, `target_mismatch`, `modality_mismatch`, `task_mismatch`, `insufficient_documentation`, `source_conflict`, `access_failure`, `mandatory_constraint_violation`, `mandatory_constraint_unknown`. A free-text note may add context but cannot substitute for a source reference. Record source URI, source type, retrieval time, snapshot/hash where available, and the exact claim or bounded observation supporting the judgment.

## Training and adjudication

Train assessors on hypothetical cases and a separate, non-benchmark calibration set. The calibration set must not contain M8 candidates or any final train/development/test candidate. Agree the interpretation of grade boundaries before the benchmark annotations begin; version and hash the rubric and packet template. During annotation, preserve first-pass labels. Identical first-pass relevance grades are retained; any disagreement is adjudicated. The adjudicator follows the trigger rules in the benchmark protocol, records a final grade/state and reason, and does not erase disagreements.
