# Phạm vi thu thập dữ liệu nghiệp vụ (Người nghiệp vụ trước, kỹ thuật sau)

## Trạng thái
[Active]

## Ai nên đọc, để làm gì

| Đối tượng | Việc cần làm sau khi đọc |
|-----------|---------------------------|
| **Sở Y tế / người ra quyết định nghiệp vụ** | Ký hoặc ghi ý vào các ô **«Cần quyết định»** (Phụ lục B) và xác nhận Phụ lục A có đủ / thiếu mục nào. **Không cần** biết SQL hay tên bảng. |
| **Trạm y tế (trưởng trạm, tiếp nhận)** | Đối chiếu Phụ lục A với thực tế quầy: có đủ thông tin để vận hành không; ghi thêm mục thiếu vào cuối tài liệu hoặc bản nháp nội bộ. |
| **Lập trình / thiết kế CSDL** | Dùng tài liệu này làm **đầu vào đã thống nhất** rồi mới chi tiết hóa bảng/cột trong [09. Đặc tả lược đồ CareVL giai đoạn 2](09_Phase2_Schema_Spec.md). |

## Đọc nhanh (1 trang)

1. **Phụ lục A** — Danh sách **thông tin bắt buộc / thường gặp** khi người dân đến khám (định danh + mã lượt khám). Đây là phần **dễ hiểu nhất**; nếu chỉ đọc một bảng thì đọc bảng này.  
2. **Phụ lục B** — **Chưa chốt** với Sở: nhóm đối tượng (trẻ, người già, …) và phần khám bổ sung. Bảng nói rõ **còn thiếu quyết định gì** — không phải kết luận cuối.  
3. **Phụ lục C** — Quy tắc soạn **câu hỏi trên phiếu / màn hình**: ưu tiên **chọn sẵn**, hạn chế **tự viết dài**.  
4. Từ **«mô-đun»**, **«lượt khám»** trong tài liệu:**  
   - *Lượt khám* = một người đến khám một lần trong phiên làm việc (có thể có nhiều bước: tiếp nhận → bác sĩ → xét nghiệm…).  
   - *Mô-đun* = một **bộ câu hỏi hoặc mục khám thêm** chỉ áp dụng cho một nhóm (ví dụ chỉ cho trẻ em). **Chưa** chỉ tên màn hình hay tên bảng CSDL ở đây.

## Bối cảnh
Đội ngoài (Sở Y tế, trạm) và đội trong (lập trình) cần **cùng một sự thật** nhưng **khác ngôn ngữ**: người nghiệp vụ cần biết *thu thập những thông tin gì, với ai*; lập trình cần *bảng, cột, kiểu dữ liệu có cấu trúc*. Nếu nhảy thẳng vào sơ đồ CSDL hoặc SQL mà chưa thống nhất phạm vi nghiệp vụ, tài liệu sẽ mơ hồ và phần mềm dễ bị yêu cầu sửa vòng.

Nhóm đã thống nhất hướng: **định danh qua căn cước công dân (CCCD)** (mã QR / chip — dữ liệu cơ bản đã được mã hóa trên thẻ). Vấn đề **gói khám / đối tượng** (trẻ em so với người cao tuổi so với lao động) **chưa khóa hết** nhưng đã có hướng: **mô-đun khảo sát / phần bổ sung khác nhau theo nhóm** (ví dụ gợi ý: trẻ em — bộ câu hỏi liên quan tự kỷ; người cao tuổi — bộ câu hỏi liên quan tâm lý / trầm cảm).

## Quyết định

1. **Hai lớp tài liệu song song, không thay thế nhau**
   - **Lớp A (tài liệu này):** bảng mô tả **ý nghĩa nghiệp vụ**, tiếng Việt, không bắt buộc cú pháp SQL. Dùng để **xác nhận phạm vi** với Sở / trạm trước khi khóa chi tiết lược đồ dữ liệu (schema).
   - **Lớp B:** [09. Đặc tả lược đồ CareVL giai đoạn 2](09_Phase2_Schema_Spec.md) — mô hình lưu trữ, bảng, migration. Cập nhật Lớp B **sau** khi Lớp A được đồng ý (hoặc ghi rõ phạm vi “giai đoạn 1”).

2. **Định danh người đến khám (đã thống nhất hướng)**
   - Nguồn chính: **quét CCCD** (QR / chip), không phụ thuộc nhập tay đầy đủ cho các trường đã có sẵn trên thẻ.
   - Các thông tin cơ bản thường có trên CCCD (số định danh, họ tên, ngày sinh, giới tính, địa chỉ thường trú, ngày cấp, …) — phía kỹ thuật ánh xạ sang hồ sơ người bệnh / mã định danh theo tài liệu giai đoạn 2 (lập trình đọc file 09).

