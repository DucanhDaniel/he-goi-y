"""Demo UI: `uv run streamlit run src/he_goi_y/app.py`"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from he_goi_y import data  # noqa: E402
from he_goi_y.models import build_all  # noqa: E402

BLUE, RED, GRAY = "#2a78d6", "#e34948", "#9a9893"
BASELINES = {"Random", "Popularity", "Top-rated", "Bias (μ+bu+bi)"}

st.set_page_config(page_title="Gợi ý phim — MovieLens", page_icon="🎬", layout="wide")


@st.cache_resource(show_spinner="Đang huấn luyện các mô hình trên toàn bộ dữ liệu…")
def load_all():
    ds = data.load()
    models = build_all(ds.ratings, ds)  # demo: fit trên toàn bộ rating
    r = ds.ratings
    stats = pd.DataFrame({
        "n": np.bincount(r["i"], minlength=ds.n_items),
        "avg": np.bincount(r["i"], weights=r["rating"], minlength=ds.n_items)
        / np.maximum(np.bincount(r["i"], minlength=ds.n_items), 1),
    })
    imdb = ds.movies["movieId"].map(ds.links.set_index("movieId")["imdbId"])
    stats["imdb"] = "https://www.imdb.com/title/tt" + imdb.fillna("")
    return ds, models, stats


ds, models, stats = load_all()
M = ds.movies
titles = M["title"].tolist()


def recommend(model_name, history, n, genre=None, min_votes=0, explain=True):
    m = models[model_name]
    sc = np.array(m.rank_scores(history), dtype=float)
    pr = m.predict_ratings(history)
    mask = np.ones(ds.n_items, bool)
    mask[list(history)] = False
    if genre:
        mask &= M["genres"].str.contains(genre, regex=False).to_numpy()
    if min_votes:
        mask &= stats["n"].to_numpy() >= min_votes
    sc[~mask] = -np.inf
    top = np.argsort(-sc)[:n]
    top = top[np.isfinite(sc[top])]
    return pd.DataFrame({
        "Phim": M["title"].to_numpy()[top],
        "Thể loại": M["genres"].to_numpy()[top].astype(str),
        "Điểm xếp hạng": sc[top].round(3),
        "Rating dự đoán": pr[top].round(2) if pr is not None else np.nan,
        "TB cộng đồng": stats["avg"].to_numpy()[top].round(2),
        "Số lượt": stats["n"].to_numpy()[top],
        "Giải thích": [m.explain(history, int(i)).text for i in top] if explain else "",
        "IMDb": stats["imdb"].to_numpy()[top],
    })


COLCFG = {"IMDb": st.column_config.LinkColumn("IMDb", display_text="mở"),
          "Rating dự đoán": st.column_config.NumberColumn(format="%.2f ★"),
          "Giải thích": st.column_config.TextColumn(width="large")}


def show_explanation(e, top_items=8):
    """Waterfall: các thành phần cộng dồn ra đúng điểm mô hình."""
    st.markdown(f"**Công thức:** `{e.formula}`")
    st.write(e.text)
    if e.score <= -1e8:
        return
    items = sorted(e.items, key=lambda p: -abs(p[1]))
    shown, rest = items[:top_items], items[top_items:]
    labels = [lab for lab, _ in e.terms] + [f"🎬 {titles[j]}" for j, _ in shown]
    vals = [v for _, v in e.terms] + [v for _, v in shown]
    if rest:
        labels.append(f"🎬 {len(rest)} phim khác trong lịch sử")
        vals.append(sum(v for _, v in rest))
    labels.append("= Điểm mô hình")
    fmt = ".3f"
    fig = go.Figure(go.Waterfall(
        orientation="h", y=labels, x=vals + [e.score], measure=["relative"] * len(vals) + ["total"],
        text=[f"{v:+{fmt}}" for v in vals] + [f"{e.score:{fmt}}{e.unit}"], textposition="outside",
        increasing={"marker": {"color": BLUE}}, decreasing={"marker": {"color": RED}},
        totals={"marker": {"color": GRAY}}, connector={"line": {"width": 1, "color": GRAY}}))
    fig.update_layout(height=max(260, 34 * len(labels) + 60), margin=dict(l=0, r=40, t=10, b=0),
                      yaxis={"autorange": "reversed"}, showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Tổng các thành phần = {e.total():.4f} = điểm mô hình {e.score:.4f} "
               f"{'✓' if abs(e.total() - e.score) < 1e-6 else '✗'} — giải thích là phân rã chính xác, "
               "không phải ước lượng.")
    c1, c2 = st.columns(2)
    if e.items:
        tb = pd.DataFrame({"Phim đã xem": [titles[j] for j, _ in items],
                           "Bạn chấm": [history.get(j) for j, _ in items],
                           "Đóng góp": [round(v, 4) for _, v in items]})
        c1.markdown("**Đóng góp của từng phim trong lịch sử**")
        c1.dataframe(tb, hide_index=True, width="stretch", height=280)
    if e.features:
        f = pd.DataFrame(e.features, columns=["Đặc trưng", "Đóng góp"])
        f = f.reindex(f["Đóng góp"].abs().sort_values(ascending=False).index).head(10)
        c2.markdown("**Đóng góp theo đặc trưng nội dung**")
        c2.dataframe(f.round(4), hide_index=True, width="stretch", height=280)

# ───────── Sidebar ─────────
st.sidebar.title("🎬 Hệ gợi ý phim")
mode = st.sidebar.radio("Người dùng", ["User có sẵn (MovieLens)", "Người dùng mới (tự chấm điểm)"])
history: dict[int, float] = {}
if mode.startswith("User"):
    uid = st.sidebar.selectbox("userId", ds.user_ids, index=0)
    g = ds.ratings[ds.ratings["userId"] == uid]
    history = dict(zip(g["i"], g["rating"]))
else:
    st.sidebar.caption("Chọn phim bạn thích / không thích (cold-start fold-in, không cần train lại).")
    pop_order = np.argsort(-stats["n"].to_numpy())
    opts = [titles[i] for i in pop_order]
    liked = st.sidebar.multiselect("👍 Thích (5★)", opts,
                                   default=["Matrix, The (1999)", "Inception (2010)", "Interstellar (2014)"])
    disliked = st.sidebar.multiselect("👎 Không thích (1★)", opts)
    idx = {t: i for i, t in enumerate(titles)}
    history = {idx[t]: 5.0 for t in liked} | {idx[t]: 1.0 for t in disliked}

model_name = st.sidebar.selectbox("Mô hình", list(models), index=list(models).index("EASE (implicit)"))
st.sidebar.caption(models[model_name].desc)
n = st.sidebar.slider("Số phim gợi ý (top-N)", 5, 30, 10)
genres = sorted({x for s in M["genres"] for x in s.split("|")} - {"(no genres listed)"})
genre = st.sidebar.selectbox("Lọc thể loại", ["(tất cả)"] + genres)
genre = None if genre == "(tất cả)" else genre
min_votes = st.sidebar.number_input("Tối thiểu số lượt đánh giá", 0, 200, 0)

tab_rec, tab_cmp, tab_sim, tab_eval, tab_data = st.tabs(
    ["⭐ Gợi ý", "⚖️ So sánh mô hình", "🔗 Phim tương tự", "📊 Kết quả đánh giá", "🗂️ Dữ liệu"])

# ───────── Gợi ý ─────────
with tab_rec:
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader(f"Top-{n} gợi ý — {model_name}")
        if not history and model_name not in {"Random", "Popularity", "Top-rated", "Bias (μ+bu+bi)"}:
            st.info("Chưa có lịch sử → mô hình cá nhân hoá rơi về baseline. Hãy chọn vài phim ở thanh bên.")
        recs = recommend(model_name, history, n, genre, min_votes)
        st.dataframe(recs, hide_index=True, column_config=COLCFG, width="stretch")
    with c2:
        st.subheader(f"Lịch sử ({len(history)} phim)")
        h = pd.DataFrame({"Phim": [titles[i] for i in history], "Rating": list(history.values()),
                          "Thể loại": [M["genres"][i] for i in history]})
        st.dataframe(h.sort_values("Rating", ascending=False), hide_index=True,
                     width="stretch", height=380)
        if history:
            gc = pd.Series([x for i, r in history.items() if r >= 4 for x in M["genres"][i].split("|")])
            if len(gc):
                vc = gc.value_counts().head(8).rename_axis("Thể loại").reset_index(name="Số phim")
                fig = px.bar(vc, x="Số phim", y="Thể loại", orientation="h",
                             title="Thể loại trong các phim được chấm ≥ 4★",
                             color_discrete_sequence=[BLUE])
                fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=300,
                                  margin=dict(l=0, r=0, t=40, b=0), bargap=0.35)
                st.plotly_chart(fig, width="stretch")

    st.subheader("🔍 Vì sao gợi ý phim này?")
    rec_titles = recs["Phim"].tolist()
    in_hist = {titles[i] for i in history}
    pick = st.selectbox("Chọn phim trong danh sách gợi ý (hoặc gõ tên phim bất kỳ để xem mô hình chấm nó thế nào)",
                        rec_titles + [t for t in titles if t not in set(rec_titles) | in_hist])
    show_explanation(models[model_name].explain(history, titles.index(pick)))

# ───────── So sánh ─────────
with tab_cmp:
    st.subheader("Top-10 của từng mô hình cho cùng người dùng")
    cols = {name: recommend(name, history, 10, genre, min_votes, explain=False)["Phim"].tolist()
            for name in models}
    st.dataframe(pd.DataFrame({k: v + [""] * (10 - len(v)) for k, v in cols.items()},
                 index=range(1, 11)), width="stretch")
    names = list(models)
    ov = pd.DataFrame([[len(set(cols[a]) & set(cols[b])) for b in names] for a in names],
                      index=names, columns=names)
    fig = px.imshow(ov, text_auto=True, color_continuous_scale=["#f0efec", "#86b6ef", "#1c5cab"],
                    title="Số phim trùng nhau trong top-10 giữa các mô hình")
    fig.update_layout(height=520)
    st.plotly_chart(fig, width="stretch")

# ───────── Tương tự ─────────
with tab_sim:
    st.subheader("Phim tương tự (item-to-item)")
    q = st.selectbox("Chọn phim", titles, index=titles.index("Toy Story (1995)"))
    qi = titles.index(q)
    c1, c2, c3 = st.columns(3)
    knn = models["Item-kNN"].S.getrow(qi)
    o = np.argsort(-knn.data)[:10]
    c1.markdown("**Item-kNN** (cùng được chấm điểm tương tự)")
    c1.dataframe(pd.DataFrame({"Phim": [titles[j] for j in knn.indices[o]], "sim": knn.data[o].round(3)}),
                 hide_index=True, width="stretch")
    e = models["EASE (implicit)"]
    if e.col[qi] >= 0:
        w = e.B[e.col[qi]]
        o = np.argsort(-w)[:10]
        c2.markdown("**EASE** (thường được xem cùng)")
        c2.dataframe(pd.DataFrame({"Phim": [titles[j] for j in e.items[o]], "w": w[o].round(4)}),
                     hide_index=True, width="stretch")
    X = models["Content-based"].X
    s = np.asarray((X @ X[qi].T).todense()).ravel()
    s[qi] = -1
    o = np.argsort(-s)[:10]
    c3.markdown("**Content-based** (thể loại + tag + thập niên)")
    c3.dataframe(pd.DataFrame({"Phim": [titles[j] for j in o], "cos": s[o].round(3)}),
                 hide_index=True, width="stretch")

# ───────── Đánh giá ─────────
with tab_eval:
    path = data.ROOT / "results" / "metrics.csv"
    if not path.exists():
        st.warning("Chưa có kết quả. Chạy: `uv run python -m he_goi_y.evaluate`")
    else:
        res = pd.read_csv(path)
        st.caption("Chia tập theo thời gian: 20% rating mới nhất của mỗi user làm test. "
                   "Phim 'phù hợp' = rating test ≥ 4. Xếp hạng trên toàn bộ phim chưa xem.")
        st.dataframe(res.drop(columns="sec").style.format(precision=4)
                     .highlight_max(subset=[c for c in res.columns if "@" in c], color="#cde2fb")
                     .highlight_min(subset=["RMSE", "MAE"], color="#cde2fb"),
                     hide_index=True, width="stretch")
        metric = st.radio("Chỉ số", ["NDCG@10", "Precision@10", "Recall@10", "HitRate@10", "RMSE",
                                    "Coverage", "Novelty"], horizontal=True)
        d = res.dropna(subset=[metric]).assign(
            Loại=lambda x: np.where(x["model"].isin(BASELINES), "Baseline", "Mô hình đề xuất"))
        fig = px.bar(d.sort_values(metric), x=metric, y="model", color="Loại", orientation="h",
                     color_discrete_map={"Baseline": GRAY, "Mô hình đề xuất": BLUE}, text_auto=".4f")
        fig.update_layout(height=420, bargap=0.35, yaxis_title=None, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, width="stretch")

# ───────── Dữ liệu ─────────
with tab_data:
    r = ds.ratings
    a, b, c, d_ = st.columns(4)
    a.metric("Ratings", f"{len(r):,}")
    b.metric("Users", f"{ds.n_users:,}")
    c.metric("Movies", f"{ds.n_items:,}")
    d_.metric("Độ thưa (sparsity)", f"{1 - len(r) / (ds.n_users * ds.n_items):.2%}")
    c1, c2 = st.columns(2)
    vc = r["rating"].value_counts().sort_index().rename_axis("rating").reset_index(name="count")
    fig = px.bar(vc, x="rating", y="count", title="Phân phối điểm rating", color_discrete_sequence=[BLUE])
    fig.update_layout(bargap=0.3)
    c1.plotly_chart(fig, width="stretch")
    pc = np.sort(stats["n"].to_numpy())[::-1]
    fig = px.line(x=np.arange(1, len(pc) + 1), y=pc, log_y=True,
                  labels={"x": "Thứ hạng phim", "y": "Số rating (log)"},
                  title="Long-tail: số rating mỗi phim", color_discrete_sequence=[BLUE])
    c2.plotly_chart(fig, width="stretch")
    c1, c2 = st.columns(2)
    upc = r.groupby("userId").size()
    fig = px.histogram(upc, nbins=60, log_y=True, title="Số rating mỗi user",
                       labels={"value": "Số rating"}, color_discrete_sequence=[BLUE])
    fig.update_layout(showlegend=False, bargap=0.1)
    c1.plotly_chart(fig, width="stretch")
    gcount = M["genres"].str.split("|").explode().value_counts().rename_axis("genre").reset_index(name="n")
    fig = px.bar(gcount, x="n", y="genre", orientation="h", title="Số phim theo thể loại",
                 color_discrete_sequence=[BLUE])
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500, bargap=0.3)
    c2.plotly_chart(fig, width="stretch")
