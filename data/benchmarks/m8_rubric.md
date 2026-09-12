# M8 Reference-Level Rubric — Option C Consistency Audit

This rubric is the project-author reference-label procedure used solely for the
**M7 Pipeline Consistency Audit**. It reuses the M5 development-rubric family and is
therefore non-independent. It is not external ground truth, independent annotation,
legal clearance, a downstream task result, or a calibrated-probability target.

The annotation unit is one `(dataset, task)` pair in the frozen M8 manifest. Assessments
use only the committed canonical record, its linked evidence/fingerprint artifacts, and the
committed task specification. They do not use a future M8 rank, score, recommendation card,
or benchmark result.

| Level | Interpretation |
|---:|---|
| 3 | Task, modality, target structure, and material constraints directly match. |
| 2 | Task and modality match, with a secondary target, feature, governance, or access limitation. |
| 1 | Broad modality/task relation exists, but a material domain, target, or structural mismatch remains. |
| 0 | Confirmed modality incompatibility or a hard access/governance incompatibility under the task constraints. |

For the audit-only binary representation, `y = 1` when the reference level is at least 2;
otherwise `y = 0`. Brier score and ECE, if later computed, are descriptive internal
consistency diagnostics only. They must never be reported as independent calibration or
external validation.
