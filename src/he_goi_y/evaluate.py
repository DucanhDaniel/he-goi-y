"""Đánh giá offline: rating prediction (RMSE/MAE) + top-N ranking."""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from . import data
from .models import build_all

K = 10
REL = 4.0  # test rating >= 4 coi là "phù hợp"


def evaluate(models, train, test, ds, k=K):
    hist = {u: dict(zip(g["i"], g["rating"])) for u, g in train.groupby("u")}
    tgt = {u: g for u, g in test.groupby("u")}
    pop = np.bincount(train["i"], minlength=ds.n_items)
    self_info = -np.log2((pop + 1) / (ds.n_users + 1))
    disc = 1 / np.log2(np.arange(2, k + 2))
    rows = []
    for name, m in models.items():
        t0 = time.time()
        se, ae, n = 0.0, 0.0, 0
        P, R, N, H = [], [], [], []
        rec_items, nov = [], []
        for u, g in tgt.items():
            h = hist.get(u, {})
            pr = m.predict_ratings(h)
            if pr is not None:
                err = pr[g["i"].to_numpy()] - g["rating"].to_numpy()
                se += (err ** 2).sum()
                ae += np.abs(err).sum()
                n += len(err)
            rel = set(g.loc[g["rating"] >= REL, "i"])
            sc = np.array(m.rank_scores(h), dtype=float)
            sc[list(h)] = -np.inf  # bỏ phim đã xem
            top = np.argpartition(-sc, k)[:k]
            top = top[np.argsort(-sc[top])]
            rec_items.append(top)
            nov.append(self_info[top].mean())
            if not rel:
                continue
            hit = np.array([i in rel for i in top])
            P.append(hit.mean())
            R.append(hit.sum() / len(rel))
            H.append(float(hit.any()))
            idcg = disc[: min(len(rel), k)].sum()
            N.append((hit * disc).sum() / idcg)
        rows.append({
            "model": name,
            "RMSE": np.sqrt(se / n) if n else np.nan,
            "MAE": ae / n if n else np.nan,
            f"Precision@{k}": np.mean(P),
            f"Recall@{k}": np.mean(R),
            f"NDCG@{k}": np.mean(N),
            f"HitRate@{k}": np.mean(H),
            "Coverage": len(np.unique(np.concatenate(rec_items))) / ds.n_items,
            "Novelty": float(np.mean(nov)),
            "sec": round(time.time() - t0, 1),
        })
        print({kk: round(float(v), 4) if kk != "model" else v for kk, v in rows[-1].items()}, flush=True)
    return pd.DataFrame(rows)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ds = data.load()
    train, test = data.temporal_split(ds.ratings)
    print(f"train={len(train)} test={len(test)} users={ds.n_users} items={ds.n_items}")
    models = build_all(train, ds)
    res = evaluate(models, train, test, ds)
    out = data.ROOT / "results"
    out.mkdir(exist_ok=True)
    res.to_csv(out / "metrics.csv", index=False)
    json.dump({"train": len(train), "test": len(test), "k": K, "rel": REL},
              open(out / "meta.json", "w"))
    print(res.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
