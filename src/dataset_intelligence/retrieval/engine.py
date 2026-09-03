from __future__ import annotations
import hashlib, json, platform, sys
from pathlib import Path
from .bm25 import BM25Index
from .dense import DenseIndex
from .documents import build_retrieval_document
from .fusion import reciprocal_rank_fusion

class RetrievalEngine:
    def __init__(self, records, encoder, config):
        self.records=list(records); self.documents=[build_retrieval_document(r) for r in self.records]; self.encoder=encoder; self.config=config
        self.bm25=BM25Index(self.documents, **config.get("bm25",{})); self.dense=None
    @classmethod
    def from_jsonl(cls, corpus_path, encoder, config):
        return cls([json.loads(line) for line in Path(corpus_path).read_text().splitlines() if line.strip()], encoder, config)
    def build_dense(self): self.dense=DenseIndex(self.documents,self.encoder.encode([d["text"] for d in self.documents]),self.encoder); return self
    def save_metadata(self, directory):
        path=Path(directory); path.mkdir(parents=True,exist_ok=True); raw="\n".join(json.dumps(r,sort_keys=True) for r in self.records)
        metadata={"index_schema_version":"1", "corpus_hash":hashlib.sha256(raw.encode()).hexdigest(), "corpus_records":len(self.records), "bm25_version":self.bm25.version,"dense_version":DenseIndex.version,"embedding_model":self.encoder.model_id,"python_version":sys.version,"platform":platform.platform(),"config":self.config}
        (path/"metadata.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)); return metadata
    def _rows(self, pairs, method, query_id):
        return [{"dataset_id":doc["dataset_id"],"source":doc["source"],"rank":rank,"score":score,"method":method,"query_id":query_id,"index_version":self.bm25.version if method=="bm25" else DenseIndex.version,"contributions":{method:{"rank":rank,"score":score}}} for rank,(doc,score) in enumerate(pairs,1)]
    def retrieve(self, query, top_k, method):
        if method=="bm25": return self._rows(self.bm25.search(query.keywords,top_k),method,query.query_id)
        if method=="dense":
            if self.dense is None: self.build_dense()
            return self._rows(self.dense.search(query.normalized_text,top_k),method,query.query_id)
        raise ValueError("method must be bm25 or dense")
    def retrieve_hybrid(self, query, top_k):
        rows=reciprocal_rank_fusion({"bm25":self.retrieve(query,top_k,"bm25"),"dense":self.retrieve(query,top_k,"dense")},top_k,self.config.get("hybrid",{}).get("rrf_k",60))
        for row in rows: row.update({"query_id":query.query_id,"index_version":"hybrid-rrf-v1"})
        return rows
