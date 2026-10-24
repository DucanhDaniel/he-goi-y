"""Mô hình deep learning làm đối thủ mạnh (cần PyTorch, nên chạy trên GPU — xem notebooks/).

    LightGCN (He et al., SIGIR 2020): mạng đồ thị trên đồ thị user–phim, học bằng BPR.
    SASRec   (Kang & McAuley, ICDM 2018): Transformer trên chuỗi phim theo thời gian,
             học bằng cross-entropy trên toàn bộ phim.

Cùng giao diện `Recommender` với models.py, học trên phản hồi ngầm (đã chấm = 1) như EASE.
Đây là mô hình hộp đen: `explain` chỉ trả về điểm, không phân rã được thành đóng góp từng phim
— chính là điểm khác biệt so với các mô hình giải thích được của đề tài.

`history` phải theo thứ tự thời gian (temporal_split giữ thứ tự này) vì SASRec dùng thứ tự xem.
"""
from __future__ import annotations

import json

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .models import Explanation, Recommender


def _device(device=None):
    return torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))


def _seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)


class _BlackBox(Recommender):
    def explain(self, history, item):
        s = float(self.rank_scores(history)[item])
        return Explanation(self.name, s, "", "score = f(lịch sử) — mạng nơ-ron, không phân rã tuyến tính",
                           [("Điểm mô hình (hộp đen)", s)],
                           text="Mô hình hộp đen: chỉ có điểm tổng, không tách được đóng góp của từng phim đã xem.")


# ───────────────────────── LightGCN ─────────────────────────
class LightGCN(_BlackBox):
    name = "LightGCN"
    desc = "GNN trên đồ thị user–phim (He et al., 2020), học BPR trên phản hồi ngầm."
    uses_user_id = True  # evaluate truyền user=u; user mới thì fold-in qua lịch sử

    def __init__(self, dim=64, layers=3, epochs=300, lr=1e-3, reg=1e-4, batch=2048, seed=0, device=None):
        self.dim, self.layers, self.epochs, self.lr, self.reg = dim, layers, epochs, lr, reg
        self.batch, self.seed, self.device = batch, seed, _device(device)

    def fit(self, train, ds):
        super().fit(train, ds)
        _seed(self.seed)
        nu, ni, dev = ds.n_users, ds.n_items, self.device
        pairs = train[["u", "i"]].drop_duplicates().to_numpy().copy()
        u, i = pairs[:, 0], pairs[:, 1]
        # Ma trận kề chuẩn hoá D^-1/2 A D^-1/2 trên đồ thị hai phía (user: 0..nu-1, phim: nu..)
        rows = np.concatenate([u, i + nu])
        cols = np.concatenate([i + nu, u])
        deg = np.bincount(rows, minlength=nu + ni).astype(np.float32)
        val = 1.0 / np.sqrt(deg[rows] * deg[cols])
        A = torch.sparse_coo_tensor(np.vstack([rows, cols]), val.astype(np.float32),
                                    (nu + ni, nu + ni), check_invariants=True).coalesce().to(dev)
        E = nn.Embedding(nu + ni, self.dim).to(dev)
        nn.init.normal_(E.weight, std=0.1)
        opt = torch.optim.Adam(E.parameters(), lr=self.lr)
        tu = torch.as_tensor(u, device=dev)
        ti = torch.as_tensor(i, device=dev)

        for _ in range(self.epochs):
            perm = torch.randperm(len(tu), device=dev)
            for s in range(0, len(perm), self.batch):
                b = perm[s:s + self.batch]
                bu, bp = tu[b], ti[b]
                bn = torch.randint(0, ni, (len(b),), device=dev)  # âm ngẫu nhiên đều
                out = self._propagate(A, E.weight)
                eu, ep, en = out[bu], out[nu + bp], out[nu + bn]
                loss = -F.logsigmoid((eu * ep).sum(1) - (eu * en).sum(1)).mean()
                e0 = E.weight
                loss = loss + self.reg * (e0[bu].pow(2).sum() + e0[nu + bp].pow(2).sum()
                                          + e0[nu + bn].pow(2).sum()) / (2 * len(b))
                opt.zero_grad()
                loss.backward()
                opt.step()

        with torch.no_grad():
            layers = [E.weight.detach()]
            for _ in range(self.layers):
                layers.append(torch.sparse.mm(A, layers[-1]))
            final = torch.stack(layers).mean(0)
        self.user_emb = final[:nu].cpu().numpy()
        self.item_emb = final[nu:].cpu().numpy()
        self.item_layers = [x[nu:].cpu().numpy() for x in layers]
        self.item_deg = deg[nu:]
        return self

    def _propagate(self, A, E0):
        out, cur = E0, E0
        for _ in range(self.layers):
            cur = torch.sparse.mm(A, cur)
            out = out + cur
        return out / (self.layers + 1)

    def user_vector(self, history):
        """Fold-in cho người dùng mới: lan truyền một bước từ các phim trong lịch sử."""
        h = np.fromiter(history.keys(), int)
        if len(h) == 0:
            return np.zeros(self.dim, dtype=np.float32)
        w = 1.0 / np.sqrt(len(h) * np.maximum(self.item_deg[h], 1))
        layers = [self.item_layers[0][h].mean(0)]
        for k in range(self.layers):
            layers.append(w @ self.item_layers[k][h])
        return np.mean(layers, axis=0)

    def rank_scores(self, history, user=None):
        uvec = self.user_emb[user] if user is not None else self.user_vector(history)
        return self.item_emb @ uvec


