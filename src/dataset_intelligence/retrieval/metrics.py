from __future__ import annotations
from math import log2
def evaluate(results, relevance, ks=(1,3,5,10)):
    relevant=set(relevance); grades=relevance if isinstance(relevance,dict) else {x:1 for x in relevant}; output={}
    for k in ks:
        ids=[r["dataset_id"] for r in results[:k]]; hits=[x for x in ids if x in relevant]
        output[f"recall@{k}"]=len(hits)/len(relevant) if relevant else 0.0; output[f"precision@{k}"]=len(hits)/k
        output[f"mrr@{k}"]=next((1/(i+1) for i,x in enumerate(ids) if x in relevant),0.0)
        dcg=sum((2**grades.get(x,0)-1)/log2(i+2) for i,x in enumerate(ids)); ideal=sorted(grades.values(),reverse=True)[:k]; idcg=sum((2**g-1)/log2(i+2) for i,g in enumerate(ideal)); output[f"ndcg@{k}"]=dcg/idcg if idcg else 0.0
    return output
