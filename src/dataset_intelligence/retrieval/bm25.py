from __future__ import annotations
from collections import Counter
from math import log

class BM25Index:
    version = "bm25-v1"
    def __init__(self, documents, k1=1.2, b=0.75):
        self.documents, self.k1, self.b = list(documents), k1, b
        self.lengths=[len(d["tokens"]) for d in self.documents]; self.avgdl=sum(self.lengths)/len(self.lengths) if self.lengths else 0
        self.tfs=[Counter(d["tokens"]) for d in self.documents]; self.df=Counter(t for tf in self.tfs for t in tf)
    def search(self, tokens, top_k):
        if not self.documents or not tokens: return []
        n=len(self.documents); rows=[]
        for i,(doc,tf) in enumerate(zip(self.documents,self.tfs)):
            score=0.0
            for term in tokens:
                if not tf[term]: continue
                idf=log(1+(n-self.df[term]+0.5)/(self.df[term]+0.5)); denom=tf[term]+self.k1*(1-self.b+self.b*self.lengths[i]/self.avgdl)
                score += idf*(tf[term]*(self.k1+1)/denom)
            if score>0: rows.append((doc,score))
        return sorted(rows,key=lambda x:(-x[1],x[0]["dataset_id"]))[:top_k]
