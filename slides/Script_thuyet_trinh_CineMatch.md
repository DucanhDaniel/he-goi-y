# Script thuyết trình CineMatch

## Tổng quan

Bài nói cho 16 slide, một người trình bày toàn bộ. Nói chậm, giải thích kỹ thì mất khoảng 28 phút. Thời lượng ghi ở từng slide chỉ là ước tính, không phải giới hạn.

| Phần | Slide | Thời lượng ước tính |
|---|---|---|
| 1. Mục tiêu và bài toán | 1–5 | 6 phút 40 giây |
| 2. Dữ liệu | 6–9 | 8 phút 15 giây |
| 3. Hướng xử lý và đánh giá | 10–13 | 11 phút 30 giây |
| 4. Kế hoạch và kết thúc | 14–16 | 1 phút 25 giây |

Mạch của bài: **mục tiêu của đề tài → dữ liệu có đủ không → làm thế nào → kiểm tra ra sao**. Mỗi phần mở đầu bằng câu hỏi đó để người nghe biết mình đang ở đâu.

Cách đọc script:

- Chữ trong ngoặc vuông, ví dụ *[chuyển slide]*, là hành động, không đọc ra.
- Lời thoại là gợi ý để nói theo ý. Không đọc nguyên văn trên slide.
- **Gặp thuật ngữ thì giải thích bằng lời thường trước, rồi mới gọi tên.** Ví dụ: "gợi ý một danh sách 10 phim, trên slide gọi là top-N". Người nghe nhớ ý, không cần nhớ tên.
- Câu chuyển phần (in đậm) là câu hỏi mở đầu phần sau. Dừng một nhịp sau câu đó để người nghe theo kịp.
- Khi nói về biểu đồ, bảng hoặc công thức, chỉ tay vào đúng chỗ đang nhắc tới.
- Không cần giải thích công thức từng ký hiệu. Chỉ cần nói công thức đó *làm gì*.
- Cuối file có bảng thuật ngữ để tra nhanh khi tập.

---

## Phần 1 — Mục tiêu và bài toán (slide 1–5)

### Slide 1 · Bìa (40 giây)

Em chào cô và các bạn. Em xin thay mặt nhóm trình bày đề tài. Nhóm em gồm ba thành viên: Hoàng Đức Anh, Phạm Đức Anh và Trần Quý Đôn, dưới sự hướng dẫn của cô Nguyễn Thị Kim Anh.

Đề tài của nhóm tên là CineMatch: một hệ thống gợi ý phim cho từng người, và mỗi gợi ý đều có lý do đi kèm.

Hôm nay em sẽ trình bày bốn câu hỏi: đề tài muốn làm gì, dữ liệu có đủ để làm không, nhóm định làm thế nào, và làm sao biết kết quả tốt hay không. *[chuyển slide]*

### Slide 2 · Nội dung trình bày (30 giây)

Bài gồm năm phần. *[chỉ lần lượt]* Đầu tiên là mục tiêu và bài toán. Thứ hai là bộ dữ liệu, trong đó em sẽ trả lời câu hỏi dữ liệu có đủ cho bài toán không. Thứ ba là hướng xử lý, tức là các mô hình nhóm định dùng. Thứ tư là cách đánh giá. Cuối cùng là kế hoạch thực hiện. *[chuyển slide]*

### Slide 3 · Mục tiêu của đề tài (1 phút 30 giây)

*[chỉ khung trên]* Nói ngắn gọn trong một câu: từ những phim một người đã chấm điểm, hệ thống đề xuất 10 phim họ chưa xem và có khả năng thích nhất, kèm lý do vì sao gợi ý.

Ví dụ, bạn đã chấm cao Interstellar và Inception. Hệ thống sẽ đưa ra 10 phim bạn chưa xem, và với mỗi phim nói rõ: "gợi ý phim này vì bạn thích Inception".

Vì sao cần một hệ thống như vậy? Có ba lý do.

*[chỉ cột 1]* Thứ nhất, quá tải lựa chọn. Các nền tảng như Netflix có hàng chục nghìn phim. Không ai có thể tự lướt hết để tìm phim hợp với mình.

*[chỉ cột 2]* Thứ hai, mỗi người một gu. Cách đơn giản nhất là đưa cho mọi người cùng một danh sách "phim hot". Nhưng người thích phim hoạt hình và người thích phim kinh dị không thể dùng chung một danh sách.

*[chỉ cột 3]* Thứ ba, người dùng mới. Khi một người vừa mở ứng dụng, họ mới chọn được vài phim. Hệ thống vẫn phải gợi ý được ngay, không bắt họ chờ.

*[chỉ dòng Phạm vi]* Về phạm vi: nhóm dùng bộ dữ liệu có sẵn tên là MovieLens. Nhóm kiểm tra chất lượng gợi ý trên dữ liệu lịch sử, chứ không thử với người dùng thật. Và có một giao diện demo để thử gợi ý trực tiếp. *[chuyển slide]*

### Slide 4 · Phát biểu bài toán (2 phút)

Mục tiêu ở slide trước được tách thành hai bài toán cụ thể.

*[chỉ khối trái]* **Bài toán chính là gợi ý một danh sách.** Đầu vào là lịch sử chấm điểm của một người. Hệ thống chấm điểm cho tất cả các phim người đó chưa xem, xếp từ cao xuống thấp, rồi lấy 10 phim đầu. Trong ngành, bài toán này gọi là "top-N recommendation", tức là gợi ý N phim đứng đầu; ở đây N bằng 10.

