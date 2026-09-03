"""Candidate-generation retrieval over canonical dataset records only."""

from .engine import RetrievalEngine
from .query import RetrievalQuery, normalize_query

__all__ = ["RetrievalEngine", "RetrievalQuery", "normalize_query"]
