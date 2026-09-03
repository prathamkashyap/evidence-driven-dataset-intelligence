"""Seven interpretable utility component evaluators implementing baseline compatibility mappings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .specification import TaskSpecification
from .uncertainty import EPISTEMIC_STATES, EVIDENCE_BASES


@dataclass(frozen=True)
class UtilityComponent:
    """Individual task-compatibility evaluation for a specific dimension."""

    component_name: str
    score: float
    epistemic_state: str
    evidence_basis: str
    explanation: str
    source_evidence_ids: tuple[str, ...]
    fingerprint_ids: tuple[str, ...]
    task_spec_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Score must be in [0.0, 1.0], got {self.score}")
        if self.epistemic_state not in EPISTEMIC_STATES:
            raise ValueError(f"Invalid epistemic state: {self.epistemic_state}")
        if self.evidence_basis not in EVIDENCE_BASES:
            raise ValueError(f"Invalid evidence basis: {self.evidence_basis}")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_task_compatibility(
    record: Any,
    task_spec: TaskSpecification,
    m3_entries: list[Any] | None = None,
    fingerprint: Any = None,
    baseline_mode: str = "baseline_c",
) -> UtilityComponent:
    """Evaluate alignment between dataset stated/observed task and task specification."""
    task_claims = []
    evidence_ids: list[str] = []
    if m3_entries and baseline_mode in {"baseline_b", "baseline_c"}:
        for e in m3_entries:
            if getattr(e, "claim_type", "") == "task":
                task_claims.append(getattr(e, "claim_value", None))
                evidence_ids.append(getattr(e, "entry_id", ""))

    raw_task = record.semantics.get("task") if hasattr(record, "semantics") else None
    dataset_tasks = set()
    if isinstance(raw_task, (list, tuple)):
        dataset_tasks.update(str(t).lower() for t in raw_task)
    elif raw_task:
        dataset_tasks.add(str(raw_task).lower())

    for tc in task_claims:
        if isinstance(tc, (list, tuple)):
            dataset_tasks.update(str(t).lower() for t in tc)
        elif tc:
            dataset_tasks.add(str(tc).lower())

    target_task = task_spec.task_type.lower()
    if target_task == "unknown":
        return UtilityComponent(
            component_name="task_compatibility",
            score=0.5,
            epistemic_state="unknown",
            evidence_basis="unstated",
            explanation="Task requirement unstated in task specification.",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=(),
            task_spec_fields=("task_type",),
        )

    if not dataset_tasks:
        return UtilityComponent(
            component_name="task_compatibility",
            score=0.5,
            epistemic_state="unknown",
            evidence_basis="unstated",
            explanation="Dataset task unstated in publisher metadata.",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=(),
            task_spec_fields=("task_type",),
        )

    # Check match
    if any(target_task in dt or dt in target_task for dt in dataset_tasks):
        return UtilityComponent(
            component_name="task_compatibility",
            score=1.0,
            epistemic_state="known_favorable",
            evidence_basis="corroborated_observation" if len(evidence_ids) > 1 else "publisher_claim",
            explanation=f"Dataset task ({sorted(dataset_tasks)}) matches requested task ({target_task}).",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=(),
            task_spec_fields=("task_type",),
        )

    # Related task check (e.g. classification vs text-classification)
    if any("classif" in dt and "classif" in target_task for dt in dataset_tasks):
        return UtilityComponent(
            component_name="task_compatibility",
            score=1.0,
            epistemic_state="known_favorable",
            evidence_basis="publisher_claim",
            explanation=f"Dataset classification task aligns with requested {target_task}.",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=(),
            task_spec_fields=("task_type",),
        )

    return UtilityComponent(
        component_name="task_compatibility",
        score=0.0,
        epistemic_state="known_unfavorable",
        evidence_basis="publisher_claim",
        explanation=f"Dataset task ({sorted(dataset_tasks)}) conflicts with requested task ({target_task}).",
        source_evidence_ids=tuple(evidence_ids),
        fingerprint_ids=(),
        task_spec_fields=("task_type",),
    )


def score_modality_compatibility(
    record: Any,
    task_spec: TaskSpecification,
    m3_entries: list[Any] | None = None,
    fingerprint: Any = None,
    baseline_mode: str = "baseline_c",
) -> UtilityComponent:
    """Evaluate modality alignment between dataset and task specification."""
    req_mod = task_spec.primary_modality.lower()
    if req_mod == "unknown":
        return UtilityComponent(
            component_name="modality_compatibility",
            score=0.5,
            epistemic_state="unknown",
            evidence_basis="unstated",
            explanation="Modality unstated in task specification.",
            source_evidence_ids=(),
            fingerprint_ids=(),
            task_spec_fields=("primary_modality",),
        )

    fp_id = ()
    fp_mod = None
    if fingerprint and baseline_mode == "baseline_c":
        fp_mod = getattr(fingerprint, "primary_modality", None)
        fp_id = (getattr(fingerprint, "fingerprint_id", ""),)

    raw_mod = record.semantics.get("modality") if hasattr(record, "semantics") else None
    ds_mods = set()
    if isinstance(raw_mod, (list, tuple)):
        ds_mods.update(str(m).lower() for m in raw_mod)
    elif raw_mod:
        ds_mods.add(str(raw_mod).lower())

    if fp_mod and fp_mod not in {"unsupported", "failed", "unknown"}:
        ds_mods.add(fp_mod.lower())

    if not ds_mods:
        return UtilityComponent(
            component_name="modality_compatibility",
            score=0.5,
            epistemic_state="unknown",
            evidence_basis="unstated",
            explanation="Dataset modality unstated.",
            source_evidence_ids=(),
            fingerprint_ids=fp_id,
            task_spec_fields=("primary_modality",),
        )

    if req_mod in ds_mods:
        return UtilityComponent(
            component_name="modality_compatibility",
            score=1.0,
            epistemic_state="known_favorable",
            evidence_basis="direct_observation" if fp_mod == req_mod else "publisher_claim",
            explanation=f"Dataset modality ({sorted(ds_mods)}) matches requested modality ({req_mod}).",
            source_evidence_ids=(),
            fingerprint_ids=fp_id,
            task_spec_fields=("primary_modality",),
        )

    return UtilityComponent(
        component_name="modality_compatibility",
        score=0.0,
        epistemic_state="known_unfavorable",
        evidence_basis="publisher_claim",
        explanation=f"Dataset modality ({sorted(ds_mods)}) conflicts with requested modality ({req_mod}).",
        source_evidence_ids=(),
        fingerprint_ids=fp_id,
        task_spec_fields=("primary_modality",),
    )


def score_target_compatibility(
    record: Any,
    task_spec: TaskSpecification,
    m3_entries: list[Any] | None = None,
    fingerprint: Any = None,
    baseline_mode: str = "baseline_c",
) -> UtilityComponent:
    """Evaluate target / label compatibility with explicit slice-bias awareness."""
    target_req = task_spec.target_requirements
    expected_classes = target_req.get("expected_classes")
    expected_type = target_req.get("target_type")

    if not expected_classes and not expected_type:
        return UtilityComponent(
            component_name="target_compatibility",
            score=1.0,
            epistemic_state="known_favorable",
            evidence_basis="unstated",
            explanation="No specific target or class constraints specified in task.",
            source_evidence_ids=(),
            fingerprint_ids=(),
            task_spec_fields=("target_requirements",),
        )

    fp_id = ()
    sample_classes = None
    if fingerprint and baseline_mode == "baseline_c":
        fp_id = (getattr(fingerprint, "fingerprint_id", ""),)
        target_diag = getattr(fingerprint, "target_diagnostics", {})
        sample_classes = target_diag.get("observed_sample_class_count")

    # Check slice bias rule: if sample observes 1 class on contiguous slice, but task expects 2
    if sample_classes == 1 and expected_classes == 2:
        return UtilityComponent(
            component_name="target_compatibility",
            score=0.8,
            epistemic_state="sample_limited_inference",
            evidence_basis="bounded_sample",
            explanation="Bounded sample observed 1 class across contiguous slice; consistent with slice bias on sorted binary split.",
            source_evidence_ids=(),
            fingerprint_ids=fp_id,
            task_spec_fields=("target_requirements",),
        )

    if sample_classes and expected_classes:
        if sample_classes == expected_classes:
            return UtilityComponent(
                component_name="target_compatibility",
                score=1.0,
                epistemic_state="known_favorable",
                evidence_basis="direct_observation",
                explanation=f"Sample observed classes ({sample_classes}) match expected classes ({expected_classes}).",
                source_evidence_ids=(),
                fingerprint_ids=fp_id,
                task_spec_fields=("target_requirements",),
            )
        else:
            return UtilityComponent(
                component_name="target_compatibility",
                score=0.5,
                epistemic_state="sample_limited_inference",
                evidence_basis="bounded_sample",
                explanation=f"Sample observed {sample_classes} classes, expected {expected_classes}; bounded sample may be incomplete.",
                source_evidence_ids=(),
                fingerprint_ids=fp_id,
                task_spec_fields=("target_requirements",),
            )

    # In Baseline A/B without fingerprint, trust metadata if classification matches
    return UtilityComponent(
        component_name="target_compatibility",
        score=0.7,
        epistemic_state="unknown",
        evidence_basis="publisher_claim",
        explanation="Target class count unobserved in sample; evaluated from metadata description.",
        source_evidence_ids=(),
        fingerprint_ids=(),
        task_spec_fields=("target_requirements",),
    )


def score_structural_compatibility(
    record: Any,
    task_spec: TaskSpecification,
    m3_entries: list[Any] | None = None,
    fingerprint: Any = None,
    baseline_mode: str = "baseline_c",
) -> UtilityComponent:
    """Evaluate feature count, text token length, or image dimensions against constraints."""
    in_constraints = task_spec.input_constraints
    if not in_constraints:
        return UtilityComponent(
            component_name="structural_compatibility",
            score=1.0,
            epistemic_state="known_favorable",
            evidence_basis="unstated",
            explanation="No structural or input constraints specified in task.",
            source_evidence_ids=(),
            fingerprint_ids=(),
            task_spec_fields=("input_constraints",),
        )

    fp_id = ()
    if fingerprint and baseline_mode == "baseline_c":
        fp_id = (getattr(fingerprint, "fingerprint_id", ""),)
        modality = getattr(fingerprint, "primary_modality", "")
        details = getattr(fingerprint, "modality_details", {})

        if modality == "text" and "max_tokens" in in_constraints:
            word_dist = details.get("word_count_distribution", {})
            max_words = word_dist.get("max", 0)
            req_max = in_constraints["max_tokens"]
            if max_words <= req_max:
                return UtilityComponent(
                    component_name="structural_compatibility",
                    score=1.0,
                    epistemic_state="known_favorable",
                    evidence_basis="direct_observation",
                    explanation=f"Observed sample max word count ({max_words}) fits within requested limit ({req_max}).",
                    source_evidence_ids=(),
                    fingerprint_ids=fp_id,
                    task_spec_fields=("input_constraints",),
                )
            else:
                return UtilityComponent(
                    component_name="structural_compatibility",
                    score=0.5,
                    epistemic_state="known_unfavorable",
                    evidence_basis="direct_observation",
                    explanation=f"Observed sample max words ({max_words}) exceeds limit ({req_max}).",
                    source_evidence_ids=(),
                    fingerprint_ids=fp_id,
                    task_spec_fields=("input_constraints",),
                )

        if modality == "tabular" and "min_features" in in_constraints:
            col_count = details.get("observed_sample_column_count", 0)
            req_cols = in_constraints["min_features"]
            if col_count >= req_cols:
                return UtilityComponent(
                    component_name="structural_compatibility",
                    score=1.0,
                    epistemic_state="known_favorable",
                    evidence_basis="direct_observation",
                    explanation=f"Observed column count ({col_count}) satisfies requirement (>= {req_cols}).",
                    source_evidence_ids=(),
                    fingerprint_ids=fp_id,
                    task_spec_fields=("input_constraints",),
                )
            else:
                return UtilityComponent(
                    component_name="structural_compatibility",
                    score=0.3,
                    epistemic_state="known_unfavorable",
                    evidence_basis="direct_observation",
                    explanation=f"Observed column count ({col_count}) below requirement ({req_cols}).",
                    source_evidence_ids=(),
                    fingerprint_ids=fp_id,
                    task_spec_fields=("input_constraints",),
                )

    return UtilityComponent(
        component_name="structural_compatibility",
        score=0.7,
        epistemic_state="unknown",
        evidence_basis="publisher_claim",
        explanation="Structural constraints evaluated against metadata claims without empirical fingerprint.",
        source_evidence_ids=(),
        fingerprint_ids=(),
        task_spec_fields=("input_constraints",),
    )


def score_quality_compatibility(
    record: Any,
    task_spec: TaskSpecification,
    m3_entries: list[Any] | None = None,
    fingerprint: Any = None,
    baseline_mode: str = "baseline_c",
) -> UtilityComponent:
    """Evaluate sample cleanliness (nulls, duplicates, constant columns) on bounded sample."""
    if baseline_mode in {"baseline_a", "baseline_b"} or not fingerprint:
        return UtilityComponent(
            component_name="quality_compatibility",
            score=0.5,
            epistemic_state="unknown",
            evidence_basis="unstated",
            explanation="Data quality unobserved without empirical content fingerprint.",
            source_evidence_ids=(),
            fingerprint_ids=(),
            task_spec_fields=(),
        )

    fp_id = (getattr(fingerprint, "fingerprint_id", ""),)
    modality = getattr(fingerprint, "primary_modality", "")
    if modality in {"unsupported", "failed"}:
        return UtilityComponent(
            component_name="quality_compatibility",
            score=0.3,
            epistemic_state=modality,
            evidence_basis="unstated",
            explanation=f"Data quality unobservable due to {modality} sample access.",
            source_evidence_ids=(),
            fingerprint_ids=fp_id,
            task_spec_fields=(),
        )

    quality = getattr(fingerprint, "quality_heuristics", {})
    null_rate = quality.get("overall_null_rate", 0.0)
    dup_rate = quality.get("duplicate_record_rate", 0.0)
    degen_rate = quality.get("degenerate_record_rate", 0.0)
    const_cols = len(quality.get("constant_columns", []))

    # Baseline heuristic calculation
    penalty = null_rate + dup_rate + degen_rate + (0.05 * min(const_cols, 4))
    score = max(0.0, min(1.0, round(1.0 - penalty, 4)))

    return UtilityComponent(
        component_name="quality_compatibility",
        score=score,
        epistemic_state="known_favorable" if score >= 0.8 else "known_unfavorable",
        evidence_basis="direct_observation",
        explanation=f"Quality computed from sample: null_rate={null_rate}, dup_rate={dup_rate}, constant_cols={const_cols}.",
        source_evidence_ids=(),
        fingerprint_ids=fp_id,
        task_spec_fields=(),
    )


def score_governance_compatibility(
    record: Any,
    task_spec: TaskSpecification,
    m3_entries: list[Any] | None = None,
    fingerprint: Any = None,
    baseline_mode: str = "baseline_c",
) -> UtilityComponent:
    """Evaluate license permissiveness and usage restrictions against task constraints."""
    gov_constraints = task_spec.governance_constraints
    prohibited = [p.lower() for p in gov_constraints.get("prohibited_licenses", ())]
    allowed = [a.lower() for a in gov_constraints.get("allowed_licenses", ())]

    evidence_ids: list[str] = []
    licenses: list[str] = []
    has_conflict = False

    if m3_entries and baseline_mode in {"baseline_b", "baseline_c"}:
        for e in m3_entries:
            if getattr(e, "claim_type", "") == "license":
                val = str(getattr(e, "claim_value", "")).lower()
                licenses.append(val)
                evidence_ids.append(getattr(e, "entry_id", ""))
                if getattr(e, "observation_state", "") == "conflicting":
                    has_conflict = True

    raw_lic = record.governance.get("license_claim") if hasattr(record, "governance") else None
    if raw_lic:
        licenses.append(str(raw_lic).lower())

    if len(set(licenses)) > 1:
        has_conflict = True

    if not licenses:
        return UtilityComponent(
            component_name="governance_compatibility",
            score=0.5,
            epistemic_state="unknown",
            evidence_basis="unstated",
            explanation="License unstated in dataset metadata.",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=(),
            task_spec_fields=("governance_constraints",),
        )

    # Check prohibited licenses
    if prohibited and any(any(p in lic for p in prohibited) for lic in licenses):
        return UtilityComponent(
            component_name="governance_compatibility",
            score=0.0,
            epistemic_state="known_unfavorable",
            evidence_basis="publisher_claim",
            explanation=f"Dataset license ({licenses[0]}) matches prohibited license list ({prohibited}).",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=(),
            task_spec_fields=("governance_constraints",),
        )

    if has_conflict:
        return UtilityComponent(
            component_name="governance_compatibility",
            score=0.5,
            epistemic_state="conflicting",
            evidence_basis="publisher_claim",
            explanation=f"Conflicting license representations observed: {licenses}.",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=(),
            task_spec_fields=("governance_constraints",),
        )

    # Check allowed licenses
    if allowed:
        if any(any(a in lic for a in allowed) for lic in licenses):
            return UtilityComponent(
                component_name="governance_compatibility",
                score=1.0,
                epistemic_state="known_favorable",
                evidence_basis="publisher_claim",
                explanation=f"Dataset license ({licenses[0]}) is in allowed list.",
                source_evidence_ids=tuple(evidence_ids),
                fingerprint_ids=(),
                task_spec_fields=("governance_constraints",),
            )
        else:
            return UtilityComponent(
                component_name="governance_compatibility",
                score=0.3,
                epistemic_state="known_unfavorable",
                evidence_basis="publisher_claim",
                explanation=f"Dataset license ({licenses[0]}) not in allowed list.",
                source_evidence_ids=tuple(evidence_ids),
                fingerprint_ids=(),
                task_spec_fields=("governance_constraints",),
            )

    # Permissive defaults
    return UtilityComponent(
        component_name="governance_compatibility",
        score=1.0,
        epistemic_state="known_favorable",
        evidence_basis="publisher_claim",
        explanation=f"Dataset license documented ({licenses[0]}); no prohibitive constraints specified.",
        source_evidence_ids=tuple(evidence_ids),
        fingerprint_ids=(),
        task_spec_fields=("governance_constraints",),
    )


def score_access_feasibility(
    record: Any,
    task_spec: TaskSpecification,
    m3_entries: list[Any] | None = None,
    fingerprint: Any = None,
    baseline_mode: str = "baseline_c",
) -> UtilityComponent:
    """Evaluate operational network accessibility and endpoint health under M0 policy."""
    if baseline_mode == "baseline_a":
        # Baseline A naively assumes access is 1.0
        return UtilityComponent(
            component_name="access_feasibility",
            score=1.0,
            epistemic_state="known_favorable",
            evidence_basis="publisher_claim",
            explanation="Naive baseline assumption: access assumed operational.",
            source_evidence_ids=(),
            fingerprint_ids=(),
            task_spec_fields=("access_constraints",),
        )

    access_block = record.access if hasattr(record, "access") else {}
    sample_acc = access_block.get("sample_accessible", "conditional")
    access_type = access_block.get("access_type", "")

    evidence_ids = []
    if m3_entries:
        for e in m3_entries:
            if getattr(e, "evidence_type", "") == "access_probe":
                evidence_ids.append(getattr(e, "entry_id", ""))

    fp_id = ()
    fp_mod = None
    if fingerprint:
        fp_id = (getattr(fingerprint, "fingerprint_id", ""),)
        fp_mod = getattr(fingerprint, "primary_modality", "")

    if fp_mod == "failed" or sample_acc == "failed":
        return UtilityComponent(
            component_name="access_feasibility",
            score=0.2,
            epistemic_state="failed",
            evidence_basis="direct_observation",
            explanation="Operational failure observed during sample endpoint access (e.g. HTTP 502).",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=fp_id,
            task_spec_fields=("access_constraints",),
        )

    if fp_mod == "unsupported" or sample_acc == "unsupported_or_policy_limited":
        return UtilityComponent(
            component_name="access_feasibility",
            score=0.3,
            epistemic_state="unsupported",
            evidence_basis="direct_observation",
            explanation="Direct sample acquisition unsupported without credentials under M0 policy.",
            source_evidence_ids=tuple(evidence_ids),
            fingerprint_ids=fp_id,
            task_spec_fields=("access_constraints",),
        )

    return UtilityComponent(
        component_name="access_feasibility",
        score=1.0,
        epistemic_state="known_favorable",
        evidence_basis="direct_observation",
        explanation=f"Operational access verified: public endpoint ({access_type}).",
        source_evidence_ids=tuple(evidence_ids),
        fingerprint_ids=fp_id,
        task_spec_fields=("access_constraints",),
    )