*[chỉ khối phải]* **Bài toán phụ là đoán điểm.** Với một phim cụ thể, hệ thống đoán xem người đó sẽ chấm bao nhiêu sao, trên thang từ nửa sao đến 5 sao. Bài toán này gọi là "rating prediction". Con số này dùng để hiển thị, ví dụ "bạn có thể chấm phim này khoảng 4,4 sao".

*[chỉ khung dưới]* Điều quan trọng: hai bài toán này không giống nhau. Một mô hình có thể đoán điểm rất sát mà vẫn gợi ý tệ.

Ví dụ: phần lớn các lượt chấm nằm quanh 3 đến 4 sao. Một mô hình lười, đoán phim nào cũng khoảng 3,5 sao, thì sai số trung bình đã khá nhỏ. Nhưng nó không chọn ra được phim nào người dùng thích nhất, vì phim nào cũng như nhau.

Vì vậy nhóm đo hai bài toán bằng hai bộ chỉ số riêng. Phần đánh giá ở cuối bài em sẽ nói kỹ. *[chuyển slide]*

### Slide 5 · Đầu vào và đầu ra (2 phút)

Để dễ hình dung, đây là một ví dụ nhóm chạy thử thật.

*[chỉ khung Đầu vào]* Đầu vào gồm ba thứ.

Thứ nhất là lịch sử chấm điểm. Ở đây là một người dùng mới vừa chọn ba phim: Interstellar 5 sao, Inception 5 sao, The Matrix 4,5 sao.

Thứ hai là thông tin về phim: thể loại, ví dụ hành động hay hài; tag, tức là các từ khoá người dùng tự gắn cho phim, ví dụ "plot twist"; và năm phát hành.

Thứ ba là tuỳ chọn, ví dụ muốn bao nhiêu phim, hoặc chỉ muốn xem phim thuộc một thể loại.

*[chỉ ô Hệ gợi ý rồi khung Đầu ra]* Hệ thống xử lý và trả về hai thứ.

Thứ nhất là danh sách phim người đó chưa xem, đã xếp thứ tự: The Shawshank Redemption, The Dark Knight, The Godfather, và tiếp tục cho đủ 10 phim. Mỗi phim kèm số sao hệ thống đoán người đó sẽ chấm.

Thứ hai là lý do. Ví dụ với The Dark Knight: hệ thống gợi ý vì bạn thích Inception và Interstellar, và phim này cùng thể loại tội phạm, IMAX với hai phim đó.

Các bạn để ý: The Dark Knight đứng thứ hai, dù số sao dự đoán là 4,36, thấp hơn The Godfather đứng thứ ba với 4,43 sao. Đó đúng là điều slide trước nói: thứ tự gợi ý và điểm dự đoán là hai việc khác nhau. Thứ tự còn tính đến việc phim có hợp gu riêng của bạn không, chứ không chỉ phim đó được chấm cao.

*[chỉ dòng chú thích dưới]* Một điểm nữa: hệ thống nhận diện người dùng qua danh sách phim họ đã chấm, chứ không qua mã người dùng. Nên người mới chỉ cần chọn vài phim là có gợi ý ngay, không phải dạy lại mô hình từ đầu.

**Chuyển phần:** Hệ thống cần những dữ liệu như vậy. Câu hỏi tiếp theo là: dữ liệu nhóm có trong tay có đủ không? *[chuyển slide]*

---

## Phần 2 — Dữ liệu (slide 6–9)

### Slide 6 · Bộ dữ liệu MovieLens (1 phút 30 giây)

Nhóm dùng bộ dữ liệu MovieLens, bản nhỏ tên là "ml-latest-small", do nhóm nghiên cứu GroupLens ở Đại học Minnesota công bố. Đây là bộ dữ liệu được dùng rất phổ biến khi nghiên cứu hệ gợi ý, nên kết quả dễ so sánh với các công trình khác.

*[chỉ lần lượt bốn con số]* Bộ này có 610 người dùng, mỗi người đã chấm ít nhất 20 phim. Có 9.742 phim, chia thành 20 thể loại. Tổng cộng hơn 100 nghìn lượt chấm điểm. Các lượt chấm trải dài từ năm 1996 đến 2018, và mỗi lượt đều ghi lại thời điểm chấm.

*[chỉ bảng]* Dữ liệu gồm bốn file:

- File quan trọng nhất là ratings, tức là bảng chấm điểm. Mỗi dòng cho biết: ai, chấm phim nào, mấy sao, vào lúc nào.
- File movies là danh sách phim: tên phim kèm năm, và các thể loại của phim.
- File tags chứa các từ khoá người dùng tự gắn cho phim.
- File links nối mỗi phim sang trang của nó trên IMDb và TMDB, hai trang thông tin phim lớn. *[chuyển slide]*

### Slide 7 · Dữ liệu có đủ cho bài toán không? (2 phút)

Đây là câu hỏi quan trọng trước khi bắt tay vào làm. Bảng này đặt cạnh nhau: bài toán cần gì, và dữ liệu có gì.

*[chỉ bốn dòng "Đủ"]* Bốn thứ chính đều đủ.

- Đầu vào của hệ thống là lịch sử chấm điểm. Dữ liệu có hơn 100 nghìn lượt, và mỗi người có ít nhất 20 lượt, nên ai cũng có đủ lịch sử để học.
- Để dạy mô hình đoán điểm, cần biết điểm thật. Dữ liệu có sẵn số sao từ nửa sao đến 5 sao cho mỗi lượt chấm.
- Để gợi ý theo nội dung phim, cần thể loại và năm. Gần như mọi phim đều có: 99,7% phim có thể loại, 99,9% có năm.
- Để kiểm tra mô hình đúng cách, cần biết lượt chấm nào trước, lượt nào sau. Mỗi lượt có ghi thời điểm, nên nhóm chia được dữ liệu theo thời gian. Phần đánh giá em sẽ nói vì sao điều này quan trọng.

