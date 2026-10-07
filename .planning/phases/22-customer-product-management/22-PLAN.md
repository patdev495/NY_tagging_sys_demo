# Phase 22: Customer & Product Management - Plan

## Goal
Xây dựng đầy đủ tính năng quản lý (CRUD) Khách hàng và Sản phẩm.

## Requirements
- **DATA-01**: CRUD Khách hàng (Customer).
- **DATA-02**: CRUD Sản phẩm (Product).
- **DATA-04**: Backend API endpoints hỗ trợ CRUD cho MSSQL.

---

## Execution Plan

### Wave 1: Backend CRUD
- [ ] **Task 1**: Cập nhật Customer API.
    - **Action**: Bổ sung POST, PUT, DELETE vào `customer/router.py`, `service.py` và `schemas.py`.
- [ ] **Task 2**: Cập nhật Product API.
    - **Action**: Bổ sung POST, PUT, DELETE vào `product/router.py`, `service.py` và `schemas.py`.

### Wave 2: Frontend Data Access
- [ ] **Task 3**: Cập nhật Frontend API layers.
    - **Action**: Bổ sung các hàm call API (create, update, delete) vào `catalog/api.js`.

### Wave 3: Frontend Management UI
- [ ] **Task 4**: Xây dựng trang Quản lý Khách hàng.
    - **Action**: Tạo `src/views/admin/CustomerManagementPage.vue` với bảng và form thêm/sửa.
- [ ] **Task 5**: Xây dựng trang Quản lý Sản phẩm.
    - **Action**: Tạo `src/views/admin/ProductManagementPage.vue` với bảng và form thêm/sửa.
- [ ] **Task 6**: Cấu hình Routing.
    - **Action**: Cập nhật `router/index.js` để trỏ đúng vào các trang quản lý mới.

---

## Verification Plan

### Automated Tests
- Kiểm tra API bằng Swagger (`/docs`): Thử tạo, sửa, xóa một khách hàng và sản phẩm test.
- Kiểm tra tính duy nhất: Thử tạo khách hàng trùng mã (code) -> Phải báo lỗi.

### Manual Verification (UAT)
- [ ] Thêm một Khách hàng mới -> Kiểm tra trong DB.
- [ ] Sửa tên Khách hàng -> Kiểm tra giao diện cập nhật.
- [ ] Thêm Sản phẩm cho Khách hàng vừa tạo.
- [ ] Xóa một Sản phẩm test.
- [ ] Kiểm tra tính năng tìm kiếm trên bảng.

---

## Must Haves (Goal-Backward)
- Phải có giao diện quản lý Khách hàng và Sản phẩm.
- Mọi thay đổi trên UI phải được lưu vào Database MSSQL 2008.
- Thông báo thành công/lỗi phải hiển thị rõ ràng cho người dùng.
