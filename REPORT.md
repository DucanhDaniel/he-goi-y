# Báo cáo: Hệ gợi ý phim trên MovieLens

> Mọi con số trong báo cáo được sinh từ `uv run python -m he_goi_y.evaluate` (seed cố định, chạy lại cho ra cùng kết quả). Siêu tham số được chọn bằng `uv run python -m he_goi_y.tune` trên tập validation, **không chạm vào tập test**.

## 1. Bài toán

Cho lịch sử chấm điểm phim của người dùng, hệ thống cần:

1. **Top-N recommendation** (mục tiêu chính): đưa ra danh sách N phim người dùng *chưa xem* và nhiều khả năng sẽ thích.
2. **Rating prediction** (mục tiêu phụ): dự đoán điểm (0.5–5★) người dùng sẽ chấm cho một phim.

Hai mục tiêu này không trùng nhau: một mô hình dự đoán điểm tốt chưa chắc xếp hạng tốt (xem mục 5.3).

## 2. Dataset: MovieLens `ml-latest-small`

Nguồn: GroupLens Research, https://grouplens.org/datasets/movielens/ (tải tự động khi chạy lần đầu).

| File | Nội dung | Số dòng |
|---|---|---|
| `ratings.csv` | `userId, movieId, rating, timestamp` | 100,836 |
| `movies.csv` | `movieId, title (kèm năm), genres` (phân tách bằng `\|`) | 9,742 |
| `tags.csv` | `userId, movieId, tag, timestamp` (tag tự do do người dùng gắn) | 3,683 |
| `links.csv` | ánh xạ sang `imdbId`, `tmdbId` | 9,742 |

### 2.1 Thống kê chính

| Chỉ số | Giá trị |
|---|---|
| Số người dùng | 610 (mỗi người ≥ 20 rating) |
| Số phim | 9,742 (9,724 phim có ít nhất 1 rating) |
| Khoảng thời gian | 03/1996 – 09/2018 |
| Độ thưa của ma trận user×item | **98.30%** (chỉ 1.7% ô có giá trị) |
| Thang điểm | 0.5 → 5.0, bước 0.5 |
| Điểm trung bình / trung vị / độ lệch chuẩn | 3.50 / 3.5 / 1.04 |
| Rating mỗi user: min / trung vị / TB / max | 20 / 70.5 / 165.3 / 2,698 |
| Rating mỗi phim: trung vị / max | 3 / 329 |
| Phim chỉ có 1 rating | 3,446 (35%) |
| Phim có < 5 rating | 6,074 (62%) |
| Thể loại | 20 (một phim có thể nhiều thể loại) |
| Tag | 3,683 lượt, 1,589 tag khác nhau, trên 1,572 phim, do 58 user gắn |

Phân phối điểm: 0.5★ 1.4% · 1★ 2.8% · 1.5★ 1.8% · 2★ 7.5% · 2.5★ 5.5% · 3★ 19.9% · 3.5★ 13.0% · **4★ 26.6%** · 4.5★ 8.5% · 5★ 13.1%.

### 2.2 Đặc điểm ảnh hưởng tới thiết kế

- **Thưa và long-tail mạnh.** 10% phim phổ biến nhất chiếm 60% tổng rating; 1% phim chiếm 16%. Hệ quả: baseline Popularity sẽ rất khó đánh bại, và các phim đuôi dài gần như không đủ tín hiệu cho lọc cộng tác → cần regularization/shrinkage, và nội dung (thể loại, tag) có ích cho phim ít rating.
- **Thiên lệch điểm cao và số nguyên.** Người dùng ưa chấm 4★ và 3★; điểm nguyên phổ biến hơn nửa sao. Mỗi người cũng có "độ khó tính" riêng → mô hình cần tách **bias của user** và **bias của phim** (`μ + b_u + b_i`) trước khi học phần tương tác.
- **Hoạt động không đều giữa user.** Vài user có hàng nghìn rating; trung vị chỉ 70 → chỉ số được tính trung bình theo user (mỗi user một phiếu) để user nặng ký không chi phối kết quả.
- **Tag thưa.** Chỉ 16% phim có tag → tag chỉ là đặc trưng bổ sung cho thể loại, không thể là nguồn chính.