*[chỉ hai dòng "Hạn chế"]* Có hai điểm hạn chế.

- Tag rất thưa: chỉ 16% phim có tag. Nên tag chỉ dùng làm thông tin phụ.
- Rất nhiều phim ít người chấm: 62% phim có dưới 5 lượt chấm. Với những phim này, mô hình có rất ít thông tin để biết ai sẽ thích chúng.

*[chỉ dòng cuối]* Còn mô tả nội dung phim, diễn viên, hay thông tin cá nhân của người dùng như tuổi, giới tính thì không có. Nhóm để những thứ này ngoài phạm vi. Nếu sau này cần, file links cho phép lấy thêm từ IMDb hoặc TMDB.

*[chỉ khung kết luận]* Kết luận: dữ liệu đủ cho cả hai bài toán, gợi ý danh sách và đoán điểm. Hai hạn chế kia không làm bài toán không giải được, mà chỉ quyết định nhóm phải chọn mô hình thế nào. Slide sau và slide tiếp theo sẽ nói rõ. *[chuyển slide]*

### Slide 8 · Đặc điểm dữ liệu (1 phút 45 giây)

Slide này cho thấy dữ liệu "trông như thế nào", để hiểu những khó khăn mô hình sẽ gặp.

*[chỉ thẻ 98.3%]* Thứ nhất, dữ liệu rất thưa. Hãy tưởng tượng một bảng lớn: mỗi hàng là một người, mỗi cột là một phim, mỗi ô là số sao người đó chấm phim đó. Trong bảng này, 98,3% số ô bị trống. Nghĩa là mỗi người chỉ chấm một phần rất nhỏ trong kho phim, và mô hình phải đoán phần trống còn lại.

*[chỉ biểu đồ]* Thứ hai, lượt chấm dồn vào một số ít phim. Cách đọc biểu đồ: nhóm xếp phim từ phim được chấm nhiều nhất tới phim ít nhất. Trục ngang là phần trăm số phim tính từ đầu danh sách, trục dọc là phần trăm tổng lượt chấm mà các phim đó chiếm.

*[chỉ điểm đánh dấu]* Ở điểm này: chỉ 10% phim đầu tiên đã chiếm 60% tổng lượt chấm. Phần còn lại, tức 90% số phim, chia nhau 40% lượt chấm. Hiện tượng này gọi là "long-tail", nghĩa là "đuôi dài": một cái đầu nhỏ gồm vài phim rất nổi tiếng, và một cái đuôi rất dài gồm rất nhiều phim ít người xem.

*[chỉ thẻ 35%]* Ở cuối đuôi, 35% số phim chỉ có đúng một lượt chấm.

*[chỉ thẻ 3.50★]* Thứ ba, điểm trung bình là 3,5 sao, tức là mọi người có xu hướng chấm cao. Và mỗi người có thói quen chấm riêng: có người dễ tính, chấm gì cũng 4–5 sao; có người khó tính, hiếm khi cho quá 3 sao. Mỗi phim cũng vậy: có phim được gần như ai cũng chấm cao.

Ba đặc điểm này dẫn thẳng tới các quyết định thiết kế ở slide sau. *[chuyển slide]*

### Slide 9 · Từ đặc điểm dữ liệu tới thiết kế (3 phút)

Slide này nối hai phần của bài: dữ liệu có đặc điểm gì, và vì thế mô hình phải được thiết kế ra sao. Bên trái là bốn đặc điểm, bên phải là cách nhóm xử lý từng cái. Mỗi quyết định ở phần sau đều xuất phát từ một trong bốn dòng này.

*[chỉ dòng 1]* **Thứ nhất, dữ liệu rất thưa.** 98,3% số ô trống, nghĩa là với phần lớn cặp người–phim, mô hình không có thông tin gì. Khi dữ liệu ít như vậy, mô hình rất dễ "học thuộc" vài lượt chấm lẻ tẻ rồi kết luận sai.

Ví dụ: có hai phim mà chỉ hai người cùng xem, và cả hai đều chấm 5 sao cho cả hai phim. Nếu chỉ nhìn con số, hai phim này "giống nhau tuyệt đối". Nhưng hai người là quá ít để tin.

Vì vậy nhóm dùng hai kỹ thuật, trên slide ghi là shrinkage và regularization:

- Khi đo hai phim giống nhau tới đâu, nhóm giảm bớt kết quả nếu có ít người cùng xem cả hai. Hai người cùng xem thì độ giống bị giảm còn khoảng một phần sáu; một trăm người cùng xem thì gần như giữ nguyên. Càng nhiều bằng chứng, càng được tin. Đó là shrinkage.
- Khi mô hình học, nhóm thêm một khoản phạt để mô hình không đưa ra kết luận quá mạnh chỉ từ vài lượt chấm. Nói đơn giản: thiếu bằng chứng thì mô hình nên dè dặt, kéo về mức trung bình. Đó là regularization.

*[chỉ dòng 2]* **Thứ hai, điểm lệch theo người và theo phim.** Như slide trước, có người dễ tính, có người khó tính. Có phim như The Shawshank Redemption gần như ai cũng chấm cao.

Nếu không tách các độ lệch này ra, mô hình sẽ nhầm. Nó tưởng người dễ tính "thích" mọi phim, và tưởng ai cũng "hợp gu" với phim nổi tiếng, trong khi đó chỉ là thói quen chấm điểm.

