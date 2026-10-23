"""Nạp MovieLens (ml-latest-small), chia train/test theo thời gian."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ml-latest-small"
URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"


def ensure_data() -> Path:
    if (DATA_DIR / "ratings.csv").exists():
        return DATA_DIR
    import io
    import urllib.request
    import zipfile

    DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL) as r:
        zipfile.ZipFile(io.BytesIO(r.read())).extractall(DATA_DIR.parent)
    return DATA_DIR


@dataclass
class Dataset:
    ratings: pd.DataFrame  # userId, movieId, rating, timestamp, u, i
    movies: pd.DataFrame   # movieId, title, genres, year, i  (index = i)
    tags: pd.DataFrame
    links: pd.DataFrame
    n_users: int
    n_items: int
    user_ids: np.ndarray   # u -> userId
    movie_ids: np.ndarray  # i -> movieId


def load() -> Dataset:
    d = ensure_data()
    ratings = pd.read_csv(d / "ratings.csv")
    movies = pd.read_csv(d / "movies.csv")
    tags = pd.read_csv(d / "tags.csv")
    links = pd.read_csv(d / "links.csv", dtype={"imdbId": str})

    movies = movies.sort_values("movieId").reset_index(drop=True)
    movies["year"] = pd.to_numeric(movies["title"].str.extract(r"\((\d{4})\)\s*$")[0])
    movies["i"] = np.arange(len(movies))
    user_ids = np.sort(ratings["userId"].unique())
    u_map = {u: k for k, u in enumerate(user_ids)}
    i_map = dict(zip(movies["movieId"], movies["i"]))
    ratings = ratings.assign(u=ratings["userId"].map(u_map), i=ratings["movieId"].map(i_map))
    return Dataset(ratings, movies, tags, links, len(user_ids), len(movies),
                   user_ids, movies["movieId"].to_numpy())


def temporal_split(ratings: pd.DataFrame, test_frac: float = 0.2):
    """Mỗi user: phần cuối (theo thời gian) làm test. Tránh rò rỉ tương lai."""
    r = ratings.sort_values(["u", "timestamp", "i"]).copy()
    pos = r.groupby("u").cumcount()
    n = r.groupby("u")["i"].transform("size")
    is_test = pos >= np.floor(n * (1 - test_frac))
    return r[~is_test].reset_index(drop=True), r[is_test].reset_index(drop=True)
