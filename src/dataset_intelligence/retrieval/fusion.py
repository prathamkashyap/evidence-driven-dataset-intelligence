from __future__ import annotations
def reciprocal_rank_fusion(rankings, top_k, rrf_k=60):
    combined={}
    for method, results in rankings.items():
        for rank, result in enumerate(results,1):
            row=combined.setdefault(result["dataset_id"], {"dataset_id":result["dataset_id"],"source":result["source"],"contributions":{}})
            row["contributions"][method]={"rank":rank,"score":result["score"]}; row["score"]=row.get("score",0)+1/(rrf_k+rank)
    return [dict(row, rank=i, method="hybrid_rrf") for i,row in enumerate(sorted(combined.values(),key=lambda x:(-x["score"],x["dataset_id"]))[:top_k],1)]