Vì vậy nhóm tách phần lệch này ra trước. *[chỉ công thức μ + bᵤ + bᵢ]* Công thức trên slide đọc là: điểm trung bình của mọi người, cộng mức dễ tính của người này, cộng mức hay của phim này. Ví dụ điểm trung bình chung là 3,5 sao; bạn hay chấm cao hơn mọi người 0,2 sao; phim này được chấm cao hơn trung bình 0,7 sao; vậy đoán bạn chấm khoảng 4,4 sao. Phần chênh lệch còn lại sau đó mới là sở thích riêng của bạn, và các mô hình ở phần sau học trên phần chênh lệch đó.

Phần này cũng được làm "dè dặt" như trên. Một phim chỉ có một lượt 5 sao sẽ không được coi là phim hay nhất, vì mô hình kéo nó về gần mức trung bình. Một phim có hai trăm lượt chấm cao thì được tin hơn nhiều.

*[chỉ dòng 3]* **Thứ ba, lượt chấm dồn vào ít phim nổi tiếng.** Điều này có hai hệ quả.

Hệ quả một: cách đơn giản nhất là gợi ý phim nổi tiếng cho tất cả mọi người, mà vẫn trúng khá nhiều, vì người nào cũng có khả năng cao đã xem hoặc sẽ xem các phim đó. Nếu nhóm chỉ so mô hình với cách chọn ngẫu nhiên thì mô hình nào trông cũng giỏi. Vì vậy nhóm lấy cách "gợi ý phim nổi tiếng nhất", trên slide gọi là Popularity, làm mốc bắt buộc: mô hình cá nhân hoá phải vượt được nó thì mới có giá trị.

Hệ quả hai: một mô hình có thể trúng nhiều chỉ bằng cách gợi ý toàn phim nổi tiếng. Mọi người nhận gần như cùng một danh sách, và phần lớn kho phim không bao giờ được gợi ý. Chỉ đo độ trúng thì không phát hiện được vấn đề này. Vì vậy nhóm đo thêm độ đa dạng của gợi ý; phần đánh giá em sẽ nói cụ thể.

*[chỉ dòng 4]* **Thứ tư, nhiều phim ít người chấm, tag lại thưa.** 35% số phim chỉ có đúng một lượt chấm. Các mô hình học từ "ai đã chấm phim nào" thì với những phim này gần như không có gì để học. Phim hoàn toàn mới, chưa ai chấm, thì các mô hình đó không gợi ý được.

Nhưng gần như mọi phim đều có thể loại và năm phát hành. Vì vậy nhóm thêm một hướng gợi ý dựa vào nội dung phim: bạn thích phim có thể loại gì, ra đời khoảng thập niên nào, thì gợi ý phim có đặc điểm giống vậy. Trên slide gọi là content-based. Thể loại được coi trọng nhất vì có ở hầu hết phim; tag chỉ là phụ.

Hướng dựa vào nội dung chỉ biết phim nào "giống", không biết phim nào "hay". Vì vậy cuối cùng nhóm kết hợp hai hướng lại thành mô hình lai, trên slide gọi là Hybrid.

*[chỉ dòng chú thích dưới cùng]* Tóm lại: dữ liệu thưa thì phải dè dặt với thông tin ít; điểm lệch thì tách phần lệch ra trước; lượt chấm dồn vào phim nổi tiếng thì phải vượt được cách gợi ý phim nổi tiếng và đo thêm độ đa dạng; phim ít lượt chấm thì dùng thêm nội dung phim và mô hình lai.

**Chuyển phần:** Dữ liệu đã đủ, và nhóm đã biết cần xử lý những điểm gì. Vậy cụ thể làm thế nào? *[chuyển slide]*

---

## Phần 3 — Hướng xử lý và đánh giá (slide 10–13)

### Slide 10 · Hướng xử lý tổng quan (2 phút 30 giây)

Nhóm đi theo bốn bước, từ đơn giản tới phức tạp. Nguyên tắc là: bước sau phải chứng minh được nó tốt hơn bước trước, nếu không thì không cần phức tạp thêm.

Em dùng lại ví dụ: bạn đã chấm cao Interstellar, Inception và The Matrix, và hệ thống cần chọn 10 phim cho bạn.

*[chỉ khối 1]* **Bước một: các cách đơn giản để làm mốc so sánh.** Trên slide gọi là baseline. Có bốn cách:

- Random: chọn ngẫu nhiên 10 phim. Đây là mức thấp nhất, mô hình nào cũng phải vượt xa.
- Popularity: gợi ý 10 phim được nhiều người chấm nhất. Mọi người nhận cùng một danh sách. Như slide trước đã nói, cách này rất khó đánh bại.
- Top-rated: gợi ý phim có điểm trung bình cao nhất. Có điều chỉnh để một phim chỉ có một người chấm 5 sao không nhảy lên đầu.
- Bias: đoán điểm bằng công thức ở slide trước: trung bình chung, cộng mức dễ tính của bạn, cộng mức hay của phim.

Cả bốn cách đều chưa thật sự hiểu gu của bạn. Chúng không quan tâm bạn thích loại phim gì.

*[chỉ khối 2]* **Bước hai: học từ những người có gu giống bạn.** Ý tưởng là: những người cũng thích Interstellar và Inception thì còn thích phim gì nữa? Cách này chỉ dựa vào ai đã chấm phim nào, không cần biết phim nói về gì. Trên slide gọi là lọc cộng tác. Nhóm dùng ba mô hình theo hướng này, slide sau em nói kỹ.

*[chỉ khối 3]* **Bước ba: dựa vào nội dung phim.** Bạn thích phim khoa học viễn tưởng, thì gợi ý thêm phim khoa học viễn tưởng. Trên slide gọi là content-based. Cách này dùng thể loại, tag và thập niên của phim.

