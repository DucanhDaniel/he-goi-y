"""Demo UI: `uv run streamlit run src/he_goi_y/app.py`"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from he_goi_y import data  # noqa: E402
from he_goi_y.models import build_all  # noqa: E402

# Design tokens — đồng bộ với .streamlit/config.toml
BG, SURFACE, BORDER = "#F7F8FB", "#FFFFFF", "#E3E7EF"
TEXT, MUTED, ACCENT = "#0F172A", "#526079", "#D97706"
BLUE, RED, GRAY = "#2563EB", "#DC2626", "#94A3B8"
BASELINES = {"Random", "Popularity", "Top-rated", "Bias (μ+bu+bi)"}

st.set_page_config(page_title="Gợi ý phim — MovieLens", page_icon=":material/movie:", layout="wide")

pio.templates["cine"] = go.layout.Template(layout=dict(
    font=dict(family="Fira Sans, sans-serif", color=TEXT, size=13),
    title=dict(font=dict(size=15, color=TEXT), x=0, xanchor="left"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[BLUE, ACCENT, "#059669", RED, "#7C3AED", GRAY],
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, tickfont=dict(color=MUTED),
               ticklabelstandoff=8),
    legend=dict(font=dict(color=MUTED), bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(color=TEXT, family="Fira Sans")),
))
pio.templates.default = "plotly_white+cine"

st.html("""<style>
:root{--bg:#F7F8FB;--surface:#FFFFFF;--surface-2:#FFFFFF;--border:#E3E7EF;--border-hi:#C7CFDD;
  --text:#0F172A;--muted:#526079;--accent:#B45309;--data:#2563EB;--neg:#DC2626;--chip:#F1F4F9;
  --shadow:0 1px 2px rgba(15,23,42,.05);--shadow-hi:0 8px 20px rgba(15,23,42,.08);}
.block-container{padding-top:4.2rem;max-width:1440px}
.hero{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;
  padding:4px 0 18px;border-bottom:1px solid var(--border);margin-bottom:8px}
