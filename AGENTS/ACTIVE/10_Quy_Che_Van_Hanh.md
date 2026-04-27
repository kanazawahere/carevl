# Quy Chế Vận Hành Hệ Thống CareVL

Tài liệu này dành cho người vận hành tại trạm và bộ phận quản trị Hub.

`README.md` dùng để giới thiệu tổng quan dự án.  
`AGENTS.md` và `PHASE2_SCHEMA_SPEC.md` dùng cho dev và kỹ thuật.  
Tài liệu này dùng để thống nhất cách vận hành hằng ngày.

---

## 1. Mục đích

Quy chế này quy định cách tổ chức, cấp quyền, nhập liệu, đồng bộ và tiếp nhận dữ liệu trong CareVL để:

- quản lý theo **trạm y tế**
- tránh nhầm giữa **người thao tác** và **đơn vị chịu trách nhiệm dữ liệu**
- giữ cho dữ liệu đi đúng luồng **Edge → Hub**

---

## 2. Nguyên tắc chung

- Mỗi trạm là một đơn vị vận hành độc lập.
- Dữ liệu được quản lý theo **trạm**, không theo cá nhân.
- Người dùng trực tiếp chỉ là người thao tác thay mặt cho trạm.
- Mỗi trạm phải có một danh tính vận hành thống nhất:
  - tài khoản GitHub của trạm
  - branch Git của trạm
  - metadata trạm trong cấu hình
- GitHub là lớp hỗ trợ truy vết và phục hồi, không phải cơ chế bảo đảm tuyệt đối chống sai dữ liệu.
- An toàn vận hành phải dựa trên quy trình đúng, không dựa vào giả định rằng GitHub sẽ tự xử lý mọi sai sót.

---

## 3. Phạm vi áp dụng

Áp dụng cho:

- bộ phận quản trị Hub
- các trạm y tế và đoàn khám
- máy tính, tài khoản GitHub, branch Git và dữ liệu thuộc hệ thống CareVL

---

## 4. Mô hình quản lý

Mỗi trạm phải có:

- `1` tài khoản GitHub đại diện cho trạm
- `1` branch Git riêng
- `1` cấu hình metadata trạm

Ví dụ:

- Tài khoản GitHub: `TRAM-Y-TE-P-CAI-VON`
- Branch: `user/TRAM-Y-TE-P-CAI-VON`
- `station_id`: `TYT-VL-001`
- `commune_code`: `86839`

Ba thành phần này phải khớp với nhau.

---

## 5. Thuật ngữ

- `Hub`
  - nơi tiếp nhận, hợp nhất, tổng hợp và đối soát dữ liệu
- `Edge`
  - điểm nhập liệu thực tế tại trạm hoặc đoàn khám
- `Dữ liệu local`
  - dữ liệu đang lưu trên máy Edge
- `Đã sync`
  - dữ liệu đã được push lên branch của trạm
- `Chờ sync`
  - dữ liệu đã lưu local nhưng chưa gửi lên branch

---

## 6. Quy ước bắt buộc

### 6.1. Quy ước tài khoản

- Mỗi trạm dùng một tài khoản GitHub thống nhất.
- Không dùng tài khoản cá nhân để vận hành chính thức, trừ khi có chỉ định đặc biệt.

### 6.2. Quy ước branch

Branch của trạm phải theo mẫu:

```text
user/<ten_tai_khoan_tram>
```

Ví dụ:

```text
user/TRAM-Y-TE-P-CAI-VON
user/TRAM-Y-TE-X-BINH-MINH
```

### 6.3. Quy ước metadata

Mỗi branch trạm phải có metadata tối thiểu:

- tên hiển thị trạm
- mã trạm
- mã địa bàn nếu có

### 6.4. Quy ước trách nhiệm dữ liệu

- Dữ liệu sinh ra trên branch nào thì thuộc trách nhiệm của trạm đó.
- Hub chỉ tiếp nhận, hợp nhất và tổng hợp; Hub không thay thế trách nhiệm kiểm tra đầu vào của trạm.

### 6.5. Quy ước an toàn với file SQLite runtime

- File runtime chính của ứng dụng là `carevl.db`.
- `carevl.db` là file nhị phân SQLite; Git chỉ biết file có thay đổi hay không, không hiểu chi tiết từng hồ sơ bên trong để tự hợp nhất an toàn.
- Không dùng nhiều máy cùng thao tác trên cùng một workspace trạm nếu chưa có quy trình quản trị riêng.
- Không chép đè `carevl.db` bằng file khác khi chưa được Hub/Admin hướng dẫn.
- Nếu cần gửi dự phòng hoặc bàn giao kỹ thuật, phải dùng chức năng `Xuất dữ liệu` để tạo `DB snapshot`.

---

## 7. Vai trò và trách nhiệm

### 7.1. Hub/Admin

Hub/Admin chịu trách nhiệm:

- cấp hoặc chuẩn hóa tài khoản GitHub cho từng trạm
- cấp quyền repo dữ liệu
- tạo hoặc chuẩn hóa branch trạm
- khai báo metadata trạm
- hướng dẫn cài đặt và đăng nhập lần đầu
- theo dõi tình trạng sync
- merge dữ liệu từ các branch trạm
- xử lý conflict và sự cố quản trị

### 7.2. Trạm

Trạm chịu trách nhiệm:

- bảo quản tài khoản GitHub của trạm
- nhập dữ liệu đúng và kịp thời
- kiểm tra dữ liệu trước khi lưu
- push dữ liệu khi có mạng
- phối hợp với Hub khi có lỗi sync hoặc dữ liệu bất thường

### 7.3. Người thao tác tại trạm

