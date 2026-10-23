"""Grid search nhỏ trên tập validation (20% cuối của train mỗi user). Test không được dùng."""
from __future__ import annotations

import sys

from . import data
from .evaluate import evaluate
from .models import ALS, EASE, ContentBased, Hybrid, ItemKNN

GRID = {
    "ItemKNN": [dict(k=k, shrink=s) for k in (20, 40, 80) for s in (10.0, 50.0)],
    "ALS": [dict(k=k, reg=r) for k in (16, 32, 64) for r in (3.0, 8.0, 20.0)],
    "EASE": [dict(lam=l) for l in (50.0, 150.0, 300.0, 600.0, 1200.0)],
}
CLS = {"ItemKNN": ItemKNN, "ALS": ALS, "EASE": EASE}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ds = data.load()
    train, _ = data.temporal_split(ds.ratings)
    fit, val = data.temporal_split(train)
    best = {}
    for name, grid in GRID.items():
        models = {str(p): CLS[name](**p).fit(fit, ds) for p in grid}
        r = evaluate(models, fit, val, ds)
        best[name] = r.loc[r["NDCG@10"].idxmax(), "model"]
        print(name, "→", best[name])
    als = ALS(**eval(best["ALS"])).fit(fit, ds)
    content = ContentBased().fit(fit, ds)
    hy = {str(dict(w=w)): Hybrid(als, content, w=w).fit(fit, ds) for w in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)}
    r = evaluate(hy, fit, val, ds)
    best["Hybrid"] = r.loc[r["NDCG@10"].idxmax(), "model"]
    print("BEST =", best)


if __name__ == "__main__":
    main()