# ───────────────────────── SASRec ─────────────────────────
class _SASRecNet(nn.Module):
    def __init__(self, n_items, dim, blocks, heads, dropout, max_len):
        super().__init__()
        self.item = nn.Embedding(n_items + 1, dim, padding_idx=0)  # 0 = padding, phim i -> i+1
        self.pos = nn.Embedding(max_len, dim)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList(
            nn.TransformerEncoderLayer(dim, heads, dim, dropout, batch_first=True, norm_first=True)
            for _ in range(blocks))
        self.norm = nn.LayerNorm(dim)
        self.dim = dim

    def forward(self, seq):  # seq: (B, L), đệm trái bằng 0
        L = seq.size(1)
        keep = (seq > 0).unsqueeze(-1).float()
        x = self.item(seq) * self.dim ** 0.5 + self.pos(torch.arange(L, device=seq.device))
        x = self.drop(x) * keep
        causal = torch.triu(torch.ones(L, L, dtype=torch.bool, device=seq.device), 1)
        for blk in self.blocks:
            x = blk(x, src_mask=causal) * keep
        return self.norm(x)

    def logits(self, h):  # điểm trên mọi phim (bỏ hàng padding)
        return h @ self.item.weight[1:].T


class SASRec(_BlackBox):
    name = "SASRec"
    desc = "Transformer trên chuỗi phim theo thời gian (Kang & McAuley, 2018)."

    def __init__(self, dim=64, blocks=2, heads=1, dropout=0.2, max_len=200, epochs=200, lr=1e-3,
                 batch=128, seed=0, device=None):
        self.dim, self.blocks, self.heads, self.dropout = dim, blocks, heads, dropout
        self.max_len, self.epochs, self.lr, self.batch = max_len, epochs, lr, batch
        self.seed, self.device = seed, _device(device)

    def _pad(self, seq):
        seq = seq[-self.max_len:]
        return [0] * (self.max_len - len(seq)) + seq

    def fit(self, train, ds):
        super().fit(train, ds)
        _seed(self.seed)
        dev = self.device
        # train đã sắp theo (u, timestamp) nên mỗi nhóm là chuỗi theo thời gian
        seqs = [(g + 1).tolist() for _, g in train.groupby("u", sort=False)["i"]]
        # Chuỗi dài được cắt thành nhiều cửa sổ max_len+1 phim; input = w[:-1], nhãn = w[1:]
        X, Y = [], []
        for s in seqs:
            for end in range(len(s), 1, -self.max_len):
                w = s[max(0, end - self.max_len - 1):end]
                X.append(self._pad(w[:-1]))
                Y.append(self._pad(w[1:]))
        X = torch.as_tensor(X, device=dev)
        Y = torch.as_tensor(Y, device=dev) - 1  # -1 = padding, bị bỏ qua trong loss
        self.net = _SASRecNet(ds.n_items, self.dim, self.blocks, self.heads, self.dropout,
                              self.max_len).to(dev)
        opt = torch.optim.Adam(self.net.parameters(), lr=self.lr, betas=(0.9, 0.98))
        for _ in range(self.epochs):
            self.net.train()
            perm = torch.randperm(len(X), device=dev)
            for s in range(0, len(perm), self.batch):
                b = perm[s:s + self.batch]
                y = Y[b]
                keep = y >= 0  # chỉ tính logits ở vị trí có nhãn: tiết kiệm bộ nhớ (n_items ~ 10k)
                logits = self.net.logits(self.net(X[b])[keep])
                loss = F.cross_entropy(logits, y[keep])
                opt.zero_grad()
                loss.backward()
                opt.step()
        self.net.eval()
        return self

    @torch.no_grad()
    def rank_scores(self, history):
        seq = [int(j) + 1 for j in history.keys()]
        x = torch.as_tensor([self._pad(seq)], device=self.device)
        return self.net.logits(self.net(x)[:, -1]).squeeze(0).cpu().numpy()


# Siêu tham số mặc định; `python -m he_goi_y.tune --deep` ghi kết quả tune vào results/best_deep.json
BEST_DEEP = {
    "LightGCN": dict(layers=3, epochs=300),
    "SASRec": dict(dropout=0.2, epochs=200),
}


def load_best(path):
    p = {k: dict(v) for k, v in BEST_DEEP.items()}
    if path.exists():
        for k, v in json.load(open(path, encoding="utf-8")).items():
            p[k].update(v)
    return p


def build_deep(train, ds, params=None, device=None) -> dict[str, Recommender]:
    p = params or BEST_DEEP
    models = [LightGCN(**p["LightGCN"], device=device).fit(train, ds),
              SASRec(**p["SASRec"], device=device).fit(train, ds)]
    return {m.name: m for m in models}