*[chỉ khối 4]* **Bước bốn: kết hợp bước hai và bước ba**, để lấy ưu điểm của cả hai. Trên slide gọi là Hybrid.

*[chỉ khung "So sánh công bằng"]* Có hai nguyên tắc chung cho mọi bước. Thứ nhất, so sánh công bằng: mọi mô hình được kiểm tra trên cùng một phần dữ liệu và đo bằng cùng một bộ chỉ số. Nhờ vậy khi nói "mô hình A tốt hơn mô hình B" là có cơ sở.

*[chỉ khung "Gợi ý có giải thích"]* Thứ hai, gợi ý nào cũng có lý do. Điểm của mỗi phim được gợi ý được tách ra thành từng phần đóng góp. Ví dụ The Dark Knight được điểm cao, trong đó phần lớn là nhờ Inception, một phần nhờ Interstellar, một phần nhờ trùng thể loại. Từ đó hệ thống nói được "vì bạn thích Inception và Interstellar". *[chuyển slide]*

### Slide 11 · Bước 2: Lọc cộng tác (3 phút)

Đây là ba mô hình theo hướng "học từ những người có gu giống bạn". Cả ba dùng chung dữ liệu, nhưng cách học khác nhau. Các công thức trên slide em sẽ không đi vào từng ký hiệu, chỉ nói mỗi mô hình làm gì.

*[chỉ cột Item-kNN]* **Mô hình thứ nhất tìm phim giống phim bạn đã thích.** Trên slide gọi là Item-kNN.

Hai phim được coi là giống nhau nếu được mọi người chấm giống nhau: ai thích phim này thì cũng thích phim kia, ai chê phim này thì cũng chê phim kia. Ví dụ, người chấm cao Inception thường cũng chấm cao The Dark Knight, nên hai phim này giống nhau.

*[chỉ công thức]* Công thức trên slide làm hai việc. Dòng dưới: trước khi so sánh, nhóm trừ đi phần lệch do người dễ tính, khó tính và do phim nổi tiếng, như đã nói ở slide 9. Dòng trên: đo độ giống của hai phim, rồi giảm bớt nếu có ít người cùng xem cả hai.

Với mỗi phim, mô hình giữ lại 20 phim giống nó nhất. Khi gợi ý cho bạn, phim nào giống nhiều phim bạn đã thích thì được điểm cao.

Ưu điểm lớn nhất là rất dễ giải thích: "gợi ý phim này vì bạn thích Inception".

*[chỉ cột MF-ALS]* **Mô hình thứ hai tìm ra các "sở thích ẩn".** Trên slide gọi là MF-ALS.

Ý tưởng: mỗi người có một số sở thích, ví dụ thích khoa học viễn tưởng tới mức nào, thích phim nhiều cú lừa tới mức nào. Mỗi phim cũng có các đặc điểm tương ứng. Nếu sở thích của bạn khớp với đặc điểm của phim, bạn sẽ chấm phim đó cao.

Điểm đặc biệt là nhóm không đặt sẵn những sở thích này. Mô hình tự tìm ra chúng từ dữ liệu chấm điểm; nhóm chỉ quy định mỗi người và mỗi phim được mô tả bằng 32 con số. Vì không ai đặt tên cho chúng, nên gọi là "ẩn".

*[chỉ công thức]* Công thức trên slide đọc là: điểm dự đoán bằng phần lệch quen thuộc, cộng mức độ khớp giữa sở thích của bạn và đặc điểm của phim.

Cách học, gọi là ALS, làm luân phiên: giữ cố định đặc điểm của phim, tính sở thích của từng người cho khớp nhất với điểm họ đã chấm; rồi giữ cố định sở thích của người, tính lại đặc điểm của từng phim; lặp lại vài lần cho tới khi ổn định.

Ưu điểm: nắm được những sở thích mà không ai mô tả bằng lời được.

*[chỉ cột EASE]* **Mô hình thứ ba học xem phim nào hay được xem cùng nhau.** Trên slide gọi là EASE.

Khác với hai mô hình trên, mô hình này không quan tâm bạn chấm mấy sao, chỉ quan tâm bạn đã xem phim hay chưa: đã xem là 1, chưa xem là 0.

Nó học ra một bảng lớn, cho biết "người đã xem phim A thì có khả năng xem phim B tới mức nào". Cách học: dùng danh sách phim mỗi người đã xem để đoán lại chính danh sách đó. *[chỉ dòng "ràng buộc diag(B) = 0"]* Có một điều kiện: không được dùng phim A để đoán chính phim A, nếu không mô hình sẽ chỉ chép lại đáp án mà không học được gì.

Ưu điểm: bảng này tính được trực tiếp bằng một công thức, không phải thử đi thử lại nhiều lần. Và vì nó học đúng việc "người dùng sẽ chọn xem phim nào", nó rất hợp với bài toán chính là gợi ý danh sách 10 phim.

Điểm yếu chung của cả ba mô hình: phim nào ít người chấm thì gần như không có thông tin để học. Đó là lý do cần bước tiếp theo. *[chuyển slide]*

### Slide 12 · Bước 3–4: Content-based và Hybrid (2 phút 30 giây)

*[chỉ khối trái]* **Bước ba: gợi ý dựa vào nội dung phim.**

Mỗi phim được mô tả bằng ba loại đặc điểm: thể loại, tag và thập niên ra đời.

*[chỉ ba thanh trọng số]* Ba loại này được coi trọng khác nhau: thể loại quan trọng nhất, trọng số 1; tag 0,6; thập niên 0,3. Thể loại cao nhất vì phim nào cũng có. Tag thấp hơn vì chỉ 16% phim có.

