# 3. Triển khai Hệ thống lên Windows Server qua Native UV và 1-Click SSH Deploy

Date: 2026-08-28

## Status

Accepted

## Context

Trước đây, mỗi lần có cập nhật mã nguồn (Backend hoặc Frontend), lập trình viên phải:
1. Chạy PyInstaller (`build_v2.bat`) để đóng gói Backend thành file `.exe` kích thước lớn.
2. Nén toàn bộ thư mục `release/` (hàng chục đến hàng trăm MB).
3. Đăng nhập Remote Desktop (RDP) vào Windows Server, copy đè file và khởi động lại ứng dụng thủ công.

Quy trình này gây tốn nhiều thời gian (3-5 phút mỗi lần), dễ phát sinh lỗi thiếu phụ thuộc C-extensions trong thư mục `_internal/` của PyInstaller, và cản trở việc phát hành các bản vá lỗi nhanh trên dây chuyền sản xuất.

## Decision

Chúng tôi quyết định chuyển đổi toàn bộ quy trình triển khai trên Central Server (máy Windows 11 / Windows Server tại xưởng) sang mô hình **Native Python (UV) + Windows Service (NSSM) + 1-Click Remote Deploy qua SSH**:

1. **Loại bỏ đóng gói PyInstaller `.exe` cho Server**: Server chạy trực tiếp mã nguồn Backend qua trình quản lý `uv` (`uv run uvicorn main:app`).
2. **Phục vụ Frontend SPA tập trung**: Frontend Vue 3 được build thành static assets và tích hợp vào thư mục `backend_v2/static` để FastAPI phục vụ trực tiếp.
3. **Quản lý tiến trình bằng NSSM Windows Service**: Backend được đăng ký thành Windows Service mang tên `NY_Tagging_Backend`, tự động khởi động cùng hệ điều hành và tự phục hồi khi crash mà không cần user đăng nhập GUI.
4. **Tự động hóa 1-Click qua SSH**: Tạo kịch bản `deploy_to_server.ps1` trên máy Dev. Khi thực thi, script tự build Frontend, push code lên Git và kích hoạt lệnh cập nhật từ xa qua SSH (`git pull && uv sync && nssm restart`).

## Consequences

### Positive
- **Tốc độ triển khai vượt trội**: Thời gian cập nhật từ máy Dev lên Server giảm từ 3-5 phút xuống còn **dưới 10 giây**.
- **Không cần Remote Desktop**: Mọi thao tác cập nhật được thực hiện tự động và an toàn qua SSH key.
- **Tiết kiệm tài nguyên**: Không cần máy ảo Docker hay bộ nhớ đệm PyInstaller, tiến trình chỉ tiêu tốn ~50-100MB RAM.
- **Độ ổn định cao**: NSSM duy trì service chạy liên tục trên Windows kể cả khi khởi động lại máy hoặc không có phiên làm việc người dùng.

### Negative / Trade-offs
- Máy Server cần có kết nối mạng để kéo mã nguồn từ Git và phải bật tính năng Windows OpenSSH Server.
- Cần cấu hình đúng quyền NTFS cho `administrators_authorized_keys` trên Windows.
