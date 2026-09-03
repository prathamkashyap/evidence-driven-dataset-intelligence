from __future__ import annotations

from dataclasses import asdict, dataclass
import re

_TERMS = {"image": ("image", "vision", "cv", "photograph"), "text": ("text", "nlp", "sentiment", "news"), "tabular": ("tabular", "table", "csv", "arff"), "classification": ("classification", "classify", "recognition", "labels"), "regression": ("regression", "predict continuous")}

@dataclass(frozen=True)
class RetrievalQuery:
    query_id: str
    original_text: str
    normalized_text: str
    task: tuple[str, ...] = ()
    domain: tuple[str, ...] = ()
    modality: tuple[str, ...] = ()
    target: tuple[str, ...] = ()
    label_type: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    unresolved_constraints: tuple[str, ...] = ()
    def to_dict(self): return asdict(self)

def normalize_query(query_id: str, text: str) -> RetrievalQuery:
    normalized = " ".join(re.findall(r"[a-z0-9]+", text.lower()))
    tokens = tuple(dict.fromkeys(normalized.split()))
    token_set = set(tokens)
    found = {key for key, terms in _TERMS.items() if any(
        all(w in token_set for w in term.split()) for term in terms
    )}
    return RetrievalQuery(query_id=query_id, original_text=text, normalized_text=normalized,
      task=tuple(sorted(found & {"classification", "regression"})), modality=tuple(sorted(found & {"image", "text", "tabular"})), keywords=tokens)