### 2.3 Tiền xử lý

- Ánh xạ `userId`, `movieId` sang chỉ số liên tục `u`, `i`.
- Trích năm phát hành từ tiêu đề (`"Toy Story (1995)"` → 1995), quy về thập niên làm đặc trưng nội dung.
- Không lọc user/phim: giữ nguyên để đánh giá trung thực trên cả đuôi dài.

### 2.4 Chia tập — theo thời gian, từng người dùng

Với **mỗi user**, sắp rating theo `timestamp`; **80% cũ nhất → train, 20% mới nhất → test**.

- Train: 80,419 rating · Test: 20,417 rating · cả 610 user đều có mặt ở test.
- Chia theo thời gian thay vì ngẫu nhiên để **không dùng tương lai đoán quá khứ**, sát với tình huống thực tế (gợi ý cho những gì người dùng sẽ xem *tiếp theo*). Cách chia này khó hơn chia ngẫu nhiên: 8.3% rating ở test thuộc về phim **chưa từng xuất hiện trong train** (item cold-start).
- **Validation** để tune: tách tiếp theo cùng quy tắc (20% cuối của phần train mỗi user).
- Một phim ở test được coi là **"phù hợp" (relevant) nếu rating ≥ 4★** (46.6% rating ở test).

## 3. Thuật toán

Tất cả mô hình dùng chung một giao diện (`src/he_goi_y/models.py`):

```
fit(train, dataset)
predict_ratings(history) -> điểm dự đoán cho mọi phim (hoặc None nếu mô hình không dự đoán điểm)
rank_scores(history)     -> điểm xếp hạng cho mọi phim (cao = nên gợi ý)
explain(history, item)   -> Explanation: phân rã chính xác điểm thành các thành phần + câu giải thích (mục 5.4)
```

`history = {phim: rating}` là lịch sử của người dùng. Vì user được biểu diễn qua lịch sử chứ không qua ID, **một người dùng mới có thể nhận gợi ý ngay mà không cần train lại** (fold-in) — UI dùng tính năng này.

### 3.1 Baseline

| # | Mô hình | Ý tưởng | Vai trò |
|---|---|---|---|
| B1 | **Random** | Xếp ngẫu nhiên | Mức sàn: mọi mô hình phải vượt xa |
| B2 | **Popularity** | Xếp theo số lượt rating trong train | Baseline không cá nhân hoá mạnh nhất trên dữ liệu long-tail |
| B3 | **Top-rated** | Điểm TB làm mịn Bayes: `(Σr + 5·μ) / (n + 5)` | Gợi ý "phim hay" nhưng không cá nhân hoá |
| B4 | **Bias** `μ + b_u + b_i` | `b_i` = độ hay của phim, `b_u` = độ dễ/khó tính của user, ước lượng luân phiên với regularization (λ_u = 10, λ_i = 25) | Baseline chuẩn cho rating prediction (Koren, 2009) |

### 3.2 Lọc cộng tác (Collaborative Filtering)

**Item-kNN (neighborhood).**
1. Tính phần dư `r̃_ui = r_ui − (μ + b_u + b_i)` để loại bỏ bias.
2. Độ tương đồng cosine giữa hai phim trên vector phần dư, nhân hệ số **shrinkage** `n_ij / (n_ij + λ)` (n_ij = số user chấm cả hai) để phạt các cặp ít bằng chứng.
3. Giữ top-k láng giềng cho mỗi phim (ma trận thưa).
4. Dự đoán: `r̂_ui = b_ui + Σ_j s_ij · r̃_uj / (Σ_j |s_ij| + 1)` trên các phim j user đã chấm.
- Siêu tham số (tune): k = 20, λ = 10. Giải thích được: "Vì bạn thích X, Y".

