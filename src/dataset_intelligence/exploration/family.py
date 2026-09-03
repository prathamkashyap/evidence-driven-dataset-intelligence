"""Conservative multi-signal dataset family linkage and redundancy detection."""

from __future__ import annotations

import re
from typing import Any

LINKAGE_STATES = frozenset({"same_family", "different_family", "unknown_family"})


def normalize_tokens(text: str | None) -> set[str]:
    """Tokenize and normalize text to lowercase alphanumeric tokens."""
    if not text:
        return set()
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def evaluate_family_linkage(rec1: Any, rec2: Any) -> tuple[str, list[str]]:
    """Evaluate relationship between two dataset records using multiple corroborating signals."""
    if not hasattr(rec1, "identity") or not hasattr(rec2, "identity"):
        return "unknown_family", ["missing_identity_block"]

    did1 = rec1.internal_id if hasattr(rec1, "internal_id") else ""
    did2 = rec2.internal_id if hasattr(rec2, "internal_id") else ""
    if did1 == did2:
        return "same_family", ["identical_dataset_id"]

    # Check for fundamental modality / task clash -> different_family
    mod1 = rec1.semantics.get("modality", []) if hasattr(rec1, "semantics") else []
    mod2 = rec2.semantics.get("modality", []) if hasattr(rec2, "semantics") else []
    s_mod1 = set(str(m).lower() for m in (mod1 if isinstance(mod1, (list, tuple)) else [mod1]))
    s_mod2 = set(str(m).lower() for m in (mod2 if isinstance(mod2, (list, tuple)) else [mod2]))

    if s_mod1 and s_mod2 and not (s_mod1 & s_mod2) and "multimodal" not in (s_mod1 | s_mod2):
        return "different_family", ["disjoint_modalities"]

    matching_signals: list[str] = []

    # Signal 1: Name token overlap
    name1 = rec1.identity.get("dataset_name", "")
    name2 = rec2.identity.get("dataset_name", "")
    tokens1 = normalize_tokens(name1)
    tokens2 = normalize_tokens(name2)
    common_tokens = tokens1 & tokens2 - {"data", "dataset", "database", "the", "a", "and", "of"}

    if common_tokens:
        matching_signals.append(f"name_token_overlap:{sorted(common_tokens)}")

    # Signal 2: Modality and Task alignment
    if s_mod1 and s_mod2 and (s_mod1 & s_mod2):
        matching_signals.append(f"compatible_modality:{sorted(s_mod1 & s_mod2)}")
        task1 = rec1.semantics.get("task", []) if hasattr(rec1, "semantics") else []
        task2 = rec2.semantics.get("task", []) if hasattr(rec2, "semantics") else []
        s_task1 = set(str(t).lower() for t in (task1 if isinstance(task1, (list, tuple)) else [task1]))
        s_task2 = set(str(t).lower() for t in (task2 if isinstance(task2, (list, tuple)) else [task2]))
        if s_task1 and s_task2 and (s_task1 & s_task2):
            matching_signals.append(f"compatible_task:{sorted(s_task1 & s_task2)}")

    # Signal 3: Structural overlap (sample count or class count match)
    struct1 = rec1.structure if hasattr(rec1, "structure") else {}
    struct2 = rec2.structure if hasattr(rec2, "structure") else {}
    samples1 = struct1.get("sample_count")
    samples2 = struct2.get("sample_count")
    classes1 = struct1.get("class_count")
    classes2 = struct2.get("class_count")

    if (samples1 is not None and samples2 is not None and samples1 == samples2) or (
        classes1 is not None and classes2 is not None and classes1 == classes2 and classes1 > 1
    ):
        matching_signals.append("structural_dimension_overlap")

    # Signal 4: Explicit family ID or lineage overlap
    fam1 = rec1.identity.get("dataset_family_id") if hasattr(rec1, "identity") else None
    fam2 = rec2.identity.get("dataset_family_id") if hasattr(rec2, "identity") else None
    if fam1 and fam2 and fam1 == fam2 and fam1 != "unresolved":
        matching_signals.append(f"matching_family_id:{fam1}")

    # Conservative rule: Require name token overlap or explicit family_id AND at least one corroborating signal
    has_name_anchor = bool(common_tokens)
    has_family_id_anchor = bool(fam1 and fam2 and fam1 == fam2 and fam1 != "unresolved")

    if (has_name_anchor or has_family_id_anchor) and len(matching_signals) >= 2:
        return "same_family", matching_signals

    if not has_name_anchor and not has_family_id_anchor:
        return "different_family", ["disjoint_names_and_lineage"]

    return "unknown_family", matching_signals


def detect_family_redundancy(
    candidate: Any,
    main_pool: list[Any],
) -> tuple[bool, str | None, str | None]:
    """Check if candidate is a redundant instance of any dataset already in the main pool."""
    cand_id = candidate.internal_id if hasattr(candidate, "internal_id") else ""

    for main_rec in main_pool:
        main_id = main_rec.internal_id if hasattr(main_rec, "internal_id") else ""
        if cand_id == main_id:
            return True, "identical_dataset", main_id

        state, reasons = evaluate_family_linkage(candidate, main_rec)
        if state == "same_family":
            cand_name = candidate.identity.get("dataset_name", "") if hasattr(candidate, "identity") else ""
            main_name = main_rec.identity.get("dataset_name", "") if hasattr(main_rec, "identity") else ""
            return True, f"family_variant({cand_name} matches {main_name})", main_id

    return False, None, None
