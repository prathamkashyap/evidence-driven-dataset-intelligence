from __future__ import annotations
from abc import ABC, abstractmethod
from math import sqrt

class DenseEncoder(ABC):
    model_id: str
    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]: ...

class SentenceTransformersEncoder(DenseEncoder):
    def __init__(self, model_id: str, revision: str = "main"):
        self.model_id, self.revision = model_id, revision
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_id, revision=revision)
    def encode(self, texts):
        return self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()

class TestDenseEncoder(DenseEncoder):
    """Deterministic test double; never used for reported M2 measurements."""
    model_id="test-token-vector-v1"
    def encode(self, texts):
        vectors=[]
        for text in texts:
            vector=[0.0]*64
            for token in text.lower().split(): vector[hash(token) % 64] += 1.0
            vectors.append(vector)
        return vectors

def cosine(a,b):
    denom=sqrt(sum(x*x for x in a))*sqrt(sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b))/denom if denom else 0.0

class DenseIndex:
    version="dense-v1"
    def __init__(self, documents, vectors, encoder): self.documents,self.vectors,self.encoder=documents,vectors,encoder
    def search(self, text, top_k):
        if not self.documents or not text.strip(): return []
        query=self.encoder.encode([text])[0]
        pairs=sorted(zip(self.documents,(cosine(query,v) for v in self.vectors)),key=lambda x:(-x[1],x[0]["dataset_id"]))[:top_k]
        return pairs
