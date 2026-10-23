"""Các mô hình gợi ý. Giao diện chung:

    fit(train: DataFrame[u,i,rating], ds: Dataset) -> self
    predict_ratings(history: {i: rating}) -> ndarray (n_items,) | None   # thang 0.5-5
    rank_scores(history) -> ndarray (n_items,)  # càng cao càng nên gợi ý
    explain(history, item) -> Explanation       # phân rã đúng điểm rank_scores(history)[item]

`history` là các phim người dùng đã chấm, nên cùng một API dùng được cho user có
sẵn lẫn user mới (cold-start do người dùng tự chấm trong UI).

Giải thích là *trung thực* (faithful), không phải đoán sau: mọi mô hình ở đây tuyến tính theo
lịch sử khi tham số đã cố định, nên điểm được tách chính xác thành tổng các thành phần
(`terms`) và đóng góp của từng phim đã xem (`items`). `tests/test_explain.py` kiểm tra
tổng các thành phần bằng đúng điểm mô hình.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


def _zscore(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / (x.std() + 1e-9)


def _hist_arrays(history):
    return np.fromiter(history.keys(), int), np.fromiter(history.values(), float)


@dataclass
class Explanation:
    model: str
    score: float          # đúng bằng rank_scores(history)[item]
    unit: str             # "★" nếu score là rating dự đoán, "" nếu là điểm xếp hạng
    formula: str
    terms: list = field(default_factory=list)     # [(nhãn, giá trị)] thành phần không gắn với phim cụ thể
    items: list = field(default_factory=list)     # [(phim đã xem, đóng góp)]
    features: list = field(default_factory=list)  # [(đặc trưng, đóng góp)] cách phân rã thứ hai (nội dung)
    text: str = ""

    def total(self) -> float:
        return float(sum(v for _, v in self.terms) + sum(v for _, v in self.items))


class Recommender:
    name = "base"
    desc = ""

    def fit(self, train, ds):
        self.ds = ds
        self.n_items = ds.n_items
        return self

    def predict_ratings(self, history):
        return None

    def rank_scores(self, history):
        return self.predict_ratings(history)

    def explain(self, history, item: int) -> Explanation:
        raise NotImplementedError

    # ── tiện ích viết câu giải thích ──
    def _title(self, j) -> str:
        return self.ds.movies.title[j]

    def _items_text(self, items, unit, lead, neg_lead="bị kéo xuống bởi", k=3) -> str:
        pos = sorted((p for p in items if p[1] > 1e-6), key=lambda p: -p[1])[:k]
        neg = sorted((p for p in items if p[1] < -1e-6), key=lambda p: p[1])[:1]
        out = []
        if pos:
            out.append(f"{lead}: " + "; ".join(f"{self._title(j)} ({v:+.3f}{unit})" for j, v in pos))
        if neg:
            j, v = neg[0]
            out.append(f"{neg_lead} {self._title(j)} ({v:+.3f}{unit})")
        return ", ".join(out)


# ───────────────────────── Baselines ─────────────────────────
class RandomRec(Recommender):
    name = "Random"
    desc = "Baseline sàn: gợi ý ngẫu nhiên."

    def rank_scores(self, history):
        # seed theo lịch sử để cùng một người luôn nhận cùng danh sách (giải thích lại được)
        seed = hash(tuple(sorted(int(j) for j in history))) % 2**32
        return np.random.default_rng(seed).random(self.n_items)

    def explain(self, history, item):
        s = float(self.rank_scores(history)[item])
        return Explanation(self.name, s, "", "score = số ngẫu nhiên ~ U(0, 1)",
                           [("Số ngẫu nhiên", s)],
                           text="Chọn ngẫu nhiên, không dùng thông tin gì về bạn hay về phim.")


class Popularity(Recommender):
    name = "Popularity"
    desc = "Baseline phổ biến: xếp theo số lượt đánh giá (non-personalized)."

    def fit(self, train, ds):
        super().fit(train, ds)
        self.count = np.bincount(train["i"], minlength=ds.n_items).astype(float)
        mu = train["rating"].mean()
        s = np.bincount(train["i"], weights=train["rating"], minlength=ds.n_items)
        self.damped = (s + 5 * mu) / (self.count + 5)
        return self

    def predict_ratings(self, history):
        return self.damped

    def rank_scores(self, history):
        return self.count

    def explain(self, history, item):
        n = self.count[item]
        rank = int((self.count > n).sum()) + 1
        return Explanation(self.name, float(n), "", "score = số người đã chấm phim",
                           [("Số người đã chấm phim này", float(n))],
                           text=f"Phổ biến: {int(n)} người đã chấm (hạng {rank}/{self.n_items}). "
                                "Giống nhau với mọi người dùng, không xét lịch sử của bạn.")


class DampedMean(Recommender):
    name = "Top-rated"
    desc = "Baseline chất lượng: điểm trung bình làm mịn Bayes (damping = 5), non-personalized."

    def fit(self, train, ds):
        super().fit(train, ds)
        self.mu = train["rating"].mean()
        self.cnt = np.bincount(train["i"], minlength=ds.n_items)
        self.sum = np.bincount(train["i"], weights=train["rating"], minlength=ds.n_items)
        self.score = (self.sum + 5 * self.mu) / (self.cnt + 5)
        return self

    def predict_ratings(self, history):
        return self.score

    def explain(self, history, item):
        n, s = int(self.cnt[item]), self.sum[item]
        mean = s / n if n else 0.0
        terms = [(f"Điểm TB thật {mean:.2f} × {n}/({n}+5)", s / (n + 5)),
                 (f"Kéo về TB hệ thống μ={self.mu:.2f} × 5/({n}+5)", 5 * self.mu / (n + 5))]
        return Explanation(self.name, float(self.score[item]), "★", "r̂ = (Σr + 5·μ) / (n + 5)", terms,
                           text=f"Điểm TB {mean:.2f}★ từ {n} lượt, trộn {5 / (n + 5):.0%} với TB hệ thống "
                                f"{self.mu:.2f}★ (càng ít lượt càng bị kéo về TB) → {self.score[item]:.2f}★. "
                                "Không xét lịch sử của bạn.")


class BiasBaseline(Recommender):
    """r̂ = μ + b_u + b_i, ước lượng luân phiên có regularization."""
    name = "Bias (μ+bu+bi)"
    desc = "Baseline cá nhân hoá nhẹ: độ khó tính của user + độ hay của phim."

    def __init__(self, reg_u=10.0, reg_i=25.0, iters=10):
        self.reg_u, self.reg_i, self.iters = reg_u, reg_i, iters

    def fit(self, train, ds):
        super().fit(train, ds)
        u, i, r = train["u"].to_numpy(), train["i"].to_numpy(), train["rating"].to_numpy()
        self.mu = r.mean()
        bu = np.zeros(ds.n_users)
        bi = np.zeros(ds.n_items)
        cu = np.bincount(u, minlength=ds.n_users)
        ci = np.bincount(i, minlength=ds.n_items)
        for _ in range(self.iters):
            bi = np.bincount(i, weights=r - self.mu - bu[u], minlength=ds.n_items) / (self.reg_i + ci)
            bu = np.bincount(u, weights=r - self.mu - bi[i], minlength=ds.n_users) / (self.reg_u + cu)
        self.bi = bi
        return self

    def user_bias(self, history) -> float:
        if not history:
            return 0.0
        idx, r = _hist_arrays(history)
        return float((r - self.mu - self.bi[idx]).sum() / (self.reg_u + len(idx)))

    def _residuals(self, train):
        """Phần dư r - (μ + b_u + b_i) trên tập train, b_u tính theo cùng công thức fold-in."""
        u, i, r = train["u"].to_numpy(), train["i"].to_numpy(), train["rating"].to_numpy()
        s = np.bincount(u, weights=r - self.mu - self.bi[i], minlength=self.ds.n_users)
        bu = s / (self.reg_u + np.bincount(u, minlength=self.ds.n_users))
        return r - self.mu - bu[u] - self.bi[i]

    def predict_ratings(self, history):
        return self.mu + self.user_bias(history) + self.bi

    def _bias_terms(self, history, item):
        bu = self.user_bias(history)
        return [("μ: điểm TB toàn hệ thống", self.mu),
                ("b_u: bạn chấm " + ("dễ" if bu >= 0 else "khắt khe") + " hơn TB", bu),
                ("b_i: phim được chấm " + ("cao" if self.bi[item] >= 0 else "thấp") + " hơn TB", self.bi[item])]

    def _bias_text(self, terms):
        _, bu = terms[1]
        _, bi = terms[2]
        return (f"Phim được chấm {'cao' if bi >= 0 else 'thấp'} hơn TB ({bi:+.2f}★), "
                f"bạn chấm {'dễ' if bu >= 0 else 'khắt khe'} hơn TB ({bu:+.2f}★)")

    def explain(self, history, item):
        terms = self._bias_terms(history, item)
        return Explanation(self.name, float(self.predict_ratings(history)[item]), "★",
                           "r̂ = μ + b_u + b_i", terms, text=self._bias_text(terms) + ".")


def _clip_term(terms, items, pred):
    raw = sum(v for _, v in terms) + sum(v for _, v in items)
    if abs(pred - raw) > 1e-9:
        terms.append(("Cắt về thang [0.5, 5]", pred - raw))


# ───────────────────────── Collaborative filtering ─────────────────────────
class ItemKNN(BiasBaseline):
    name = "Item-kNN"
    desc = "Lọc cộng tác theo item: cosine trên phần dư rating (đã trừ bias), shrinkage, top-k láng giềng."

    def __init__(self, k=40, shrink=20.0, damp=1.0):
        super().__init__()
        self.k, self.shrink, self.damp = k, shrink, damp

    def fit(self, train, ds):
        super().fit(train, ds)
        u, i = train["u"].to_numpy(), train["i"].to_numpy()
        resid = self._residuals(train)
        X = sp.csr_matrix((resid, (i, u)), shape=(ds.n_items, ds.n_users))
        B = sp.csr_matrix((np.ones(len(i)), (i, u)), shape=X.shape)
        Xn = normalize(X)
        rows, cols, vals = [], [], []
        for s in range(0, ds.n_items, 1000):
            e = min(s + 1000, ds.n_items)
            sim = (Xn[s:e] @ Xn.T).toarray()
            co = (B[s:e] @ B.T).toarray()
            sim *= co / (co + self.shrink)
            sim[np.arange(e - s), np.arange(s, e)] = 0
            top = np.argpartition(-np.abs(sim), self.k, axis=1)[:, : self.k]
            v = np.take_along_axis(sim, top, 1)
            keep = v != 0
            rows.append(np.repeat(np.arange(s, e), self.k).reshape(-1, self.k)[keep])
            cols.append(top[keep])
            vals.append(v[keep])
        self.S = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                               shape=(ds.n_items, ds.n_items))
        self.Sabs = abs(self.S)
        return self

    def predict_ratings(self, history):
        base = super().predict_ratings(history)
        if not history:
            return base
        idx, r = _hist_arrays(history)
        res = np.zeros(self.n_items)
        res[idx] = r - base[idx]
        seen = np.zeros(self.n_items)
        seen[idx] = 1
        return np.clip(base + (self.S @ res) / (self.Sabs @ seen + self.damp), 0.5, 5)

    def explain(self, history, item):
        terms = self._bias_terms(history, item)
        base = BiasBaseline.predict_ratings(self, history)
        lo, hi = self.S.indptr[item], self.S.indptr[item + 1]
        nb = [(int(j), s) for j, s in zip(self.S.indices[lo:hi], self.S.data[lo:hi]) if j in history]
        den = sum(abs(s) for _, s in nb) + self.damp
        items = [(j, s * (history[j] - base[j]) / den) for j, s in nb]
        pred = float(self.predict_ratings(history)[item])
        _clip_term(terms, items, pred)
        txt = self._items_text(items, "★", "Giống các phim bạn chấm cao hơn kỳ vọng",
                               "bị kéo xuống vì giống phim bạn chấm thấp hơn kỳ vọng")
        return Explanation(self.name, pred, "★",
                           "r̂ = μ + b_u + b_i + Σⱼ sᵢⱼ·(r_uj − b_uj) / (Σⱼ|sᵢⱼ| + 1)", terms, items,
                           text=(txt or "Không có láng giềng nào trong lịch sử của bạn") + ". "
                                + self._bias_text(terms) + ".")


class ALS(BiasBaseline):
    """Matrix factorization: r̂ = μ + b_u + b_i + p_u·q_i, tối ưu ALS trên phần dư."""
    name = "MF-ALS"
    desc = "Phân rã ma trận (latent factors) tối ưu bằng Alternating Least Squares."

    def __init__(self, k=32, reg=8.0, iters=12, seed=0):
        super().__init__()
        self.k, self.reg, self.iters, self.seed = k, reg, iters, seed

    def _solve(self, F, idx, res):
        Fi = F[idx]
        return np.linalg.solve(Fi.T @ Fi + self.reg * np.eye(self.k), Fi.T @ res)

    def fit(self, train, ds):
        super().fit(train, ds)
        u, i = train["u"].to_numpy(), train["i"].to_numpy()
        res = self._residuals(train)
        rng = np.random.default_rng(self.seed)
        P = rng.normal(0, 0.1, (ds.n_users, self.k))
        Q = rng.normal(0, 0.1, (ds.n_items, self.k))
        ou = np.argsort(u, kind="stable")
        bu_ = np.searchsorted(u[ou], np.arange(ds.n_users + 1))
        oi = np.argsort(i, kind="stable")
        bi_ = np.searchsorted(i[oi], np.arange(ds.n_items + 1))
        for _ in range(self.iters):
            for x in range(ds.n_users):
                ix = ou[bu_[x]:bu_[x + 1]]
                if len(ix):
                    P[x] = self._solve(Q, i[ix], res[ix])
            for y in range(ds.n_items):
                ix = oi[bi_[y]:bi_[y + 1]]
                if len(ix):
                    Q[y] = self._solve(P, u[ix], res[ix])
        self.Q = Q
        return self

    def user_vector(self, history):
        if not history:
            return np.zeros(self.k)
        idx, r = _hist_arrays(history)
        return self._solve(self.Q, idx, r - self.mu - self.user_bias(history) - self.bi[idx])

    def predict_ratings(self, history):
        base = super().predict_ratings(history)
        return np.clip(base + self.Q @ self.user_vector(history), 0.5, 5)

    def explain(self, history, item):
        # p_u = A⁻¹ Q_Hᵀ e  với A = Q_HᵀQ_H + λI  ⇒  q_iᵀ p_u = Σ_j (q_iᵀ A⁻¹ q_j) · e_j
        terms = self._bias_terms(history, item)
        items = []
        if history:
            idx, r = _hist_arrays(history)
            Qh = self.Q[idx]
            v = np.linalg.solve(Qh.T @ Qh + self.reg * np.eye(self.k), self.Q[item])
            e = r - self.mu - self.user_bias(history) - self.bi[idx]
            items = list(zip(idx.tolist(), (Qh @ v * e).tolist()))
        pred = float(self.predict_ratings(history)[item])
        _clip_term(terms, items, pred)
        txt = self._items_text(items, "★", "Sở thích ẩn học từ")
        return Explanation(self.name, pred, "★",
                           "r̂ = μ + b_u + b_i + q_iᵀp_u,  q_iᵀp_u = Σⱼ (q_iᵀA⁻¹q_j)·(r_uj − b_uj)",
                           terms, items,
                           text=(txt or "Chưa có lịch sử") + ". " + self._bias_text(terms) + ".")


class EASE(Recommender):
    """Embarrassingly Shallow Autoencoder (Steck, 2019) trên phản hồi ngầm (đã xem / chưa).

    B = argmin ||X - XB||² + λ||B||²  s.t. diag(B)=0, có nghiệm đóng: P=(XᵀX+λI)⁻¹, B=-P/diag(P).
    """
    name = "EASE (implicit)"
    desc = "Mô hình tuyến tính item-item nghiệm đóng trên dữ liệu ngầm (đã xem); mạnh cho top-N."

    def __init__(self, lam=300.0, min_count=2):
        self.lam, self.min_count = lam, min_count

    def fit(self, train, ds):
        super().fit(train, ds)
        cnt = np.bincount(train["i"], minlength=ds.n_items)
        self.items = np.where(cnt >= self.min_count)[0]
        col = np.full(ds.n_items, -1)
        col[self.items] = np.arange(len(self.items))
        t = train[col[train["i"]] >= 0]
        X = sp.csr_matrix((np.ones(len(t)), (t["u"], col[t["i"]])),
                          shape=(ds.n_users, len(self.items)))
        G = (X.T @ X).toarray()
        G[np.diag_indices_from(G)] += self.lam
        P = np.linalg.inv(G)
        self.B = -P / np.diag(P)
        self.B[np.diag_indices_from(self.B)] = 0
        self.col = col
        return self

    def rank_scores(self, history):
        x = np.zeros(len(self.items))
        c = self.col[list(history)] if history else np.array([], int)
        x[c[c >= 0]] = 1
        out = np.full(self.n_items, -1e9)
        out[self.items] = x @ self.B
        return out

    def explain(self, history, item):
        formula = "score = Σⱼ B[j, i]  (j: phim bạn đã xem)"
        c = self.col[item]
        if c < 0:
            return Explanation(self.name, -1e9, "", formula,
                               [("Phim có < 2 lượt xem, EASE không xét", -1e9)],
                               text="Phim quá ít người xem nên EASE không gợi ý.")
        items = [(int(j), float(self.B[self.col[j], c])) for j in history if self.col[j] >= 0]
        txt = self._items_text(items, "", "Người xem các phim này cũng thường xem",
                               "người xem phim này ít khi xem")
        score = float(self.rank_scores(history)[item])
        return Explanation(self.name, score, "", formula, [], items,
                           text=(txt or "Không có phim nào trong lịch sử liên quan") +
                                ". Mô hình chỉ dựa trên việc xem cùng nhau, không dựa trên thể loại.")


# ───────────────────────── Content-based & hybrid ─────────────────────────
class ContentBased(Recommender):
    name = "Content-based"
    desc = "TF-IDF trên thể loại + tag + thập niên; profile user = trung bình có trọng số (rating − mean)."

    def fit(self, train, ds):
        super().fit(train, ds)
        m = ds.movies
        gv = TfidfVectorizer(tokenizer=lambda s: s.split("|"), token_pattern=None, lowercase=False)
        G = gv.fit_transform(m["genres"].replace("(no genres listed)", ""))
        tg = ds.tags.assign(tag=ds.tags["tag"].str.lower()).groupby("movieId")["tag"].apply(" ".join)
        tv = TfidfVectorizer(min_df=2, sublinear_tf=True, stop_words="english")
        T = tv.fit_transform(m["movieId"].map(tg).fillna(""))
        dv = TfidfVectorizer(token_pattern=r"\S+")
        D = dv.fit_transform((m["year"].fillna(0) // 10 * 10).astype(int).astype(str))
        self.X = normalize(sp.hstack([G, 0.6 * T, 0.3 * D]).tocsr())
        self.feat_names = ([f"thể loại {g}" for g in gv.get_feature_names_out()]
                           + [f"tag “{t}”" for t in tv.get_feature_names_out()]
                           + [f"thập niên {d}" for d in dv.get_feature_names_out()])
        return self

    def _profile(self, history):
        idx, r = _hist_arrays(history)
        w = r - r.mean()
        if np.allclose(w, 0):
            w = np.ones_like(w)
        prof = np.asarray(self.X[idx].T @ w).ravel()
        return idx, w, prof, np.linalg.norm(prof)

    def rank_scores(self, history):
        if not history:
            return np.zeros(self.n_items)
        _, _, prof, n = self._profile(history)
        return np.asarray(self.X @ (prof / n)).ravel() if n else np.zeros(self.n_items)

    def explain(self, history, item):
        formula = "score = cos(x_i, profile),  profile = Σⱼ (r_uj − r̄_u)·x_j"
        if not history or (n := self._profile(history)[3]) == 0:
            return Explanation(self.name, 0.0, "", formula, text="Chưa có lịch sử để so khớp nội dung.")
        idx, w, prof, n = self._profile(history)
        xi = self.X.getrow(item)
        sims = np.asarray((self.X[idx] @ xi.T).todense()).ravel()
        items = list(zip(idx.tolist(), (w * sims / n).tolist()))
        feats = sorted(((self.feat_names[f], v * prof[f] / n) for f, v in zip(xi.indices, xi.data)),
                       key=lambda p: -p[1])
        good = [f"{name} ({v:+.3f})" for name, v in feats[:3] if v > 1e-6]
        txt = ("Khớp nội dung bạn thích: " + ", ".join(good)) if good else "Ít đặc trưng chung với gu của bạn"
        near = self._items_text(items, "", "gần với")
        return Explanation(self.name, float(self.rank_scores(history)[item]), "", formula, [], items, feats,
                           text=txt + (f"; {near}" if near else "") + ".")


class Hybrid(Recommender):
    name = "Hybrid (ALS+Content)"
    desc = "Kết hợp tuyến tính z-score điểm MF-ALS và Content-based; rating dự đoán lấy từ ALS."

    def __init__(self, als: ALS, content: ContentBased, w=0.8):
        self.als, self.content, self.w = als, content, w

    def fit(self, train, ds):
        super().fit(train, ds)  # als/content đã được fit bên ngoài
        return self

    def predict_ratings(self, history):
        return self.als.predict_ratings(history)

    def rank_scores(self, history):
        return self.w * _zscore(self.als.predict_ratings(history)) + \
            (1 - self.w) * _zscore(self.content.rank_scores(history))

    def explain(self, history, item):
        a, c = self.als.predict_ratings(history), self.content.rank_scores(history)
        wa, wc = self.w / (a.std() + 1e-9), (1 - self.w) / (c.std() + 1e-9)
        ea, ec = self.als.explain(history, item), self.content.explain(history, item)
        terms = [(f"ALS · {lab}", wa * v) for lab, v in ea.terms] + \
                [("ALS · chuẩn hoá z-score (− trung bình)", -wa * a.mean()),
                 ("Content · chuẩn hoá z-score (− trung bình)", -wc * c.mean())]
        merged: dict[int, float] = {}
        for j, v in ea.items:
            merged[j] = merged.get(j, 0.0) + wa * v
        for j, v in ec.items:
            merged[j] = merged.get(j, 0.0) + wc * v
        items = list(merged.items())
        feats = [(name, wc * v) for name, v in ec.features]
        txt = self._items_text(items, "", "Đóng góp lớn nhất từ")
        return Explanation(self.name, float(self.rank_scores(history)[item]), "",
                           f"score = {self.w:.1f}·z(ALS) + {1 - self.w:.1f}·z(Content)", terms, items, feats,
                           text=f"{self.w:.0%} từ MF-ALS ({ea.score:.2f}★ dự đoán), {1 - self.w:.0%} từ nội dung. "
                                + (txt + ". " if txt else "") + ec.text)


# Siêu tham số chọn bằng `python -m he_goi_y.tune` (validation tách từ train, không chạm test)
BEST = {
    "ItemKNN": dict(k=20, shrink=10.0),
    "ALS": dict(k=32, reg=8.0),
    "EASE": dict(lam=300.0),
    "Hybrid": dict(w=0.6),
}


def build_all(train, ds, params=None) -> dict[str, Recommender]:
    p = {**BEST, **(params or {})}
    als = ALS(**p["ALS"]).fit(train, ds)
    content = ContentBased().fit(train, ds)
    models = [RandomRec().fit(train, ds), Popularity().fit(train, ds), DampedMean().fit(train, ds),
              BiasBaseline().fit(train, ds), ItemKNN(**p["ItemKNN"]).fit(train, ds), als,
              EASE(**p["EASE"]).fit(train, ds), content, Hybrid(als, content, **p["Hybrid"]).fit(train, ds)]
    return {m.name: m for m in models}
