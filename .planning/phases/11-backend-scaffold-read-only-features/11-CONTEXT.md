# Phase 11 Context

## Domain
Thiết lập cấu trúc lõi backend và tách các tính năng đọc dữ liệu (Customer, Product, Carton Search).

## Decisions

### 1. Giao tiếp Database (Router & Service Layer)
* **Quyết định:** Đẩy việc gọi DB hoàn toàn vào Service layer. Service nhận Session từ Router.
* **Lý do:** Giúp Service xử lý logic cốt lõi, Router chỉ nhận Request/Response, dễ dàng viết test hơn.

### 2. Cấu trúc Schema (Pydantic)
* **Quyết định:** Đặt Schema ngay trong thư mục tính năng (ví dụ: `src/features/customer/schemas.py`).
* **Lý do:** Giúp đóng gói hoàn toàn logic của một feature, tránh phình to file schema chung.

### 3. Khởi tạo App (App Factory)
* **Quyết định:** Chuyển sang dùng pattern `create_app()` thay vì instance toàn cục.
* **Lý do:** Chuyên nghiệp hóa khởi tạo, dễ dàng truyền biến môi trường hoặc cấu hình khi test.

### 4. Xử lý Lỗi (Error Handling)
* **Quyết định:** Dùng Global Exception Handler (trong `core/exceptions.py`).
* **Lý do:** Chuẩn hóa JSON lỗi trả về cho Frontend, dễ bắt lỗi trên UI hơn.

## Implementation Constraints & User Notes

> [!WARNING]
> **BẢO TOÀN DATABASE:** Tuyệt đối KHÔNG thay đổi cấu trúc bảng, lược đồ (schema), relationship hay dữ liệu của database hiện tại. Mọi service mới phải tương thích hoàn toàn với schema cũ.

> [!IMPORTANT]
> **THƯ MỤC LÀM VIỆC MỚI (V2):** Để đảm bảo an toàn, yêu cầu tạo các thư mục mới là `backend_v2` và `frontend_v2`. **KHÔNG ĐƯỢC XÓA HAY SỬA** code trong thư mục `backend` và `frontend` cũ. Chúng ta sẽ review code cũ và sao chép/chỉnh sửa sang thư mục mới để dễ dàng đối chiếu hoặc rollback khi cần.

## Canonical Refs
- `backend/main.py` (Nguồn logic API cũ)
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
