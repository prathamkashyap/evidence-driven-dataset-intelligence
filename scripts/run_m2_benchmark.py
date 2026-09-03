from __future__ import annotations
import json, resource, sys, time
from pathlib import Path
from dataset_intelligence.retrieval.dense import SentenceTransformersEncoder
from dataset_intelligence.retrieval.engine import RetrievalEngine
from dataset_intelligence.retrieval.metrics import evaluate
from dataset_intelligence.retrieval.query import normalize_query

ROOT=Path(__file__).resolve().parents[1]
def main():
    config=json.loads((ROOT/"configs/m2_retrieval.json").read_text()); start=time.perf_counter()
    encoder=SentenceTransformersEncoder(config["dense"]["model_id"],config["dense"]["model_revision"])
    engine=RetrievalEngine.from_jsonl(ROOT/config["corpus"],encoder,config); dense_start=time.perf_counter(); engine.build_dense(); metadata=engine.save_metadata(ROOT/config["index_directory"])
    queries=json.loads((ROOT/"experiments/m2/benchmark/development_queries.json").read_text()); rows=[]
    for item in queries:
        query=normalize_query(item["query_id"],item["natural_language_query"])
        for method, call in (("bm25",lambda:engine.retrieve(query,10,"bm25")),("dense",lambda:engine.retrieve(query,10,"dense")),("hybrid_rrf",lambda:engine.retrieve_hybrid(query,10))):
            t=time.perf_counter(); results=call(); rows.append({"query_id":query.query_id,"method":method,"latency_ms":(time.perf_counter()-t)*1000,"metrics":evaluate(results,item["relevance"]),"results":results})
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss = rss if sys.platform == "darwin" else rss * 1024
    artifact={"metadata":metadata,"index_build_ms":(dense_start-start)*1000,"embedding_generation_ms":(time.perf_counter()-dense_start)*1000,"peak_rss_bytes":peak_rss,"runs":rows}
    out=ROOT/"experiments/m2/results/benchmark.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(artifact,indent=2)); print(out)
if __name__ == "__main__": main()