Trong mỗi loại, nhóm dùng một cách tính trọng số gọi là TF-IDF. Ý tưởng đơn giản: đặc điểm càng hiếm thì càng nói lên nhiều về phim. Ví dụ, rất nhiều phim là Drama, nên biết một phim là Drama không giúp phân biệt được bao nhiêu. Còn tag "heist", tức phim về một phi vụ trộm, rất hiếm, nên hai phim cùng có tag này thì nhiều khả năng giống nhau thật.

*[chỉ công thức Profile]* Tiếp theo, nhóm xây "hồ sơ sở thích" của bạn từ các phim bạn đã chấm. Phim bạn chấm cao hơn mức bình thường của chính bạn sẽ kéo hồ sơ về phía đặc điểm của phim đó. Phim bạn chấm thấp hơn mức bình thường sẽ đẩy hồ sơ ra xa. Ví dụ bạn chấm cao nhiều phim khoa học viễn tưởng, thì hồ sơ của bạn nghiêng mạnh về khoa học viễn tưởng.

Cuối cùng, phim nào có đặc điểm gần với hồ sơ của bạn nhất thì được điểm cao.

Ưu điểm: gợi ý được cả phim mới, phim ít người xem, chỉ cần biết thể loại của nó. Nhược điểm: nó chỉ biết phim nào "giống" phim bạn thích, không biết phim nào "hay". Một phim khoa học viễn tưởng rất dở vẫn có thể được gợi ý.

*[chỉ khối phải]* **Bước bốn: kết hợp hai hướng.**

Hướng "học từ người có gu giống bạn" giỏi tìm phim hay mà bạn sẽ thích. Hướng "dựa vào nội dung" giỏi xử lý phim ít người xem. Mô hình lai cộng điểm của hai hướng lại.

*[chỉ công thức]* Công thức đọc là: điểm cuối cùng bằng w phần điểm từ hướng thứ nhất, cộng phần còn lại từ hướng thứ hai. Ví dụ w bằng 0,6 nghĩa là 60% từ hướng thứ nhất, 40% từ hướng thứ hai.

*[chỉ dòng z(·)]* Có một chi tiết: hai loại điểm có thang đo khác nhau. Một bên tính bằng số sao, một bên là độ giống. Cộng thẳng thì giống cộng mét với ki-lô-gam. Nên trước khi cộng, nhóm đưa cả hai về cùng một thang chung. Ký hiệu z trên slide là việc đó.

*[chỉ dòng "w chọn trên tập validation"]* Còn w bằng bao nhiêu thì nhóm không tự đặt. Nhóm thử nhiều giá trị, mỗi giá trị kiểm tra trên một phần dữ liệu được giữ riêng, rồi chọn giá trị cho kết quả tốt nhất. Phần dữ liệu giữ riêng đó gọi là tập validation; slide sau em nói rõ. *[chuyển slide]*

### Slide 13 · Kế hoạch đánh giá (3 phút 30 giây)

Phần này trả lời câu hỏi: làm sao biết mô hình gợi ý đúng, và đúng tới mức nào? Có ba ý: cách kiểm tra, thế nào là gợi ý đúng, và đo bằng chỉ số gì.

*[chỉ thanh train/test]* **Cách kiểm tra.** Nhóm không hỏi được người dùng thật, nên làm như sau: giấu bớt một phần dữ liệu đi, rồi xem mô hình có đoán ra phần bị giấu không.

Ví dụ, anh A đã chấm 100 phim, xếp theo thời gian. 80 phim chấm sớm nhất đưa cho mô hình học; phần này gọi là tập train. 20 phim chấm gần đây nhất bị giấu đi; phần này gọi là tập test. Mô hình chỉ được nhìn 80 phim cũ, rồi phải đoán xem sau đó anh A thích những phim nào. Đối chiếu với 20 phim bị giấu là biết mô hình đoán đúng hay sai.

Vì sao chia theo thời gian, mà không chọn ngẫu nhiên 20 phim để giấu? Vì ngoài đời, hệ thống chỉ biết quá khứ để đoán tương lai. Nếu chọn ngẫu nhiên, mô hình có thể học từ một phim anh A xem năm 2018 để "đoán" phim anh xem năm 2010. Như vậy là biết trước đáp án, và kết quả sẽ đẹp hơn thực tế.

Ngoài ra, nhóm tách thêm một phần nhỏ từ tập train, gọi là tập validation, để thử và chọn các thông số như trọng số w ở slide trước. Tập test chỉ dùng một lần duy nhất để chấm điểm cuối cùng, giống đề thi: không được xem trước khi thi.

**Thế nào là gợi ý đúng?** Một phim trong 20 phim bị giấu được coi là "phù hợp" nếu anh A chấm nó từ 4 sao trở lên, tức là anh thật sự thích. Nếu anh xem nhưng chỉ chấm 2 sao, thì gợi ý trúng phim đó cũng không được tính là đúng.

*[chỉ lần lượt ba khối dưới]* **Chỉ số đo** chia thành ba nhóm, tương ứng ba câu hỏi.

*[khối Dự đoán điểm]* **Câu hỏi một: đoán điểm có sát không?** Ví dụ mô hình đoán anh A chấm một phim 4,2 sao, thực tế anh chấm 5 sao, vậy lệch 0,8 sao. Lấy trung bình độ lệch trên tất cả các phim, ta được chỉ số MAE. Chỉ số RMSE cũng đo độ lệch, nhưng phạt nặng hơn những lần đoán sai nhiều: một lần lệch 2 sao bị phạt nặng hơn hai lần lệch 1 sao. Cả hai càng thấp càng tốt.

*[khối Xếp hạng top-10]* **Câu hỏi hai: danh sách 10 phim có trúng không?** Đây là câu hỏi chính.

