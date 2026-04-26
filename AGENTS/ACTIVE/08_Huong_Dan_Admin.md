# Hướng Dẫn Nghiệp Vụ Cho Admin CareVL

Tài liệu này dành cho bộ phận Hub/Admin vận hành hệ thống CareVL ở cấp quản trị.

Nếu `QUY_CHE_VAN_HANH.md` là tài liệu quy định nguyên tắc vận hành, thì tài liệu này là hướng dẫn thao tác nghiệp vụ cho admin trong công việc hàng ngày.

## 1. Vai trò của admin

Admin là bộ phận quản trị hệ thống ở cấp Hub, chịu trách nhiệm:

- Tạo và quản lý danh tính vận hành cho từng trạm
- Cấp quyền truy cập repo dữ liệu
- Kiểm soát cấu hình trạm
- Hướng dẫn đăng nhập và sử dụng cho trạm
- Theo dõi tình trạng đồng bộ
- Tiếp nhận, review và merge dữ liệu từ các trạm
- Xử lý các sự cố vận hành ở cấp hệ thống

## 2. Nguyên tắc admin phải nắm

- Hệ thống quản lý theo `trạm`, không quản lý theo `cá nhân`
- Mỗi trạm phải có một danh tính thống nhất: `tài khoản GitHub + branch + metadata trạm`
- Trạm push dữ liệu lên branch riêng
- Hub/Admin merge dữ liệu từ các branch trạm về `main`
- Push thành công không có nghĩa là dữ liệu đã vào nhánh tổng hợp

## 3. Bộ quản lý tối thiểu cho mỗi trạm

Admin phải bảo đảm mỗi trạm có đầy đủ:

- `1 tài khoản GitHub đại diện cho trạm`
- `1 branch đúng quy ước`
- `1 metadata trạm` trong file quản lý trạm
- `1 máy vận hành` đã có repo dữ liệu và ứng dụng

Mẫu quy ước:

```text
Tai khoan GitHub: TRAM-Y-TE-P-CAI-VON
Branch: user/TRAM-Y-TE-P-CAI-VON
Title: Tram Y Te Phuong Cai Von
Station ID: TYT-VL-001
Commune code: 86839
```

## 3A. Bộ tool admin đang có trong repo

Admin có thể dùng ngay bộ tool trong repo này:

- Nguồn dữ liệu gốc: `config/stations.csv`
- File cấu hình app đọc: `config/stations.json`
- File cấu hình admin app: `config/app_config.json`
- File mở giao diện admin: `CareVL Admin.bat`

Quy trình sử dụng đề xuất:

1. Sửa `config/stations.csv`
2. Chạy `CareVL Admin.bat`
3. Trong `Admin App`, chạy kiểm tra danh sách trạm
4. Nếu cần, kiểm tra branch nào đã có `carevl.db`
5. Nếu hợp lệ, build `stations.json`
6. Nếu cần bàn giao hoặc theo dõi onboarding, xuất checklist
7. Nếu cần gom snapshot dữ liệu toàn hệ thống theo ngày, chạy aggregate
8. Nếu cần tổng hợp/thống kê/dashboard tại Hub, build Hub DuckDB

Kết quả checklist sẽ được xuất ra:

- `reports/onboarding_checklist.csv`
- `reports/onboarding_checklist.md`
- `reports/hub/runtime_branch_status.json`
- `reports/aggregate/YYYY-MM-DD/`
- `reports/hub/carevl_hub.duckdb`

Luu y:

- App se hien che do doi tram cho admin khi dang o nhanh `main`
- Hoac khi username GitHub nam trong `admin_usernames` cua `config/app_config.json`

## 4. Quy trình admin onboard trạm mới

### Bước 1. Tạo danh tính cho trạm

Admin thực hiện:

- Chuẩn hóa tên tài khoản trạm
- Chuẩn hóa tên branch trạm
- Gán mã trạm và mã địa bàn cho trạm

Checklist:

- Đã có tên viết không dấu, dễ nhận diện
- Đã thống nhất tên tài khoản và tên branch
- Đã gán mã trạm duy nhất
- Đã gán commune code nếu có

### Bước 2. Cấp quyền GitHub

Admin thực hiện:

- Tạo tài khoản GitHub cho trạm hoặc tiếp nhận tài khoản đã được cấp
- Mời tài khoản trạm vào repo dữ liệu private
- Kiểm tra tài khoản có quyền clone, pull, push

Checklist:

- Tài khoản đã vào đúng org hoặc repo
- Tài khoản đã accept lời mời
- Repo dữ liệu đã truy cập được

### Bước 3. Khai báo metadata trạm

Admin thêm bản ghi cho trạm vào file cấu hình quản lý trạm.

Thông tin tối thiểu:

- Tên branch
- Tên hiển thị trạm
- Mã trạm
- Mã địa bàn

Checklist:

- Branch trong metadata trùng với branch sẽ vận hành
- Tên hiển thị đúng tên trạm
- Mã trạm không trùng với trạm khác

### Bước 4. Chuẩn bị máy cho trạm

Admin hoặc bộ phận kỹ thuật chuẩn bị:

- Repo dữ liệu
- File `carevl.exe`
- Cấu hình cần thiết
- Kết nối Git bình thường
- Lệnh onboarding chuẩn cho tester hoặc trạm:

```powershell
$tmp="$env:TEMP\carevl-bootstrap-github.ps1"; Invoke-WebRequest "https://raw.githubusercontent.com/kanazawahere/carevl/main/Onboarding/Bootstrap-GitHub.ps1" -OutFile $tmp; powershell -ExecutionPolicy Bypass -File $tmp
```

Checklist:

- Máy mở được ứng dụng
- Repo là đúng repo dữ liệu
- Remote `origin` đúng
- Có thể đăng nhập GitHub trên máy

### Bước 5. Bàn giao cho trạm

Admin bàn giao:

- Tài khoản GitHub của trạm
- Cách đăng nhập lần đầu
- Cách thêm lượt khám mới
- Cách gửi dữ liệu về Hub
- Cách báo lỗi khi gặp sự cố

## 5. Quy trình admin kiểm tra sau onboard

Sau khi trạm đăng nhập lần đầu, admin cần kiểm tra:

- Trạm đăng nhập bằng đúng tài khoản trạm
- App hiện đúng tên trạm
- Lượt khám tạo mới gắn đúng station_id
- Dữ liệu push lên đúng branch của trạm

Checklist nghiệm thu:

- Tạo 1 lượt khám thử
- Kiểm tra commit đã sinh ra
- Kiểm tra push lên branch thành công
- Xác nhận Hub nhìn thấy branch và thay đổi mới

## 6. Công việc hàng ngày của admin

Admin hàng ngày hoặc theo chu kỳ cần:

- Theo dõi trạm nào đã gửi dữ liệu
- Xác nhận branch nào có cập nhật mới
- Tiếp nhận dữ liệu từ từng branch trạm
- Merge branch trạm vào `main`
- Tổng hợp báo cáo nếu cần

Checklist vận hành hàng ngày:

- Đã kiểm tra các branch trạm có dữ liệu mới
- Đã ghi nhận trạm nào chưa gửi dữ liệu
- Đã merge các branch hợp lệ
- Đã ghi nhận branch gặp lỗi hoặc conflict

## 7. Quy trình tiếp nhận và merge dữ liệu

### Bước 1. Xác định branch có dữ liệu mới

Admin kiểm tra danh sách branch trạm và xác định branch nào có commit mới.

Mục tiêu:

- Biết trạm nào đã gửi dữ liệu
- Biết trạm nào chưa gửi
- Biết branch nào cần review

### Bước 2. Review thay đổi

Trước khi merge, admin cần review tối thiểu:

- Dữ liệu SQLite của trạm có được commit đúng vào repo dữ liệu
- Không có thay đổi bất thường ở file cấu hình
- Không có thay đổi không liên quan đến dữ liệu

Nếu branch chỉ chứa thay đổi SQLite dữ liệu đúng quy ước thì có thể merge theo quy trình thường.

### Bước 3. Merge vào nhánh tổng hợp

Admin merge từng branch trạm vào `main`.

Sau merge:

- Ghi nhận trạm đã được tiếp nhận dữ liệu
- Cập nhật theo dõi nội bộ nếu cần

### Bước 4. Xử lý sau merge

Admin cần:

- Kiểm tra `main` ổn định
- Báo cáo nếu có branch lỗi
- Ghi nhận conflict nếu có

## 8. Cách xử lý các tình huống nghiệp vụ thường gặp

### Tình huống 1. Trạm không đăng nhập được

Admin kiểm tra:

- Tài khoản có đúng là tài khoản trạm không
- Tài khoản đã vào repo private chưa
- Trạm đã accept lời mời GitHub chưa
- Máy có mạng không

Hướng xử lý:

- Nếu chưa có quyền repo thì cấp quyền lại
- Nếu sai tài khoản thì yêu cầu đăng xuất và đăng nhập lại đúng tài khoản trạm
- Nếu lỗi mạng thì hướng dẫn thử lại khi có mạng

### Tình huống 2. Trạm đăng nhập được nhưng hiện sai tên trạm

Admin kiểm tra:

- Branch hiện tại của máy
- Mapping trong file metadata trạm
- Tài khoản đăng nhập có đúng với branch vận hành không

Hướng xử lý:

- Chỉnh lại branch
- Chỉnh lại metadata
- Không cho trạm nhập liệu thật nếu nhận diện trạm chưa đúng

### Tình huống 3. Trạm lưu dữ liệu được nhưng push thất bại

Admin kiểm tra:

- Quyền push của tài khoản trạm
- Remote `origin`
- Branch có đúng quy ước không
- Kết nối mạng

Hướng xử lý:

- Nếu lỗi quyền thì cấp quyền lại
- Nếu sai remote thì cấu hình lại repo
- Nếu lỗi branch thì đưa về đúng branch trạm
- Nếu chỉ do mất mạng thì hướng dẫn push lại sau

### Tình huống 4. Trạm push dữ liệu lên nhưng Hub chưa thấy trong báo cáo tổng hợp

Nguyên nhân thường gặp:

- Dữ liệu mới chỉ nằm trên branch trạm
- Chưa merge vào `main`
- Chưa chạy lại bước aggregate/build Hub DuckDB sau khi merge

Hướng xử lý:

- Admin review branch trạm
- Merge branch vào `main`
- Mở `CareVL Admin.bat`
- Chạy aggregate rồi build Hub DuckDB trong `Admin App`

### Tình huống 5. Conflict khi merge

Admin cần:

- Tạm dừng merge branch đó
- Xác định file xung đột
- Đánh giá đó là xung đột dữ liệu hay xung đột cấu hình
- Xử lý thủ công ở cấp Hub

Nguyên tắc:

- Trạm không tự ý sửa lịch sử Git
- Conflict tổng hợp là trách nhiệm của Hub/Admin

### Tình huống 6. Đổi người vận hành tại trạm

Nếu trạm không đổi:

- Không tạo danh tính mới
- Tiếp tục dùng tài khoản trạm
- Bàn giao nội bộ trong trạm

Admin chỉ cần hỗ trợ nếu:

- Cần đổi mật khẩu
- Cần thu hồi token cũ
- Cần hướng dẫn đăng nhập lại trên máy

### Tình huống 7. Thêm trạm mới

Admin lặp lại đầy đủ quy trình onboard trạm mới.

Không được:

- Dùng chung tài khoản của trạm cũ
- Dùng chung branch của trạm cũ
- Gộp 2 trạm vào một danh tính vận hành

## 9. Quy trình thu hồi hoặc tạm dừng một trạm

Khi trạm ngừng sử dụng hệ thống tạm thời hoặc vĩnh viễn, admin cần:

- Thu hồi hoặc đổi thông tin đăng nhập tài khoản trạm
- Kiểm tra dữ liệu đã được push đầy đủ chưa
- Merge hết dữ liệu còn tồn đọng nếu cần
- Ghi nhận trạng thái trạm trong quản lý nội bộ

Nếu trạm đổi máy:

- Kiểm tra máy cũ đã đồng bộ xong
- Đăng nhập lại tài khoản trạm trên máy mới
- Kiểm tra branch và metadata trước khi vận hành tiếp

## 10. Điều admin không được làm

- Không quản lý chính thức theo tài khoản cá nhân
- Không cho 2 trạm dùng chung 1 danh tính vận hành
- Không merge vô điều kiện khi branch có thay đổi bất thường
- Không bỏ qua bước review khi nghi có sai metadata hoặc sai branch
- Không hướng dẫn trạm xóa dữ liệu local để xử lý sự cố nếu chưa kiểm tra kỹ

## 11. Checklist nhanh cho admin

### Khi thêm trạm mới

- Đã cấp tài khoản GitHub cho trạm
- Đã cấp quyền repo
- Đã thống nhất tên branch
- Đã thêm metadata trạm
- Đã chuẩn bị máy và app
- Đã test đăng nhập
- Đã test tạo 1 lượt khám mẫu
- Đã test push

### Khi nhận dữ liệu hàng ngày

- Đã xem branch nào có dữ liệu mới
- Đã review thay đổi
- Đã merge branch hợp lệ vào `main`
- Đã ghi nhận branch lỗi nếu có

### Khi có sự cố

- Xác định lỗi nằm ở đăng nhập, branch, metadata, quyền repo hay mạng
- Không yêu cầu trạm thao tác nguy hiểm với Git nếu chưa xác minh
- Ghi nhận và xử lý theo đúng cấp trách nhiệm

## 12. Kết luận

Admin không chỉ là người cấp quyền kỹ thuật mà còn là đầu mối bảo đảm mô hình `quản lý theo trạm` được vận hành đúng.

Nguyên tắc cần nhớ:

- Quản lý theo trạm
- Mỗi trạm một danh tính
- Mỗi trạm một branch
- Hub nhận và merge dữ liệu
- Mọi sai lệch về tài khoản, branch hoặc metadata đều phải xử lý sớm trước khi dữ liệu đi xa hơn