.hero h1{font-size:1.9rem;font-weight:700;margin:0;padding:0;letter-spacing:-.01em}
.hero p{color:var(--muted);margin:4px 0 0;font-size:.95rem}
.hero .model{font-family:'Fira Code',monospace;font-size:.82rem;color:var(--accent);
  border:1px solid #FCD9A8;background:#FFF7EB;padding:6px 12px;border-radius:999px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:4px 0 8px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow)}
.kpi .lbl{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.07em}
.kpi .val{font-size:1.45rem;font-weight:600;margin-top:2px;font-variant-numeric:tabular-nums;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi .val small{font-size:.85rem;color:var(--muted);font-weight:400}
.rec-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;margin-top:6px}
.rec{background:linear-gradient(180deg,var(--surface-2),var(--surface));border:1px solid var(--border);
  border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:10px;box-shadow:var(--shadow);
  transition:border-color .2s ease,transform .2s ease,box-shadow .2s ease}
.rec:hover{border-color:var(--border-hi);transform:translateY(-2px);box-shadow:var(--shadow-hi)}
.rec .top{display:flex;gap:12px;align-items:flex-start}
.rec .rank{flex:none;width:34px;height:34px;border-radius:9px;display:grid;place-items:center;
  font-family:'Fira Code',monospace;font-weight:500;font-size:.9rem;background:var(--chip);color:var(--muted)}
.rec:nth-child(-n+3) .rank{background:#FEF3C7;color:var(--accent)}
.rec .ttl{font-weight:600;font-size:1.02rem;line-height:1.3;color:var(--text)}
.rec .yr{color:var(--muted);font-weight:400;font-size:.88rem}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chips span{font-size:.72rem;color:#334155;background:var(--chip);border:1px solid var(--border);
  padding:2px 8px;border-radius:999px;white-space:nowrap}
.stats{display:flex;gap:16px;font-size:.84rem;color:var(--muted);font-variant-numeric:tabular-nums;flex-wrap:wrap}
.stats b{color:var(--text);font-weight:600}
.stats .star{color:var(--accent)}
.fit{display:flex;align-items:center;gap:10px;font-size:.75rem;color:var(--muted)}
.fit .bar{flex:1;height:6px;background:#E8ECF3;border-radius:999px;overflow:hidden}
.fit .bar i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#60A5FA,var(--data))}
.fit code{font-family:'Fira Code',monospace;color:var(--text);background:none;padding:0;font-size:.75rem}
.why{color:var(--muted);font-size:.84rem;line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;
  -webkit-box-orient:vertical;overflow:hidden;margin:0}
.rec .foot{margin-top:auto;display:flex;justify-content:flex-end}
.rec a.imdb{font-size:.8rem;font-weight:600;color:#1D4ED8;text-decoration:none;padding:6px 10px;
  border-radius:8px;border:1px solid var(--border)}
.rec a.imdb:hover{border-color:#1D4ED8;background:#EFF4FF}
.rec a.imdb:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.liked{display:flex;flex-direction:column;gap:6px;margin-top:6px}
.liked div{display:flex;justify-content:space-between;gap:12px;font-size:.88rem;padding:7px 10px;
  border-radius:8px;background:var(--surface);border:1px solid var(--border)}
.liked div span:last-child{color:var(--accent);font-variant-numeric:tabular-nums;white-space:nowrap}
.formula{background:#FFFBF2;border:1px solid var(--border);border-left:3px solid var(--accent);
  border-radius:10px;padding:12px 16px;margin:4px 0 8px}
.formula .lbl{font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.formula code{font-family:'Fira Code',monospace;color:var(--accent);background:none;font-size:.92rem}
.formula p{margin:8px 0 0;color:var(--text);line-height:1.6}
.side-desc{font-size:.8rem;color:var(--muted);line-height:1.5;padding:10px 12px;border-radius:8px;
  background:var(--chip);border:1px solid var(--border);margin-top:-6px}
@media (prefers-reduced-motion:reduce){.rec{transition:none}.rec:hover{transform:none}}
</style>""")


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


def pretty(title: str) -> str:
    """'Matrix, The (1999)' -> 'The Matrix'."""
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", title)
    m = re.match(r"^(.*), (The|A|An|Les|La|Le|L'|Il|Das|Der|Die|El)$", t)
    return f"{m[2]} {m[1]}" if m else t


def chart(fig, where=st):
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    where.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def kpis(items):
    cells = "".join(f'<div class="kpi"><div class="lbl">{html.escape(k)}</div>'
                    f'<div class="val" title="{html.escape(str(v))}">{v}</div></div>' for k, v in items)
    st.html(f'<div class="kpis">{cells}</div>')


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
        "i": top,
        "Phim": M["title"].to_numpy()[top],
        "Thể loại": M["genres"].to_numpy()[top].astype(str),
        "Điểm xếp hạng": sc[top].round(3),
        "Rating dự đoán": pr[top].round(2) if pr is not None else np.nan,
        "TB cộng đồng": stats["avg"].to_numpy()[top].round(2),
        "Số lượt": stats["n"].to_numpy()[top],
        "Giải thích": [m.explain(history, int(i)).text for i in top] if explain else "",
        "IMDb": stats["imdb"].to_numpy()[top],
    })


COLCFG = {"i": None,
          "IMDb": st.column_config.LinkColumn("IMDb", display_text="Mở IMDb"),
          "Rating dự đoán": st.column_config.NumberColumn(format="%.2f ★"),
          "TB cộng đồng": st.column_config.NumberColumn(format="%.2f ★"),
          "Giải thích": st.column_config.TextColumn(width="large")}


def rec_cards(recs):
    s = recs["Điểm xếp hạng"].to_numpy()
    lo, hi = (s.min(), s.max()) if len(s) else (0, 1)
    cards = []
    for k, row in enumerate(recs.itertuples(index=False), 1):
        fit = 100 if hi == lo else 12 + 88 * (row[3] - lo) / (hi - lo)
        year = M["year"][row.i]
        chips = "".join(f"<span>{html.escape(g)}</span>" for g in row[2].split("|")[:4])
        pred = row[4]
        pred_html = (f'<span>Dự đoán <b class="star">{pred:.2f}★</b></span>'
                     if pd.notna(pred) else "")
        why = html.escape(row[7]) if row[7] else ""
        cards.append(f"""<article class="rec">
  <div class="top"><div class="rank" aria-label="Hạng {k}">{k}</div>
    <div><div class="ttl">{html.escape(pretty(row[1]))}</div>
    <div class="yr">{'' if pd.isna(year) else int(year)}</div></div></div>
  <div class="chips">{chips}</div>
  <div class="stats">{pred_html}<span>Cộng đồng <b>{row[5]:.2f}★</b></span>
    <span><b>{row[6]:,}</b> lượt</span></div>
  <div class="fit"><span>Phù hợp</span><div class="bar" role="img"
    aria-label="Mức phù hợp {fit:.0f}%"><i style="width:{fit:.0f}%"></i></div><code>{row[3]:.3f}</code></div>
  {f'<p class="why" title="{why}">{why}</p>' if why else ''}
  <div class="foot"><a class="imdb" href="{html.escape(row[8])}" target="_blank" rel="noopener"
    aria-label="Mở {html.escape(pretty(row[1]))} trên IMDb">IMDb ↗</a></div>
</article>""")
    st.html(f'<div class="rec-grid">{"".join(cards)}</div>')


def show_explanation(e, top_items=8):
    """Waterfall: các thành phần cộng dồn ra đúng điểm mô hình."""
    st.html(f'<div class="formula"><div class="lbl">Công thức</div><code>{html.escape(e.formula)}</code>'
            f'<p>{html.escape(e.text)}</p></div>')
    if e.score <= -1e8:
        return
    items = sorted(e.items, key=lambda p: -abs(p[1]))
    shown, rest = items[:top_items], items[top_items:]
    labels = [lab for lab, _ in e.terms] + [pretty(titles[j]) for j, _ in shown]
    vals = [v for _, v in e.terms] + [v for _, v in shown]
    if rest:
        labels.append(f"{len(rest)} phim khác trong lịch sử")
        vals.append(sum(v for _, v in rest))
    labels.append("<b>= Điểm mô hình</b>")
    fmt = ".3f"
    fig = go.Figure(go.Waterfall(
        orientation="h", y=labels, x=vals + [e.score], measure=["relative"] * len(vals) + ["total"],
        text=[f"{v:+{fmt}}" for v in vals] + [f"{e.score:{fmt}}{e.unit}"], textposition="outside",
        cliponaxis=False, textfont=dict(family="Fira Code, monospace", size=12, color=TEXT),
        increasing={"marker": {"color": BLUE}}, decreasing={"marker": {"color": RED}},
        totals={"marker": {"color": ACCENT}}, connector={"line": {"width": 1, "color": BORDER}}))
    fig.update_layout(height=max(260, 34 * len(labels) + 60), margin=dict(l=0, r=70, t=10, b=0),
                      yaxis={"autorange": "reversed"}, showlegend=False)
    chart(fig)
    ok = abs(e.total() - e.score) < 1e-6
    st.caption(f"{':material/check_circle:' if ok else ':material/error:'} Tổng các thành phần = "
               f"{e.total():.4f} = điểm mô hình {e.score:.4f} — giải thích là phân rã chính xác, "
               "không phải ước lượng.")
    c1, c2 = st.columns(2)
    if e.items:
        tb = pd.DataFrame({"Phim đã xem": [titles[j] for j, _ in items],
                           "Bạn chấm": [history.get(j) for j, _ in items],
                           "Đóng góp": [round(v, 4) for _, v in items]})
        c1.markdown("**Đóng góp của từng phim trong lịch sử**")
        c1.dataframe(tb, hide_index=True, width="stretch", height=280,
                     column_config={"Bạn chấm": st.column_config.NumberColumn(format="%.1f ★")})
    if e.features:
        f = pd.DataFrame(e.features, columns=["Đặc trưng", "Đóng góp"])
        f = f.reindex(f["Đóng góp"].abs().sort_values(ascending=False).index).head(10)
        c2.markdown("**Đóng góp theo đặc trưng nội dung**")
        c2.dataframe(f.round(4), hide_index=True, width="stretch", height=280)


# ───────── Sidebar ─────────
with st.sidebar:
    st.markdown("### :material/movie: Hệ gợi ý phim")
    st.caption("MovieLens · 9 mô hình")
    st.markdown("##### :material/person: Người xem")
    mode = st.segmented_control("Người dùng", ["Có sẵn", "Người mới"], default="Có sẵn",
                                label_visibility="collapsed") or "Có sẵn"
    history: dict[int, float] = {}
    if mode == "Có sẵn":
        uid = st.selectbox("User ID (MovieLens)", ds.user_ids, index=0)
        g = ds.ratings[ds.ratings["userId"] == uid]
        history = dict(zip(g["i"], g["rating"]))
    else:
        st.caption("Chọn phim bạn thích / không thích — cold-start fold-in, không cần train lại.")
        pop_order = np.argsort(-stats["n"].to_numpy())
        opts = [titles[i] for i in pop_order]
        liked = st.multiselect(":material/thumb_up: Thích (5★)", opts,
                               default=["Matrix, The (1999)", "Inception (2010)", "Interstellar (2014)"])
        disliked = st.multiselect(":material/thumb_down: Không thích (1★)", opts)
        idx = {t: i for i, t in enumerate(titles)}
        history = {idx[t]: 5.0 for t in liked} | {idx[t]: 1.0 for t in disliked}

    st.markdown("##### :material/model_training: Mô hình")
    model_name = st.selectbox("Mô hình", list(models), index=list(models).index("EASE (implicit)"),
                              label_visibility="collapsed")
    st.html(f'<div class="side-desc">{html.escape(models[model_name].desc)}</div>')

    st.markdown("##### :material/tune: Bộ lọc")
    n = st.slider("Số phim gợi ý (top-N)", 5, 30, 12)
    genres = sorted({x for s in M["genres"] for x in s.split("|")} - {"(no genres listed)"})
    genre = st.selectbox("Thể loại", ["Tất cả"] + genres)
    genre = None if genre == "Tất cả" else genre
    min_votes = st.number_input("Tối thiểu số lượt đánh giá", 0, 200, 0, step=5)

# ───────── Header ─────────
who = f"User #{uid}" if mode == "Có sẵn" else "Người dùng mới"
st.html(f'<header class="hero"><div><h1>Gợi ý phim cho {html.escape(who)}</h1>'
        f'<p>Mọi gợi ý đều kèm giải thích là phân rã chính xác điểm số của mô hình.</p></div>'
        f'<span class="model">{html.escape(model_name)}</span></header>')

tab_rec, tab_cmp, tab_sim, tab_eval, tab_data = st.tabs([
    ":material/auto_awesome: Gợi ý", ":material/compare_arrows: So sánh mô hình",
    ":material/hub: Phim tương tự", ":material/leaderboard: Kết quả đánh giá",
    ":material/database: Dữ liệu"])

# ───────── Gợi ý ─────────
with tab_rec:
    liked_genres = pd.Series([x for i, r in history.items() if r >= 4 for x in M["genres"][i].split("|")])
    rvals = list(history.values())
    kpis([("Phim đã chấm", f"{len(history):,}"),
          ("Rating trung bình", f"{np.mean(rvals):.2f}<small> ★</small>" if rvals else "—"),
          ("Thể loại yêu thích", html.escape(liked_genres.value_counts().index[0]) if len(liked_genres) else "—"),
          ("Phim chấm ≥ 4★", f"{sum(r >= 4 for r in rvals):,}")])

    recs = recommend(model_name, history, n, genre, min_votes)
    head, view_col = st.columns([4, 1], vertical_alignment="bottom")
    head.subheader(f":material/auto_awesome: Top-{len(recs)} gợi ý"
                   + (f" · {genre}" if genre else ""))
    view = view_col.segmented_control("Hiển thị", [":material/grid_view: Thẻ", ":material/table_rows: Bảng"],
                                      default=":material/grid_view: Thẻ", label_visibility="collapsed")
    if not history and model_name not in BASELINES:
        st.info("Chưa có lịch sử → mô hình cá nhân hoá rơi về baseline. Hãy chọn vài phim ở thanh bên.",
                icon=":material/info:")
    if recs.empty:
        st.warning("Không có phim nào thoả bộ lọc. Hãy nới điều kiện thể loại / số lượt đánh giá.",
                   icon=":material/filter_alt_off:")
    elif view and "Bảng" in view:
        st.dataframe(recs, hide_index=True, column_config=COLCFG, width="stretch")
    else:
        rec_cards(recs)

    st.space("medium")
    st.subheader(":material/person_search: Hồ sơ người xem")
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        st.markdown("**Phim được chấm cao nhất**")
        top_h = sorted(history.items(), key=lambda p: -p[1])[:6]
        if top_h:
            st.html('<div class="liked">' + "".join(
                f"<div><span>{html.escape(pretty(titles[i]))}</span><span>{r:.1f}★</span></div>"
                for i, r in top_h) + "</div>")
        with st.expander(f"Toàn bộ lịch sử ({len(history)} phim)", icon=":material/history:"):
            h = pd.DataFrame({"Phim": [titles[i] for i in history], "Rating": list(history.values()),
                              "Thể loại": [M["genres"][i] for i in history]})
            st.dataframe(h.sort_values("Rating", ascending=False), hide_index=True, width="stretch",
                         height=320, column_config={"Rating": st.column_config.NumberColumn(format="%.1f ★")})
    with c2:
        if len(liked_genres):
            vc = liked_genres.value_counts().head(8).rename_axis("Thể loại").reset_index(name="Số phim")
            fig = px.bar(vc, x="Số phim", y="Thể loại", orientation="h", text="Số phim",
                         title="Thể loại trong các phim được chấm ≥ 4★", color_discrete_sequence=[BLUE])
            fig.update_traces(textposition="outside", cliponaxis=False,
                              hovertemplate="%{y}: %{x} phim<extra></extra>")
            fig.update_layout(yaxis={"categoryorder": "total ascending", "title": None}, height=320,
                              xaxis={"title": None, "showgrid": False, "showticklabels": False},
                              margin=dict(l=0, r=30, t=40, b=0), bargap=0.35)
            chart(fig)
        else:
            st.caption("Chưa có phim nào được chấm ≥ 4★.")

    st.space("medium")
    st.subheader(":material/psychology_alt: Vì sao gợi ý phim này?")
    rec_titles = recs["Phim"].tolist()
    in_hist = {titles[i] for i in history}
    pick = st.selectbox("Chọn phim trong danh sách gợi ý, hoặc gõ tên phim bất kỳ để xem mô hình chấm nó thế nào",
                        rec_titles + [t for t in titles if t not in set(rec_titles) | in_hist])
    with st.container(border=True):
        show_explanation(models[model_name].explain(history, titles.index(pick)))

# ───────── So sánh ─────────
with tab_cmp:
    st.subheader("Top-10 của từng mô hình cho cùng người dùng")
    st.caption("Cùng lịch sử và bộ lọc ở thanh bên; khác biệt chỉ đến từ mô hình.")
    cols = {name: recommend(name, history, 10, genre, min_votes, explain=False)["Phim"].tolist()
            for name in models}
    st.dataframe(pd.DataFrame({k: v + [""] * (10 - len(v)) for k, v in cols.items()},
                 index=pd.Index(range(1, 11), name="#")), width="stretch")
    names = list(models)
    ov = pd.DataFrame([[len(set(cols[a]) & set(cols[b])) for b in names] for a in names],
                      index=names, columns=names)
    fig = px.imshow(ov, text_auto=True, color_continuous_scale=["#F1F4F9", "#93B4F5", BLUE],
                    title="Số phim trùng nhau trong top-10 giữa các mô hình")
    fig.update_layout(height=540, coloraxis_colorbar=dict(title=None, outlinewidth=0))
    fig.update_traces(hovertemplate="%{y} ∩ %{x}: %{z} phim<extra></extra>")
    chart(fig)

# ───────── Tương tự ─────────
with tab_sim:
    st.subheader("Phim tương tự (item-to-item)")
    q = st.selectbox("Chọn phim", titles, index=titles.index("Toy Story (1995)"))
    qi = titles.index(q)
    c1, c2, c3 = st.columns(3)
    knn = models["Item-kNN"].S.getrow(qi)
    o = np.argsort(-knn.data)[:10]
    prog = lambda lab, mx: st.column_config.ProgressColumn(lab, format="%.3f", min_value=0,  # noqa: E731
                                                          max_value=float(mx) if mx > 0 else 1.0)
    with c1.container(border=True):
        st.markdown("**Item-kNN**")
        st.caption("Được chấm điểm tương tự nhau")
        d = pd.DataFrame({"Phim": [titles[j] for j in knn.indices[o]], "sim": knn.data[o].round(3)})
        st.dataframe(d, hide_index=True, width="stretch",
                     column_config={"sim": prog("sim", d["sim"].max() if len(d) else 1)})
    e = models["EASE (implicit)"]
    if e.col[qi] >= 0:
        w = e.B[e.col[qi]]
        o = np.argsort(-w)[:10]
        with c2.container(border=True):
            st.markdown("**EASE**")
            st.caption("Thường được xem cùng")
            d = pd.DataFrame({"Phim": [titles[j] for j in e.items[o]], "w": w[o].round(4)})
            st.dataframe(d, hide_index=True, width="stretch",
                         column_config={"w": prog("w", d["w"].max())})
    X = models["Content-based"].X
    s = np.asarray((X @ X[qi].T).todense()).ravel()
    s[qi] = -1
    o = np.argsort(-s)[:10]
    with c3.container(border=True):
        st.markdown("**Content-based**")
        st.caption("Thể loại + tag + thập niên")
        d = pd.DataFrame({"Phim": [titles[j] for j in o], "cos": s[o].round(3)})
        st.dataframe(d, hide_index=True, width="stretch",
                     column_config={"cos": prog("cos", d["cos"].max())})

# ───────── Đánh giá ─────────
with tab_eval:
    path = data.ROOT / "results" / "metrics.csv"
    if not path.exists():
        st.warning("Chưa có kết quả. Chạy: `uv run python -m he_goi_y.evaluate`", icon=":material/warning:")
    else:
        res = pd.read_csv(path)
        st.caption("Chia tập theo thời gian: 20% rating mới nhất của mỗi user làm test. "
                   "Phim 'phù hợp' = rating test ≥ 4. Xếp hạng trên toàn bộ phim chưa xem. "
                   "Ô tô vàng = tốt nhất theo cột.")
        best = "background-color: #FEF3C7; color: #92400E; font-weight: 600"
        st.dataframe(res.drop(columns="sec").style.format(precision=4, na_rep="—")
                     .highlight_max(subset=[c for c in res.columns if "@" in c], props=best)
                     .highlight_min(subset=["RMSE", "MAE"], props=best),
                     hide_index=True, width="stretch")
        metric = st.segmented_control("Chỉ số", ["NDCG@10", "Precision@10", "Recall@10", "HitRate@10",
                                                 "RMSE", "Coverage", "Novelty"], default="NDCG@10") or "NDCG@10"
        d = res.dropna(subset=[metric]).assign(
            Loại=lambda x: np.where(x["model"].isin(BASELINES), "Baseline", "Mô hình đề xuất"))
        asc = metric != "RMSE"
        fig = px.bar(d.sort_values(metric, ascending=asc), x=metric, y="model", color="Loại",
                     orientation="h", text_auto=".4f",
                     color_discrete_map={"Baseline": GRAY, "Mô hình đề xuất": BLUE})
        fig.update_traces(textposition="outside", cliponaxis=False,
                          textfont=dict(family="Fira Code, monospace", size=11))
        fig.update_layout(height=440, bargap=0.35, yaxis_title=None, margin=dict(l=0, r=60, t=20, b=0),
                          legend=dict(orientation="h", y=1.08, x=0, title=None))
        chart(fig)
        if metric == "RMSE":
            st.caption("RMSE: càng thấp càng tốt — mô hình tốt nhất ở trên cùng.")

# ───────── Dữ liệu ─────────
with tab_data:
    r = ds.ratings
    kpis([("Ratings", f"{len(r):,}"), ("Users", f"{ds.n_users:,}"), ("Movies", f"{ds.n_items:,}"),
          ("Độ thưa (sparsity)", f"{1 - len(r) / (ds.n_users * ds.n_items):.2%}")])
    c1, c2 = st.columns(2)
    vc = r["rating"].value_counts().sort_index().rename_axis("rating").reset_index(name="count")
    fig = px.bar(vc, x="rating", y="count", title="Phân phối điểm rating", color_discrete_sequence=[BLUE])
    fig.update_layout(bargap=0.3)
    chart(fig, c1)
    pc = np.sort(stats["n"].to_numpy())[::-1]
    fig = px.line(x=np.arange(1, len(pc) + 1), y=pc, log_y=True,
                  labels={"x": "Thứ hạng phim", "y": "Số rating (log)"},
                  title="Long-tail: số rating mỗi phim", color_discrete_sequence=[ACCENT])
    chart(fig, c2)
    c1, c2 = st.columns(2)
    upc = r.groupby("userId").size()
    fig = px.histogram(upc, nbins=60, log_y=True, title="Số rating mỗi user",
                       labels={"value": "Số rating"}, color_discrete_sequence=[BLUE])
    fig.update_layout(showlegend=False, bargap=0.1)
    chart(fig, c1)
    gcount = M["genres"].str.split("|").explode().value_counts().rename_axis("genre").reset_index(name="n")
    fig = px.bar(gcount, x="n", y="genre", orientation="h", title="Số phim theo thể loại",
                 color_discrete_sequence=[BLUE])
    fig.update_layout(yaxis={"categoryorder": "total ascending", "title": None}, height=500, bargap=0.3)
    chart(fig, c2)