Giả sử trong 20 phim bị giấu, anh A thích 6 phim. Mô hình gợi ý 10 phim, và trúng 3 trong 6 phim đó.

- Precision là trong 10 phim gợi ý, bao nhiêu phim trúng: 3 trên 10. Chỉ số này trả lời: gợi ý có nhiều phim thừa không?
- Recall là trong 6 phim anh A thích, tìm ra được bao nhiêu: 3 trên 6. Chỉ số này trả lời: có bỏ sót nhiều phim anh thích không?
- HitRate là có trúng ít nhất một phim hay không. Ở đây có, nên được tính là 1. Lấy trung bình trên mọi người dùng, ta biết bao nhiêu phần trăm người dùng nhận được ít nhất một gợi ý đúng.

Chỉ số chính của nhóm là **NDCG@10**. Ba chỉ số trên chỉ đếm số phim trúng. NDCG còn xét phim trúng nằm ở vị trí nào trong danh sách: trúng ở vị trí số 1 được nhiều điểm hơn trúng ở vị trí số 9, vì người dùng thường chỉ nhìn mấy phim đầu. Điểm này được so với một danh sách hoàn hảo, tức là mọi phim anh A thích đều nằm ở đầu danh sách. Nên NDCG nằm trong khoảng từ 0 đến 1, càng gần 1 càng tốt. Số 10 trong tên nghĩa là chỉ xét 10 phim đầu.

*[khối Mức hệ thống]* **Câu hỏi ba: hệ thống có gợi ý đa dạng không?** Như slide 9 đã nói, một hệ thống chỉ gợi ý mãi 10 phim bom tấn có thể trúng khá nhiều, nhưng không giúp ai khám phá được phim mới.

- Coverage, tức độ phủ: gộp danh sách gợi ý của tất cả người dùng lại, xem chúng chạm tới bao nhiêu phần trăm kho phim. Nếu ai cũng nhận cùng một danh sách thì độ phủ rất thấp.
- Novelty, tức độ mới lạ: các phim được gợi ý có phải toàn phim ai cũng biết không. Phim càng ít người xem thì càng được tính là mới lạ.

Vì sao cần cả ba nhóm? Vì mỗi nhóm phát hiện một kiểu "ăn gian" mà nhóm khác không thấy. Như slide 4 đã nói, đoán phim nào cũng quanh 3,5 sao thì sai số nhỏ, nhưng không chọn ra được phim người dùng thích nhất; nhóm hai sẽ phát hiện điều đó. Gợi ý toàn phim nổi tiếng thì trúng khá nhiều, nhưng độ phủ rất thấp; nhóm ba sẽ phát hiện điều đó.

**Chuyển phần:** Cuối cùng là nhóm sẽ thực hiện tất cả những việc trên theo kế hoạch nào. *[chuyển slide]*

---

## Phần 4 — Kế hoạch và kết thúc (slide 14–16)

### Slide 14 · Kế hoạch thực hiện (1 phút)

Nhóm chia công việc thành năm giai đoạn, theo đúng thứ tự em vừa trình bày. *[chỉ lần lượt]*

1. Đề xuất đề tài và tìm hiểu các công trình liên quan.
2. Chuẩn bị dữ liệu và làm các cách đơn giản để làm mốc.
3. Làm các mô hình học từ người có gu giống nhau, và mô hình dựa vào nội dung phim.
4. Kết hợp thành mô hình lai, và chạy đánh giá cho tất cả.
5. Làm giao diện demo và viết báo cáo.

Sản phẩm cuối kỳ gồm mã nguồn, hướng dẫn chạy, báo cáo, bài trình bày và hệ thống demo. *[chuyển slide]*

Khi slide đã điền tuần và người phụ trách, nói thêm mỗi giai đoạn một cụm, ví dụ "tuần 5–6, Đôn phụ trách".

### Slide 15 · Tài liệu tham khảo (10 giây)

Đây là các tài liệu nhóm tham khảo. Số trong ngoặc vuông khớp với các số em đã ghi trên các slide trước. *[chuyển slide ngay, không đọc từng dòng]*

### Slide 16 · Cảm ơn (15 giây)

Phần trình bày của em đến đây là kết thúc. Em cảm ơn cô và các bạn đã lắng nghe. Nhóm em rất mong nhận được câu hỏi và góp ý để hoàn thiện đề tài.

---

## Chuẩn bị hỏi đáp

Trả lời ngắn, đúng câu hỏi, rồi dừng. Nếu câu hỏi đi sâu vào phần một thành viên khác phụ trách, có thể nhờ bạn đó bổ sung.

