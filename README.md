# Hệ gợi ý phim (MovieLens)

9 mô hình gợi ý (4 baseline + Item-kNN, MF-ALS, EASE, Content-based, Hybrid), đánh giá offline và UI demo Streamlit.
Báo cáo chi tiết về dataset, thuật toán, kỳ vọng và kết quả: [REPORT.md](REPORT.md).

```bash
uv sync
uv run python -m he_goi_y.evaluate        # đánh giá -> results/metrics.csv
uv run streamlit run src/he_goi_y/app.py  # demo UI
uv run python -m he_goi_y.tune            # (tuỳ chọn) tune siêu tham số trên validation
uv run pytest                             # kiểm tra giải thích cộng đúng bằng điểm mô hình
```

Hai mô hình deep learning làm đối thủ mạnh (LightGCN, SASRec, cần PyTorch) chạy trên GPU bằng
[notebooks/deep_models_colab.ipynb](notebooks/deep_models_colab.ipynb) (mở bằng Google Colab):
`python -m he_goi_y.tune --deep` rồi `python -m he_goi_y.evaluate --deep` → `results/metrics_deep.csv`.

Mọi gợi ý đều kèm giải thích: `model.explain(history, item)` phân rã chính xác điểm của mô hình thành các thành phần (bias, đóng góp của từng phim đã xem, đặc trưng nội dung). Xem REPORT.md mục 5.4.

Dữ liệu `ml-latest-small` được tải tự động vào `data/` khi chạy lần đầu.

| File | Nội dung |
|---|---|
| `src/he_goi_y/data.py` | Nạp dữ liệu, chia train/test theo thời gian |
| `src/he_goi_y/models.py` | Các mô hình, giao diện chung `predict_ratings` / `rank_scores` / `explain` |
| `src/he_goi_y/deep.py` | LightGCN, SASRec (PyTorch, hộp đen: không phân rã được giải thích) |
| `src/he_goi_y/evaluate.py` | RMSE, MAE, Precision/Recall/NDCG/HitRate@10, Coverage, Novelty |
| `src/he_goi_y/tune.py` | Grid search trên validation |
| `src/he_goi_y/app.py` | UI Streamlit |