Người thao tác phải:

- dùng đúng tài khoản của trạm
- không dùng tài khoản cá nhân để vận hành chính thức
- không chia sẻ token hoặc mật khẩu ra ngoài phạm vi được phép
- báo ngay khi phát hiện lỗi đồng bộ hoặc sai dữ liệu

---

## 8. Quy trình trạm mới tham gia

### Bước 1. Hub chuẩn bị danh tính trạm

- cấp tài khoản GitHub
- mời vào repo dữ liệu
- tạo branch đúng quy ước
- khai báo metadata

### Bước 2. Hub bàn giao cho trạm

- tài khoản GitHub
- repo dữ liệu
- `carevl.exe` hoặc bộ cài tương ứng
- hướng dẫn đăng nhập và nhập liệu

### Bước 3. Trạm đăng nhập lần đầu

- mở ứng dụng
- đăng nhập GitHub
- xác nhận mã thiết bị
- hoàn tất xác thực

### Bước 4. Kiểm tra nhận diện trạm

Sau đăng nhập, phải kiểm tra:

- tên trạm hiển thị đúng
- dữ liệu mới gắn đúng `station_id`
- sync hoạt động bình thường

Nếu sai nhận diện trạm, phải dừng vận hành và báo Hub.

---

## 9. Quy trình vận hành hằng ngày tại trạm

### Bước 1. Mở ứng dụng

- nếu token còn hiệu lực thì vào thẳng app
- nếu token hết hạn thì đăng nhập lại

### Bước 2. Nhập và lưu dữ liệu

- tạo hồ sơ
- sửa hồ sơ nếu cần
- xóa hồ sơ sai sau khi xác nhận

Khi lưu:

- dữ liệu được ghi vào SQLite local
- hệ thống tự commit thay đổi vào Git
- hồ sơ ở trạng thái `chờ sync` cho đến khi được push

### Bước 3. Làm việc offline

Trạm được phép làm việc hoàn toàn offline. Mất mạng không được làm gián đoạn thao tác nhập liệu.

### Bước 4. Đồng bộ khi có mạng

Khi có mạng, trạm bấm `Gửi về Hub`.

Nếu push thành công:

- dữ liệu được gửi lên branch của trạm
- hồ sơ chuyển sang trạng thái `đã sync`

Nếu push thất bại:

- dữ liệu vẫn còn trên máy
- tiếp tục làm việc bình thường
- push lại khi mạng ổn hoặc sau khi xử lý xong lỗi

Lưu ý an toàn:

- `Gửi về Hub` giúp đưa dữ liệu lên branch của trạm và giữ lịch sử commit để truy vết.
- `Gửi về Hub` không có nghĩa là hệ thống tự động sửa mọi sai sót dữ liệu.
- Nếu người dùng đã nhập sai rồi lưu sai, GitHub vẫn có thể lưu lại bản sai đó nếu người dùng tiếp tục gửi.
- Vì vậy, trạm vẫn phải kiểm tra dữ liệu trước khi lưu và dùng `DB snapshot` khi cần lưu dự phòng.

---

## 10. Quy trình Hub tiếp nhận dữ liệu

Hub thực hiện theo chu kỳ hoặc theo nhu cầu:

- kiểm tra branch nào có dữ liệu mới
- review thay đổi nếu cần
- merge từng branch trạm vào `main`
- chạy aggregate và build DuckDB để tổng hợp

Lưu ý:

- push thành công từ trạm không có nghĩa là dữ liệu đã vào `main`
- dữ liệu chỉ được xem là đã vào kho tổng hợp khi Hub merge thành công

---

## 11. Bảo mật

- Tài khoản GitHub của trạm là tài sản vận hành của trạm
- Token đăng nhập là thông tin nhạy cảm
- Không commit file chứa token
- Không chia sẻ tài khoản trạm cho đơn vị khác
- Khi nghi ngờ lộ tài khoản hoặc mất máy, phải báo Hub ngay

---

## 12. Xử lý sự cố

### Không đăng nhập được

Kiểm tra:

- có mạng hay không
- tài khoản GitHub còn quyền repo hay không

Nếu không tự xử lý được thì báo Hub.

### Push thất bại

Trạm:

- không xóa dữ liệu local
- ghi nhận thông báo lỗi
- thử lại khi có mạng
- nếu cần an toàn hơn trước khi xử lý tiếp, xuất `DB snapshot` và báo Hub/Admin

Hub:

- kiểm tra quyền repo, remote, branch và trạng thái hệ thống

### Sai tên trạm hoặc sai metadata

- dừng nhập liệu thật
- báo Hub để kiểm tra mapping trạm, branch và tài khoản

### Conflict khi merge

- Hub chịu trách nhiệm xử lý conflict ở cấp tổng hợp
- Trạm không tự ý sửa lịch sử Git nếu chưa có hướng dẫn

---

## 13. Điều cấm

- dùng tài khoản GitHub cá nhân để vận hành chính thức
- tự ý đổi tên branch trạm
- tự ý sửa metadata trạm
- xóa dữ liệu local để “sửa lỗi sync” khi chưa được hướng dẫn
- dùng lẫn nhiều tài khoản trên cùng máy vận hành chính thức nếu chưa có quy trình rõ ràng

---

## 14. Kết luận

CareVL vận hành theo nguyên tắc:

- `Một trạm = một danh tính vận hành`
- `Một trạm = một tài khoản GitHub đại diện`
- `Một trạm = một branch dữ liệu riêng`
- `Dữ liệu quản lý theo trạm, không theo cá nhân`

Đây là nền tảng để triển khai, đào tạo, tổng hợp dữ liệu và giảm lỗi vận hành.
