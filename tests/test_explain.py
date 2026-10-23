"""Giải thích phải trung thực: tổng các thành phần = đúng điểm mô hình dùng để xếp hạng."""
import numpy as np
import pytest

from he_goi_y import data
from he_goi_y.models import build_all

ds = data.load()
train, _ = data.temporal_split(ds.ratings)
MODELS = build_all(train, ds)
TITLE = {t: i for i, t in enumerate(ds.movies["title"])}
HISTORIES = {
    "user lịch sử dài": dict(train.loc[train["u"] == train["u"].value_counts().idxmax(), ["i", "rating"]].values),
    "user thường": dict(train.loc[train["u"] == 5, ["i", "rating"]].values),
    "user mới 3 phim": {TITLE["Matrix, The (1999)"]: 5.0, TITLE["Toy Story (1995)"]: 4.0,
                        TITLE["Titanic (1997)"]: 1.0},
    "user chưa có gì": {},
}
HISTORIES = {k: {int(i): float(r) for i, r in h.items()} for k, h in HISTORIES.items()}


@pytest.mark.parametrize("model", list(MODELS))
@pytest.mark.parametrize("who", list(HISTORIES))
def test_explanation_sums_to_score(model, who):
    m, h = MODELS[model], HISTORIES[who]
    scores = np.asarray(m.rank_scores(h), dtype=float)
    cand = [i for i in np.argsort(-scores)[:5]] + list(np.random.default_rng(1).integers(0, ds.n_items, 5))
    for i in cand:
        e = m.explain(h, int(i))
        assert e.score == pytest.approx(scores[i], abs=1e-6), (model, who, i)
        assert e.total() == pytest.approx(e.score, abs=1e-6), (model, who, i)
        assert e.text
        if model == "Content-based" and h:
            # cách phân rã thứ hai (theo thể loại / tag / thập niên) cũng phải cộng đúng bằng điểm
            assert sum(v for _, v in e.features) == pytest.approx(e.score, abs=1e-6)