3. **Đối tượng và mô-đun bổ sung (chưa khóa đủ — ghi rõ *chưa quyết*)**
   - Hệ thống **không** giả định “một gói khám một kiểu cho tất cả mọi người”.
   - **Nhóm đối tượng** dùng để **chọn / hiển thị** các **mô-đun khảo sát hoặc mục khám bổ sung** (ví dụ: trẻ em / người cao tuổi khác nhau).
   - Chưa quyết định cuối: danh sách đủ các nhóm, tên gọi chính thức, và tiêu chí tự động (theo tuổi) hay chọn tay. Phụ lục B ghi **rõ câu hỏi cần Sở trả lời**.

4. **Thứ tự làm việc gợi ý (tránh kẹt suy nghĩ)**
   - Bước 1: Hoàn thiện / ký duyệt **bảng Lớp A** trong tài liệu này (với Sở hoặc nhóm nghiệp vụ).
   - Bước 2: Chuyển quyết định sang **Lớp B** (tài liệu 09 + SQL / migration + hợp đồng API).
   - Bước 3: Cập nhật **sơ đồ E2E / tính năng** ([26. Thư mục trực quan hóa](26_Visualization.md), [1. Tiếp nhận mới](../FEATURES/1_tiep_nhan_moi.md)) nếu bước 4 (vận hành hằng ngày) đổi màn hình hoặc luồng.
   - **Wireframe** (nếu cần): chỉ bắt buộc khi luồng tiếp nhận / chọn mô-đun phức tạp; không bắt buộc trước bước 1.

5. **Hình thức câu hỏi trên biểu mẫu thu thập / khảo sát tại trạm (ưu tiên lựa chọn sẵn)**  
   *(Đây là cách đặt **câu hỏi cho người bệnh / nhân viên trên màn hình** — **khác** với câu hỏi dùng khi **họp thiết kế CSDL** — bảng, cột, migration; phần đó nằm trong [09. Đặc tả lược đồ CareVL giai đoạn 2](09_Phase2_Schema_Spec.md), mục **«Câu hỏi khi xây dựng schema»**.)*
   - Mỗi mục cần thu thập: **mặc định** thiết kế dưới dạng **câu hỏi có đáp án chọn** (một lựa chọn, nhiều lựa chọn, thang điểm, Có–Không–Không rõ, …) với **danh mục đáp án đóng** do nghiệp vụ phê duyệt.
   - **Tự viết tay** (ô chữ tự do) chỉ khi **không thể** gói vào lựa chọn sẵn; **hạn chế** số câu và độ dài.
   - Nguyên tắc tại trạm: **nhiều câu trắc nghiệm** thường **dễ hơn** cho người khai và cho tổng hợp báo cáo hơn **nhiều câu tự viết dài**.

## Cơ sở
Tách “con người” và “máy” giảm rủi ro: Sở ký phạm vi thu thập trước, lập trình không phải đoán. Biểu mẫu động trong giai đoạn 2 **khớp** với ý tưởng mô-đun theo đối tượng mà **chưa cần** biết hết SQL ngay hôm nay. Đáp án có cấu trúc (chọn sẵn) **vừa** giảm tải ở quầy **vừa** giúp Hub / báo cáo đếm nhất quán. Nguyên tắc «ưu tiên lựa chọn sẵn» áp dụng **song song**: trên biểu mẫu (mục 5) và trong **câu hỏi khi xây CSDL** (tài liệu 09).

---

## Phụ lục A — Thông tin định danh & lượt khám (bảng cho Sở / trạm đọc trước)

**Ý nghĩa một dòng:** Đây là những thứ **hệ thống cần có** để biết **đang khám ai** và **một lượt khám là gì**, trước khi nói đến xét nghiệm hay khảo sát bổ sung.

| Thông tin cần có | Bắt buộc? | Lấy từ đâu (nói đơn giản) | Ví dụ / ghi chú dễ hiểu |
|------------------|-----------|---------------------------|-------------------------|
| Số CCCD (căn cước) | **Có** — luồng chuẩn | Quét QR hoặc chip trên thẻ; nhập tay chỉ khi máy hỏng | Giống khi đọc thẻ ở cửa ra vào bệnh viện |
| Họ tên, ngày sinh, giới tính | **Thường có** trên thẻ | Từ CCCD sau khi quét | Nếu thẻ lỗi có thể nhập để đối chiếu |
| Địa chỉ thường trú | **Thường có** trên thẻ | Từ CCCD | |
| **Tem / mã vạch / sticker** gắn với **một lần khám** | **Có** — theo thiết kế CareVL | In tại quầy tiếp nhận, dán cho người bệnh | Cùng một mã theo người từ lúc vào đến khi có kết quả (tránh nhầm người) |

*Nếu Sở hoặc trạm thấy thiếu một dòng bắt buộc nào (ví dụ thêm số BHYT bắt buộc), ghi rõ vào chỗ «Mớ mở» cuối tài liệu hoặc bản họp.*

---

## Phụ lục B — Nhóm đối tượng & phần khám thêm (chưa chốt — **bảng để hỏi Sở**)

