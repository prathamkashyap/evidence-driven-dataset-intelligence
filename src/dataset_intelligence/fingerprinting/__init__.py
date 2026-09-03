"""Dataset fingerprinting foundation: structural, statistical, and quality diagnostics."""

from .image import extract_image_features, parse_image_header
from .pipeline import compute_fingerprint
from .quality import compute_quality_heuristics
from .schema import DatasetFingerprint, compute_fingerprint_id
from .tabular import extract_tabular_features
from .target import extract_target_diagnostics
from .text import extract_text_features

__all__ = [
    "DatasetFingerprint",
    "compute_fingerprint",
    "compute_fingerprint_id",
    "compute_quality_heuristics",
    "extract_image_features",
    "extract_tabular_features",
    "extract_target_diagnostics",
    "extract_text_features",
    "parse_image_header",
]
