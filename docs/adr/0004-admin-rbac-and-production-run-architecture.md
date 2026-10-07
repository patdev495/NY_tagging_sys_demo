# 0004. Phân quyền Admin-QA và Kiến trúc Quản trị Đợt Sản Xuất

## Bối cảnh và Quyết định

Hệ thống đóng gói tem NY Tagging System cần mở rộng phân hệ Quản trị (Admin) để phục vụ đồng thời bộ phận Vận hành/Kỹ thuật và bộ phận Đảm bảo chất lượng (QA). Trước đây, phân hệ quản trị chỉ sử dụng mật khẩu tĩnh `admin123` trên trình duyệt và thiếu hoàn toàn khả năng theo dõi lệnh sản xuất cũng như xuất báo cáo dữ liệu.

Chúng tôi quyết định:
1. **Phân quyền vai trò (Role-Based Access Control - RBAC)**: Quản lý tài khoản trong bảng `users` với 2 vai trò chuẩn: `Admin` (toàn quyền cấu hình, CRUD, xóa thùng, reprint) và `QA` (chỉ đọc, tra cứu S/N, theo dõi tiến độ và xuất báo cáo Excel). Quyền hạn được kiểm soát nghiêm ngặt ở cả tầng API Backend (trả về `403 Forbidden` đối với các phương thức ghi/xóa/in lại của QA) và ẩn nút trên giao diện Frontend.
2. **Kiến trúc Quản lý Đợt Sản Xuất (Production Run Tracking)**: Hợp nhất giao diện giám sát tiến độ đóng gói theo 2 cơ chế:
   - Tab **Job Orders**: Dành cho chế độ `item_scan` (khách hàng UI), theo dõi tiến độ cấp phát và quét các vị trí thùng (`JobOrderCartonSlot` từ 1..N, trạng thái `PENDING`, `SCANNED`, `shipped`).
   - Tab **PO / Lot Runs**: Dành cho chế độ `weight_scale` (khách hàng A11), theo dõi sản lượng tổng hợp theo cặp `PO Number` và `Lot Number`.
3. **Báo cáo và Truy xuất nguồn gốc**: Hỗ trợ xuất dữ liệu ra file Excel (`.xlsx`) ở 2 cấp độ: Báo cáo tổng hợp cấp thùng (`Carton`) và Bảng kê chi tiết sê-ri con (`Carton Item`).
4. **Chuẩn hóa Mẫu tem**: Thay thế việc nhập chuỗi đường dẫn tự do bằng danh mục file `.btw` được chọn từ thư mục template chuẩn của hệ thống (`resources/templates/`).