**MF-ALS (matrix factorization).**
`r̂_ui = μ + b_u + b_i + p_uᵀ q_i`, với p_u, q_i ∈ ℝ³². Cực tiểu bình phương sai số + `λ(‖p_u‖² + ‖q_i‖²)` bằng **Alternating Least Squares**: cố định Q giải P dạng nghiệm đóng (ridge regression từng user), rồi ngược lại, lặp 12 vòng.
- Siêu tham số (tune): k = 32, λ = 8. Fold-in user mới = một bước giải ridge với Q cố định.

**EASE — Embarrassingly Shallow Autoencoder (Steck, 2019).**
Làm việc trên phản hồi **ngầm** (đã xem = 1, chưa xem = 0) thay vì giá trị rating. Tìm ma trận item-item B:

`min_B ‖X − XB‖² + λ‖B‖²  với  diag(B) = 0`

Có nghiệm đóng: `P = (XᵀX + λI)⁻¹`, `B_ij = −P_ij / P_jj`. Điểm của user = `x_u · B`.
- Lý do chọn: tối ưu trực tiếp việc "tái tạo" những gì user sẽ xem, khớp với mục tiêu top-N hơn so với tối ưu RMSE; đơn giản, không có vòng lặp, thường là baseline rất mạnh trong các bài so sánh gần đây.
- Siêu tham số (tune): λ = 300; bỏ phim có < 2 lượt xem khỏi B (ma trận B còn 5.4k × 5.4k trên train, 6.3k × 6.3k trên toàn bộ dữ liệu, thay vì 9.7k × 9.7k).

### 3.3 Content-based

Mỗi phim được biểu diễn bằng vector TF-IDF ghép từ: **thể loại** (trọng số 1.0) + **tag** (0.6) + **thập niên** (0.3), chuẩn hoá L2.
Profile user = `Σ (r_ui − r̄_u) · x_i` (phim chấm cao hơn trung bình kéo về phía nó, phim chấm thấp đẩy ra xa). Điểm = cosine(profile, x_i).
- Ưu: gợi ý được phim mới/ít rating, giải thích được ("khớp thể loại Sci-Fi, Action"). Nhược: không biết chất lượng phim, chỉ biết "giống".

### 3.4 Hybrid

`score = w · z(ALS) + (1 − w) · z(Content)`, với `z(·)` là chuẩn hoá z-score trên toàn bộ phim. w = 0.6 chọn trên validation (lưới 0.3 → 1.0). Rating dự đoán lấy từ ALS.

## 4. Phương pháp đánh giá

Với mỗi user ở test: xếp hạng **toàn bộ phim chưa có trong train của user đó** (≈ 9.6k ứng viên), lấy top-10.

