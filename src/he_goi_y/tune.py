"""Grid search nhỏ trên tập validation (20% cuối của train mỗi user). Test không được dùng."""
from __future__ import annotations

import json
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


DEEP_GRID = {
    "LightGCN": [dict(layers=l, epochs=e) for l in (1, 2, 3) for e in (100, 300)],
    "SASRec": [dict(dropout=d, epochs=e) for d in (0.2, 0.5) for e in (50, 100, 200)],
}


def tune_deep(ds, fit, val):
    """Tune LightGCN/SASRec trên validation, ghi results/best_deep.json cho `evaluate --deep`."""
    from .deep import LightGCN, SASRec

    cls = {"LightGCN": LightGCN, "SASRec": SASRec}
    best = {}
    for name, grid in DEEP_GRID.items():
        models = {json.dumps(p): cls[name](**p).fit(fit, ds) for p in grid}
        r = evaluate(models, fit, val, ds)
        best[name] = json.loads(r.loc[r["NDCG@10"].idxmax(), "model"])
        print(name, "→", best[name])
    out = data.ROOT / "results"
    out.mkdir(exist_ok=True)
    json.dump(best, open(out / "best_deep.json", "w", encoding="utf-8"), indent=2)
    print("BEST_DEEP =", best)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ds = data.load()
    train, _ = data.temporal_split(ds.ratings)
    fit, val = data.temporal_split(train)
    if "--deep" in sys.argv:
        return tune_deep(ds, fit, val)
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
