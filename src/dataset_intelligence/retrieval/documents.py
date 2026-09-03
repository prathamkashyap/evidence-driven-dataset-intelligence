from __future__ import annotations
import re

def _text(value):
    if value is None: return ""
    return " ".join(value) if isinstance(value, list) else str(value)

def build_retrieval_document(record: dict) -> dict:
    semantic = record.get("semantics", {})
    identity = record.get("identity", {})
    fields = {"dataset_name": identity.get("dataset_name"), "description": semantic.get("description"), "task": semantic.get("task"), "domain": semantic.get("domain"), "modality": semantic.get("modality"), "target": semantic.get("target"), "label_type": semantic.get("label_type"), "tags": semantic.get("tags"), "intended_use": semantic.get("intended_use")}
    text = " ".join(_text(v) for v in fields.values() if v is not None)
    return {"dataset_id": record["internal_id"], "source": identity.get("source_name"), "text": text, "tokens": tuple(re.findall(r"[a-z0-9]+", text.lower())), "fields": fields}
