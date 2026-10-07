---
wave: 1
depends_on: []
files_modified:
  - backend_v2/src/core/config.py
  - backend_v2/src/core/database.py
  - backend_v2/src/core/exceptions.py
  - backend_v2/src/core/models.py
  - backend_v2/src/features/customer/schemas.py
  - backend_v2/src/features/customer/service.py
  - backend_v2/src/features/customer/router.py
  - backend_v2/src/features/product/schemas.py
  - backend_v2/src/features/product/service.py
  - backend_v2/src/features/product/router.py
  - backend_v2/src/features/history/schemas.py
  - backend_v2/src/features/history/service.py
  - backend_v2/src/features/history/router.py
  - backend_v2/main.py
  - backend_v2/requirements.txt
autonomous: true
---

# Phase 11: Backend Scaffold & Read-Only Features

## Goal
Thiết lập cấu trúc lõi backend và tách các tính năng đọc dữ liệu (Customer, Product, Carton Search). Chạy `backend_v2` độc lập với port 8001 để đối chiếu với `backend`.

## Requirements Covered
- BACK-01: Tách Customer router và service
- BACK-02: Tách Product router và service
- BACK-05: Tách History (Search/Reprint) router/service

## Verification Criteria
- [ ] Chạy `uvicorn main:app --port 8001` trong `backend_v2` thành công, không có lỗi import.
- [ ] Truy cập `http://localhost:8001/api/v1/customers` trả về danh sách khách hàng.
- [ ] Truy cập `http://localhost:8001/api/v1/customers/1/products` trả về danh sách sản phẩm.
- [ ] Lệnh kiểm tra cấu trúc thư mục đảm bảo `backend` không bị sửa đổi.

## Tasks

```xml
<task id="scaffold_core" title="Scaffold backend_v2 core structure">
  <read_first>
    - backend/main.py
    - backend/database.py
    - backend/models.py
    - backend/requirements.txt (if exists)
  </read_first>
  <action>
    - Tạo thư mục `backend_v2/src/core`.
    - Tạo file `backend_v2/requirements.txt` với nội dung tương tự `backend/requirements.txt` (hoặc các thư viện: fastapi, uvicorn, sqlalchemy, pyodbc/ceODBC, pydantic).
    - Sao chép `backend/database.py` sang `backend_v2/src/core/database.py`.
    - Sao chép `backend/models.py` sang `backend_v2/src/core/models.py` mà KHÔNG thay đổi gì. Cập nhật import `from .database import Base` (thêm dot relative import).
    - Tạo `backend_v2/src/core/config.py` chứa class `Settings` với `API_PORT = 8001` và `DATABASE_URL` từ môi trường (hoặc chuỗi kết nối MSSQL mặc định nếu có trong codebase).
    - Tạo `backend_v2/src/core/exceptions.py` với một hàm `custom_http_exception_handler(request, exc)` trả về `JSONResponse(status_code=exc.status_code, content={"error": exc.detail})`.
  </action>
  <acceptance_criteria>
    - Lệnh `ls backend_v2/src/core/models.py` thành công.
    - File `backend_v2/src/core/exceptions.py` chứa `custom_http_exception_handler`.
  </acceptance_criteria>
</task>

<task id="feature_customer" title="Extract Customer Feature">
  <read_first>
    - backend/schemas.py
    - backend/main.py
  </read_first>
  <action>
    - Tạo thư mục `backend_v2/src/features/customer`.
    - Tạo `schemas.py`: sao chép class `Customer` và `CustomerCreate` (nếu có) từ `backend/schemas.py`.
    - Tạo `service.py`: viết hàm `get_all_customers(db: Session)` thực hiện `db.query(models.Customer).all()`.
    - Tạo `router.py`: tạo `APIRouter(prefix="/customers", tags=["Customers"])`, định nghĩa endpoint `GET /` gọi service `get_all_customers(db)`.
  </action>
  <acceptance_criteria>
    - File `backend_v2/src/features/customer/router.py` chứa `APIRouter`.
    - Hàm `get_all_customers` trong `service.py` trả về danh sách khách hàng.
  </acceptance_criteria>
</task>

<task id="feature_product" title="Extract Product Feature">
  <read_first>
    - backend/schemas.py
    - backend/main.py
  </read_first>
  <action>
    - Tạo thư mục `backend_v2/src/features/product`.
    - Tạo `schemas.py`: sao chép class `Product` từ `backend/schemas.py`.
    - Tạo `service.py`: viết hàm `get_products_by_customer(customer_id: int, db: Session)` thực hiện logic query sản phẩm theo `customer_id`.
    - Tạo `router.py`: tạo `APIRouter(prefix="/customers", tags=["Products"])` (lưu ý prefix để mount chuẩn REST), định nghĩa endpoint `GET /{customer_id}/products` gọi service `get_products_by_customer(customer_id, db)`.
  </action>
  <acceptance_criteria>
    - File `backend_v2/src/features/product/router.py` chứa endpoint `/{customer_id}/products`.
  </acceptance_criteria>
</task>

<task id="feature_history" title="Extract History Feature (Read-only)">
  <read_first>
    - backend/schemas.py
    - backend/main.py
  </read_first>
  <action>
    - Tạo thư mục `backend_v2/src/features/history`.
    - Tạo `schemas.py`: sao chép class `Carton` và `CartonItem` từ `backend/schemas.py` (cần thiết để trả về info tìm kiếm).
    - Tạo `service.py`: viết hàm `search_carton_by_sn(carton_sn: str, db: Session)` để lấy thông tin thùng đã in thành công.
    - Tạo `router.py`: tạo `APIRouter(prefix="/cartons", tags=["History"])`, định nghĩa endpoint `GET /search` nhận tham số `carton_sn` và gọi service `search_carton_by_sn`.
  </action>
  <acceptance_criteria>
    - Lệnh `grep "search_carton_by_sn" backend_v2/src/features/history/service.py` có kết quả.
  </acceptance_criteria>
</task>

<task id="app_factory" title="Create App Factory and Main Entry">
  <read_first>
    - backend/main.py
  </read_first>
  <action>
    - Tạo `backend_v2/main.py`.
    - Xây dựng hàm `create_app() -> FastAPI`.
    - Gắn exception handler: `app.add_exception_handler(HTTPException, custom_http_exception_handler)`.
    - Khởi tạo base router `api_v1 = APIRouter(prefix="/api/v1")`.
    - Include các router từ `customer`, `product`, `history` vào `api_v1`.
    - Include `api_v1` vào `app`.
    - Cấu hình khối `if __name__ == "__main__":` chạy uvicorn với cổng `8001`.
    - Bỏ qua phần phục vụ giao diện tĩnh (Frontend Static Files) vì chúng ta sẽ dùng server riêng biệt cho `frontend_v2`.
  </action>
  <acceptance_criteria>
    - File `backend_v2/main.py` chứa `def create_app()`.
    - File `backend_v2/main.py` có import `uvicorn.run(app, port=8001)`.
  </acceptance_criteria>
</task>
```