| Chỉ số | Định nghĩa | Ý nghĩa |
|---|---|---|
| RMSE, MAE | Sai số giữa rating dự đoán và rating thật ở test | Chất lượng dự đoán điểm |
| Precision@10 | (# phim phù hợp trong top-10) / 10 | Độ chính xác của danh sách |
| Recall@10 | (# phim phù hợp trong top-10) / (# phim phù hợp ở test) | Độ bao phủ sở thích |
| NDCG@10 | DCG / IDCG, phần thưởng giảm theo vị trí `1/log2(rank+1)` | **Chỉ số chính**: đúng *và* xếp đúng lên đầu |
| HitRate@10 | Tỷ lệ user có ít nhất 1 phim phù hợp trong top-10 | Trải nghiệm người dùng tối thiểu |
| Coverage | Số phim khác nhau xuất hiện trong mọi top-10 / tổng số phim | Đa dạng ở mức hệ thống |
| Novelty | TB `−log2(độ phổ biến)` của phim được gợi ý | Mức "ít người biết" của gợi ý |

Chỉ số ranking lấy trung bình trên các user có ít nhất một phim phù hợp ở test (592 user).

## 5. Kỳ vọng đầu ra và kết quả

### 5.1 Kỳ vọng đặt ra trước khi chạy

1. Random gần 0 trên mọi chỉ số ranking; coverage và novelty rất cao.
2. **Popularity là baseline khó vượt** vì dữ liệu long-tail (60% rating dồn vào 10% phim).
3. Rating prediction: `Bias` giảm RMSE rõ so với trung bình theo phim; Item-kNN/MF giảm thêm vài phần trăm.
4. Mô hình cá nhân hoá tốt nhất phải **vượt Popularity rõ rệt về NDCG@10** (mục tiêu ≥ +20%).
5. Content-based kém về độ chính xác nhưng đa dạng/mới lạ hơn; hybrid nhích nhẹ so với thành phần CF của nó.
6. UI trả gợi ý tức thời (< 1s), cho cả user mới.

### 5.2 Kết quả trên tập test (K = 10)

| Mô hình | RMSE ↓ | MAE ↓ | P@10 | R@10 | **NDCG@10** | Hit@10 | Coverage | Novelty |
|---|---|---|---|---|---|---|---|---|
| *B1* Random | – | – | 0.0017 | 0.0015 | 0.0014 | 0.017 | 46.5% | 7.31 |
| *B2* Popularity | 0.9985 | 0.7718 | 0.0576 | 0.0484 | 0.0750 | 0.321 | 1.0% | 1.52 |
| *B3* Top-rated | 0.9985 | 0.7718 | 0.0233 | 0.0178 | 0.0342 | 0.184 | 0.4% | 3.81 |
| *B4* Bias μ+bu+bi | 0.9148 | 0.7093 | 0.0556 | 0.0411 | 0.0675 | 0.306 | 0.7% | 1.92 |
| Item-kNN | **0.9008** | **0.6948** | 0.0654 | 0.0518 | 0.0835 | 0.338 | 2.5% | 2.28 |
| MF-ALS | 0.9104 | 0.7000 | 0.0564 | 0.0472 | 0.0703 | 0.340 | 4.0% | 2.31 |
| **EASE (implicit)** | – | – | **0.0833** | **0.0789** | **0.1016** | **0.453** | 6.0% | 2.32 |
| Content-based | – | – | 0.0042 | 0.0023 | 0.0049 | 0.041 | 33.6% | 7.38 |
| Hybrid (ALS+Content) | 0.9104 | 0.7000 | 0.0618 | 0.0530 | 0.0748 | 0.383 | 4.5% | 2.46 |

(RMSE của Popularity/Top-rated là của cùng ước lượng "điểm TB làm mịn của phim"; "–" = mô hình không dự đoán điểm.)

### 5.3 Phân tích — đối chiếu với kỳ vọng

- **Kỳ vọng 1, 2 — đúng.** Random ≈ 0. Popularity đạt NDCG 0.075, cao hơn cả Bias và MF-ALS — đây là hiện tượng đã biết trong tài liệu (Cremonesi et al., 2010): trên dữ liệu long-tail, "gợi ý phim ai cũng xem" là chiến lược rất mạnh.
- **Kỳ vọng 3 — đúng.** Bias giảm RMSE 8.4% so với điểm TB theo phim (0.9985 → 0.9148). Item-kNN giảm thêm 1.5% (→ 0.9008), MF-ALS 0.5%. Mức cải thiện nhỏ là bình thường với tập dữ liệu chỉ 100k rating và chia theo thời gian.
- **Kỳ vọng 4 — đạt.** **EASE vượt Popularity +35% NDCG@10, +63% Recall@10, +41% HitRate@10**, đồng thời gợi ý đa dạng gấp 6 lần (coverage 6.0% vs 1.0%). Với 45% user, ít nhất 1 trong 10 phim gợi ý là phim họ thực sự xem và chấm ≥ 4★ trong tương lai.
- **Mô hình tốt nhất cho dự đoán điểm ≠ mô hình tốt nhất cho xếp hạng.** MF-ALS có RMSE tốt hơn Bias nhưng NDCG còn thua Popularity: tối ưu RMSE chỉ học trên các phim *đã được chấm*, không học được "phim nào người dùng sẽ chọn xem". EASE học trên tín hiệu ngầm nên khớp mục tiêu top-N hơn. Đây là kết luận quan trọng nhất của thí nghiệm.
- **Kỳ vọng 5 — đúng một phần.** Content-based rất kém về độ chính xác (NDCG 0.005) nhưng coverage 34% và novelty 7.4 — nó gợi ý phim "đúng thể loại" nhưng ít người biết. Hybrid cải thiện ALS ở mọi chỉ số ranking (NDCG +6%, HitRate +13%) và tăng đa dạng, nhưng vẫn chưa vượt Popularity về NDCG.
- **Kỳ vọng 6 — đạt.** Sau khi huấn luyện một lần lúc khởi động (~20s), mỗi lượt gợi ý < 0.1s; user mới chọn vài phim là có gợi ý ngay.

Ví dụ định tính (user mới chỉ thích *The Matrix*, *Inception*, *Interstellar*):
- EASE → *The Dark Knight, Fight Club, The Shawshank Redemption, Star Wars IV, LOTR…* — "người xem các phim này cũng xem…".
- Content-based → *Edge of Tomorrow, Iron Man 3, Riddick…* — đúng thể loại Sci-Fi/Action nhưng chất lượng không đồng đều, minh hoạ đúng điểm yếu đo được ở bảng trên.

### 5.4 Khả năng giải thích (explainability)

Mỗi mô hình có `explain(history, item)` trả về một **phân rã chính xác** của chính điểm mô hình dùng để xếp hạng. Đây không phải lời giải thích ước lượng sau khi đã có kết quả (như LIME/SHAP). Phân rã chính xác được là nhờ mọi mô hình ở đây đều tuyến tính theo lịch sử người dùng khi tham số đã cố định.

| Mô hình | Phân rã | Câu giải thích mẫu |
|---|---|---|
| Popularity | score = số lượt chấm | "329 người đã chấm (hạng 1/9742)" |
| Top-rated | `Σr/(n+5)` + `5μ/(n+5)` | "Điểm TB 4.43★ từ 317 lượt, trộn 2% với TB hệ thống" |
| Bias | `μ + b_u + b_i` | "Phim được chấm cao hơn TB (+0.62★), bạn chấm dễ hơn TB (+0.28★)" |
| Item-kNN | bias + `Σⱼ sᵢⱼ·(r_uj − b_uj)/(Σ|sᵢⱼ|+1)`, mỗi phim đã xem là một hạng tử | "Giống các phim bạn chấm cao hơn kỳ vọng: Interstellar (+0.11★)…" |
| MF-ALS | `p_u = A⁻¹Q_Hᵀe` nên `q_iᵀp_u = Σⱼ (q_iᵀA⁻¹q_j)·e_j`: đóng góp của từng phim đã xem vào phần nhân tố ẩn | "Sở thích ẩn học từ: Interstellar (+0.04★)…" |
| EASE | `Σⱼ B[j, i]` | "Người xem các phim này cũng thường xem: Star Wars IV (+0.094)…" |
| Content-based | hai cách: theo phim đã xem `wⱼ·(xⱼ·xᵢ)/‖profile‖`, và theo đặc trưng `xᵢf·profile_f/‖profile‖` | "Khớp nội dung bạn thích: thể loại Sci-Fi (+0.25)…" |
| Hybrid | tổ hợp tuyến tính của hai phân rã trên, cộng hạng tử chuẩn hoá z-score | "60% từ MF-ALS, 40% từ nội dung…" |

Phép cắt điểm về [0.5, 5] (Item-kNN, MF-ALS) được ghi thành một hạng tử riêng để tổng vẫn khớp. `tests/test_explain.py` kiểm tra với 9 mô hình × 4 loại người dùng (lịch sử dài, thường, mới 3 phim, chưa có gì) × 10 phim: tổng các thành phần bằng đúng điểm mô hình (sai số < 1e-6). Random dùng seed theo lịch sử để cùng một người luôn nhận cùng danh sách và giải thích lại được.

Giải thích trung thực còn giúp phát hiện hành vi của mô hình. Ví dụ: với người dùng chỉ thích *Matrix, Inception, Interstellar, Star Wars IV*, Item-kNN cho *Forrest Gump* đúng bằng điểm của Bias. Phân rã cho thấy không phim nào trong lịch sử nằm trong top-20 láng giềng của nó, nên phần cộng tác bằng 0. Còn EASE gợi ý *Forrest Gump* (nhãn có Comedy) vì 65–75% người xem 4 phim kia cũng xem nó, không vì thể loại.

### 5.5 Hạn chế

- Dữ liệu nhỏ (610 user) → độ lệch giữa các cách chia có thể vài phần trăm; chưa chạy nhiều seed / khoảng tin cậy.
- Content-based dùng toàn bộ `tags.csv` (kể cả tag gắn sau thời điểm chia) → rò rỉ nhẹ. Tag chỉ có trên 16% phim nên ảnh hưởng nhỏ.
- Phim xuất hiện lần đầu ở test (8.3% rating test) là cold-start; chỉ Content-based xử lý được chúng.
- Chưa có poster/mô tả phim (cần API TMDB); UI chỉ link sang IMDb.

### 5.6 Hướng phát triển

- Hybrid dựa trên EASE thay vì ALS; learning-to-rank (BPR, LightGCN) hoặc mô hình tuần tự (SASRec) khai thác thứ tự thời gian.
- Tối ưu đa mục tiêu: rerank (MMR) để cân bằng độ chính xác và đa dạng.
- Chạy trên `ml-25m` để kết quả ổn định hơn.

## 6. Demo UI

`uv run streamlit run src/he_goi_y/app.py` → http://localhost:8501. Ứng dụng huấn luyện mọi mô hình trên **toàn bộ** dữ liệu (khác với đánh giá chỉ dùng train).

| Tab | Chức năng |
|---|---|
| ⭐ Gợi ý | Chọn user có sẵn **hoặc** làm người dùng mới (chọn phim thích/không thích); chọn mô hình, top-N, lọc thể loại, ngưỡng số lượt đánh giá. Bảng gợi ý có điểm, rating dự đoán, điểm cộng đồng, **lý do gợi ý**, link IMDb; bên cạnh là lịch sử và biểu đồ thể loại yêu thích. Khung **"Vì sao gợi ý phim này?"**: chọn một phim trong danh sách (hoặc phim bất kỳ) để xem công thức, biểu đồ thác nước cộng dồn từng thành phần ra đúng điểm, bảng đóng góp của từng phim trong lịch sử và của từng đặc trưng nội dung. |
| ⚖️ So sánh mô hình | Top-10 của cả 9 mô hình đặt cạnh nhau cho cùng một người + heatmap số phim trùng nhau. |
| 🔗 Phim tương tự | Chọn 1 phim → 10 phim giống nhất theo Item-kNN, EASE và Content-based. |
| 📊 Kết quả đánh giá | Bảng chỉ số ở mục 5.2 + biểu đồ, baseline tô xám để dễ so sánh. |
| 🗂️ Dữ liệu | Thống kê và biểu đồ ở mục 2 (phân phối điểm, long-tail, hoạt động user, thể loại). |

## 7. Cách chạy lại

```bash
uv sync                                   # cài phụ thuộc (Python ≥ 3.14)
uv run python -m he_goi_y.tune            # (tuỳ chọn, ~3 phút) chọn siêu tham số trên validation
uv run python -m he_goi_y.evaluate        # ~20s, ghi results/metrics.csv
uv run streamlit run src/he_goi_y/app.py  # mở demo
```

## Tài liệu tham khảo

- F. M. Harper, J. A. Konstan. *The MovieLens Datasets: History and Context.* ACM TiiS, 2015.
- Y. Koren, R. Bell, C. Volinsky. *Matrix Factorization Techniques for Recommender Systems.* IEEE Computer, 2009.
- B. Sarwar et al. *Item-based Collaborative Filtering Recommendation Algorithms.* WWW 2001.
- H. Steck. *Embarrassingly Shallow Autoencoders for Sparse Data.* WWW 2019.
- P. Cremonesi, Y. Koren, R. Turrin. *Performance of Recommender Algorithms on Top-N Recommendation Tasks.* RecSys 2010.
