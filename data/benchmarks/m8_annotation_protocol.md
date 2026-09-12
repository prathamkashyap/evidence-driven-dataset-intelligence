# M8 Project-Author Reference-Label Procedure

## Scope and status

This artifact documents the project-author reference-label procedure used solely for the
**M7 Pipeline Consistency Audit** under Option C. It is explicitly **not** an independent
ground-truth annotation protocol. No independent annotator, inter-annotator agreement,
external validation, or calibrated-probability claim is implied.

Before the M8 offline evaluation harness is run, the author records one Reference Level for
each pair in the frozen 24-record corpus and eight frozen task specifications. The resulting
matrix is `m8_ground_truth_labels.json`; its name is retained only because the frozen M8
protocol specifies that path. Its contents are non-independent reference labels.

## Procedure

1. Use the fixed dataset and task order in `m8_benchmark_manifest.json`.
2. Consult only the frozen canonical record, linked M3 evidence, M4 fingerprint, and task
   specification. Do not consult a future M8 rank, candidate score, recommendation set, or
   recommendation card.
3. Apply the four-level rubric in `m8_rubric.md`.
4. Encode `y = 1` for levels 2–3 and `y = 0` for levels 0–1.
5. Treat unknown, unsupported, failed, and conflicting states as explicit evidence states;
   do not fabricate a favorable observation.

The later M7 Pipeline Consistency Audit may compare scores with this matrix only as a
descriptive consistency check. It cannot establish independent ground truth, probability
calibration, legal suitability, or downstream model performance.