**Ý nghĩa một dòng:** Bảng dưới **không phải** quyết định cuối. Đây là **danh sách việc cần làm rõ**; khi Sở trả lời từng ô «Cần quyết định», lập trình mới gắn vào phần mềm và CSDL.

| Nhóm người (tạm gọi) | Phần có thể thêm khi khám (ý tưởng) | Trạng thái hiện tại | **Câu hỏi cần Sở / chuyên môn trả lời** (gợi ý) |
|----------------------|--------------------------------------|---------------------|------------------------------------------------|
| Trẻ em | Bộ câu hỏi / mục khám gợi ý liên quan **tự kỷ** (sàng lọc) | **Chưa quyết** | Có bắt buộc không? Từ tuổi nào? Theo quy định nào? |
| Người cao tuổi | Bộ câu hỏi / mục khám gợi ý **tâm lý / trầm cảm** | **Chưa quyết** | Định nghĩa «cao tuổi» theo tuổi hay theo nhóm đối tượng chương trình? |
| Người lao động / khác | Gói khám theo **quy định địa phương** | **Chưa quyết** | Có bao nhiêu «gói» chính thức; ai được xếp vào gói nào? |

**Sau khi có câu trả lời:** phía kỹ thuật ghi vào tài liệu 09 (tên bảng, trường lưu câu trả lời, v.v.). Trước đó, **không** coi bảng trên là đã hiểu xong nếu chưa họp.

---

## Phụ lục C — Cách đặt câu hỏi trên phiếu / màn hình (ưu tiên chọn, hạn chế viết)

**Ý nghĩa một dòng:** Người điền **bấm chọn** nhanh hơn và ít sai hơn **viết tay dài**; báo cáo sau này cũng dễ đếm.

| Loại câu hỏi trên màn hình | Nó là gì (một câu) | Ví dụ cụ thể (minh họa) |
|----------------------------|--------------------|-------------------------|
| Chọn **một** đáp án | Danh sách có sẵn, chỉ chọn một | «Tình trạng dinh dưỡng: Bình thường / Thiếu cân / Thừa cân / Không đánh giá» |
| Chọn **nhiều** đáp án | Tick nhiều mục trong danh sách | «Triệu chứng hô hấp: Ho / Sổ mũi / Khó thở / Không có» |
| Thang điểm / mức độ | Chọn mức từ nhẹ đến nặng hoặc 1–5 sao | «Mức đau hiện tại: Không / Nhẹ / Vừa / Nặng» |
| Có / Không / Không rõ | Chuẩn hóa, không để người dân tự diễn đạt | «Có dị ứng thuốc không: Có / Không / Chưa rõ» |
| Chọn từ **danh mục có mã** | Chọn dòng trong bảng chuẩn (không tự gõ mã) | «Loại xét nghiệm: …» (danh mục do đơn vị ban hành) |

| Loại | Khi nào được dùng | Hạn chế |
|------|-------------------|---------|
| Ô viết **ngắn** (một vài dòng) | Chỉ khi không gói được vào bảng trên | Ít câu; có dòng gợi ý («Ghi thêm nếu có…») |
| Ô viết **dài** | Tránh ở quầy đông | Nếu bắt buộc: làm ở bước sau (sau khám), giới hạn số chữ |

**Ví dụ một câu đúng tinh thần tài liệu:**  
*«Trẻ có tiếp xúc mắt khi gọi tên không? »* → Đáp án: **Luôn / Đôi khi / Hiếm / Không đánh giá** (chọn một) — **không** để ô trống «Mô tả hành vi của trẻ» làm câu chính.

**Việc cần làm khi soạn với chuyên môn:** mang theo **bảng: câu hỏi — kiểu (một / nhiều / thang) — các lựa chọn sẵn**; sau đó lập trình map vào biểu mẫu trong hệ thống.

---

## Mớ mở cần làm rõ (ghi thêm dần)

- Danh sách chính thức **các nhóm đối tượng** và tiêu chí vào nhóm (tuổi? loại khám?).
- Gói khám theo **quy định địa phương / năm** có thay đổi theo mùa không.
- Mô-đun nào **bắt buộc** so với **tự chọn**; ai ký (bác sĩ / tiếp nhận / hệ thống tự động).
- Ngưỡng nghiệp vụ: tối đa **bao nhiêu** câu tự viết / mô-đun; tỷ lệ gợi ý (ví dụ ≥80% câu có lựa chọn sẵn) nếu Sở muốn quy chuẩn.

## Tài liệu liên quan
- [09. Đặc tả lược đồ CareVL giai đoạn 2](09_Phase2_Schema_Spec.md)
- [12. Luồng dữ liệu giao diện: từ tiếp nhận đến kết quả trễ](12_ui_ux_flow.md)
- [26. Thư mục trực quan hóa: SVG, Mermaid và bảng](26_Visualization.md)
- [1. Tiếp nhận mới](../FEATURES/1_tiep_nhan_moi.md)
- [19. Hướng dẫn migration giai đoạn 2](19_Phase2_Migration_Guide.md)
