# 0012. Workstation Template File Inspection

## Context

Trên các màn hình quét mã và đóng gói của nhà máy (cả trạm `item_scan` của khách hàng UI và `weight_scale` của khách hàng Erro), công nhân và kỹ sư cần kiểm tra thực tế định dạng mẫu tem in (.btw BarTender) khi bắt đầu ca hoặc khi phát hiện cảnh báo thiếu mẫu tem.

Các tệp mẫu tem BarTender là định dạng nhị phân độc quyền (`.btw`) và được lưu trữ trên ổ đĩa cục bộ của máy tính trạm (`localTemplateDir`, mặc định `D:\PAT\Templates`). Trình duyệt web không thể đọc hoặc render trực tiếp tệp `.btw`. Tuy nhiên, mỗi máy trạm đều được cài đặt và vận hành ứng dụng **NY Print Agent** (`http://127.0.0.1:8080`) có quyền truy cập hệ điều hành Windows và BarTender COM.

## Decision

1. **Ủy quyền mở file cho Print Agent cục bộ**: Thay vì tải tệp hoặc xử lý render phức tạp trên server, web frontend gửi yêu cầu tới Print Agent tại `POST /open-template` truyền tham số `folder` và `filename`.
2. **Kích hoạt ứng dụng BarTender Designer GUI**: Print Agent kiểm tra sự tồn tại của tệp trên máy trạm Windows:
   - Nếu tồn tại: Tìm vị trí thực thi của `bartend.exe` (qua App Paths Registry hoặc Program Files) và gọi trực tiếp `subprocess.Popen([bartend_exe, f"/F={full_path}", "/MAX"])`. Cách này đảm bảo BarTender Designer mở cửa sổ GUI hiển thị trên màn hình máy tính trạm độc lập, tránh việc bị DDE nuốt lệnh vào tiến trình BarTender COM ngầm (`Visible = False`). Trường hợp không tìm thấy đường dẫn exe, sử dụng fallback qua `os.startfile(full_path)`.
   - Nếu không tồn tại: Trả về trạng thái `exists: false` cùng thông tin đường dẫn chi tiết và thông báo hướng dẫn.
3. **Mở thư mục tem qua File Explorer**: Bổ sung endpoint `POST /open-dir` trên Print Agent cho phép người dùng mở trực tiếp thư mục `D:\PAT\Templates` trên Windows Explorer bằng `os.startfile(folder)` khi cần sao chép tệp mẫu tem bị thiếu.
4. **Trực quan hóa tại trạm (UI & Erro)**:
   - Đặt nút hành động "Mở Mẫu Tem" cố định tại thanh thông tin Product trên cả 2 màn hình quét mã UI (`UIPackingPage.vue`) và Erro (`ErroPackingPage.vue`).
   - Tích hợp nút hành động nhanh trên banner cảnh báo thiếu file tem (`templateMissing`).
   - Hiển thị thông báo Modal cảnh báo rõ ràng khi file không tồn tại, cung cấp nút "Mở thư mục tem" và "Kiểm tra lại".
5. **Không hạn chế quyền Admin**: Cho phép thao tác mở xem mẫu tem trực tiếp tại trạm vận hành mà không yêu cầu đăng nhập Admin, phục vụ việc đối chiếu nhanh của công nhân/kỹ sư xưởng.

## Consequences

- Kỹ sư và người vận hành có thể đối chiếu thiết kế tem gốc 100% trên BarTender chỉ với một cú click chuột từ giao diện web.
- Trải nghiệm xử lý lỗi thiếu mẫu tem được cải thiện đáng kể nhờ khả năng mở ngay thư mục lưu trữ để copy file.
- Không gây tải xử lý trên máy chủ Backend vì việc mở tệp hoàn toàn diễn ra cục bộ trên máy trạm thông qua Print Agent.