| Câu hỏi có thể gặp | Gợi ý trả lời |
|---|---|
| Phần "giải thích" của nhóm khác các công cụ giải thích như LIME, SHAP thế nào? | LIME và SHAP đứng ngoài mô hình rồi ước lượng xem mô hình đã dựa vào đâu, nên chỉ là ước lượng gần đúng. Các mô hình của nhóm có dạng cộng dồn: điểm của một phim bằng tổng đóng góp của từng phim bạn đã xem. Nên nhóm tách được chính xác từng phần, không phải ước lượng. |
| Sao không chọn ngẫu nhiên dữ liệu để kiểm tra? | Chọn ngẫu nhiên thì mô hình có thể dùng thông tin tương lai để đoán quá khứ, nên kết quả đẹp hơn thực tế. Chia theo thời gian khó hơn nhưng đúng với việc gợi ý "phim xem tiếp theo". |
| Vì sao NDCG@10 là chỉ số chính? | Người dùng chủ yếu nhìn vài phim đầu danh sách. NDCG cho nhiều điểm hơn khi phim đúng nằm ở vị trí cao. Precision và Recall chỉ đếm trúng bao nhiêu, không quan tâm thứ tự. |
| Đoán điểm đã sát thì cần gì đo danh sách gợi ý? | Phần lớn điểm nằm quanh 3–4 sao, nên đoán gần mức trung bình đã có sai số nhỏ. Nhưng như vậy không chọn ra được phim người dùng thích nhất. Đó là lý do gợi ý danh sách là bài toán chính. |
| Vì sao chọn EASE? | EASE học đúng việc "người dùng sẽ chọn xem phim nào", hợp với bài toán gợi ý danh sách. Nó tính bằng một công thức trực tiếp nên đơn giản, và trong các nghiên cứu gần đây nó là đối thủ rất mạnh [4]. |
| Gợi ý phim nổi tiếng đã tốt như vậy thì cá nhân hoá có đáng không? | Chính vì vậy nhóm lấy cách gợi ý phim nổi tiếng làm mốc bắt buộc. Nhóm đặt mục tiêu mô hình tốt nhất vượt nó ít nhất 20% về NDCG@10. Ngoài ra, cách đó đưa cùng một danh sách cho mọi người, nên độ phủ rất thấp. |
| Dữ liệu thiếu mô tả phim, diễn viên thì sao? | Với hai bài toán của đề tài, lịch sử chấm điểm và thể loại là đủ. Thiếu mô tả chỉ làm phần lý do theo nội dung đơn giản hơn. File links cho phép lấy thêm từ IMDb hoặc TMDB nếu mở rộng. |
| Phim mới hoặc người dùng mới thì xử lý ra sao? | Người dùng mới: hệ thống nhận diện người dùng qua các phim họ đã chọn, nên chọn vài phim là có gợi ý, không cần dạy lại mô hình. Phim mới chưa ai chấm: các mô hình học từ người dùng khác không xử lý được, nên cần hướng dựa vào nội dung và mô hình lai. |
| Sao dùng bản nhỏ mà không dùng bản lớn ml-25m? | Bản nhỏ chạy nhanh, đủ để so sánh nhiều mô hình và thử nhiều thông số trong thời gian môn học. Chạy trên bản lớn để kết quả chắc chắn hơn là hướng mở rộng. |
| Ngưỡng "phù hợp" 4 sao lấy từ đâu? | Đây là ngưỡng thường dùng với MovieLens. Vì mọi người có xu hướng chấm cao, 3 sao chỉ là "bình thường", từ 4 sao trở lên mới thể hiện là thích. |
| Có dùng deep learning không? | Giai đoạn này chưa. Nhóm ưu tiên các mô hình giải thích được chính xác lý do gợi ý. Các mô hình deep learning như SASRec hoặc LightGCN là hướng phát triển sau. |

---

## Bảng thuật ngữ

Tra nhanh khi tập. Khi nói, luôn nói phần "nghĩa là" trước, tên thuật ngữ sau.

| Thuật ngữ trên slide | Nghĩa là |
|---|---|
| Top-N recommendation | Gợi ý một danh sách N phim đứng đầu (ở đây N = 10) |
| Rating prediction | Đoán xem một người sẽ chấm một phim bao nhiêu sao |
| Baseline | Cách làm đơn giản dùng làm mốc so sánh |
| Popularity | Gợi ý phim được nhiều người chấm nhất, ai cũng nhận như nhau |
| Bias, μ + bᵤ + bᵢ | Điểm trung bình chung + mức dễ tính của người + mức hay của phim |
| Long-tail | Lượt chấm dồn vào ít phim nổi tiếng; rất nhiều phim ít người xem |
| Ma trận thưa | Bảng người × phim mà hầu hết các ô đều trống |
| Shrinkage | Giảm độ tin vào một kết luận khi có ít người làm bằng chứng |
| Regularization | Khoản phạt khiến mô hình dè dặt khi thiếu dữ liệu |
| Lọc cộng tác (collaborative filtering) | Gợi ý dựa trên những người có gu giống bạn |
| Item-kNN | Tìm phim giống phim bạn đã thích, dựa trên cách mọi người chấm |
| MF-ALS | Tự tìm ra các "sở thích ẩn" của người và phim; học luân phiên |
| EASE | Học xem phim nào hay được xem cùng nhau; chỉ xét đã xem hay chưa |
| Phản hồi ngầm | Chỉ biết người dùng đã xem hay chưa, không biết chấm mấy sao |
| Content-based | Gợi ý dựa vào nội dung phim: thể loại, tag, thập niên |
| TF-IDF | Cách tính trọng số: đặc điểm càng hiếm càng được coi trọng |
| Hybrid | Kết hợp lọc cộng tác và content-based |
| z-score, z(·) | Đưa hai loại điểm về cùng một thang trước khi cộng |
| Train / Test | Phần dữ liệu để mô hình học / phần dữ liệu giấu đi để kiểm tra |
| Validation | Phần dữ liệu riêng để thử và chọn thông số, không đụng tới tập test |
| RMSE, MAE | Đoán điểm lệch so với thực tế bao nhiêu sao; càng thấp càng tốt |
| Precision@10 | Trong 10 phim gợi ý, bao nhiêu phần trăm là trúng |
| Recall@10 | Trong các phim người dùng thích, tìm ra được bao nhiêu phần trăm |
| HitRate@10 | Có trúng ít nhất một phim trong 10 phim hay không |
| NDCG@10 | Độ trúng có tính vị trí: trúng càng gần đầu danh sách càng nhiều điểm |
| Coverage | Các gợi ý chạm tới bao nhiêu phần trăm kho phim |
| Novelty | Các phim được gợi ý có phải toàn phim ai cũng biết không |
