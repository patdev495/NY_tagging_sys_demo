# REQUIREMENTS.md

## Milestone v3.0: Admin Dashboard & Statistics

### Admin Infrastructure (ADMIN)
- [ ] **ADMIN-01**: Thiết lập Dashboard Layout với Sidebar navigation (Packing Station vs Admin).
- [ ] **ADMIN-02**: Quản lý trạng thái xác thực/phân quyền cơ bản (Placeholder cho tương lai).
- [ ] **ADMIN-03**: Tích hợp thư viện đồ thị (e.g., Chart.js hoặc Vue-ECharts).

### Data Management (DATA)
- [ ] **DATA-01**: CRUD Khách hàng (Customer): Xem danh sách, thêm mới, cập nhật thông tin, xóa.
- [ ] **DATA-02**: CRUD Sản phẩm (Product): Quản lý thông tin SKU, định mức QTY, gán mẫu tem.
- [ ] **DATA-03**: Quản lý Carton: Tra cứu lịch sử đóng gói, xem chi tiết các S/N bên trong một thùng.
- [ ] **DATA-04**: Backend API endpoints hỗ trợ đầy đủ các thao tác CRUD cho MSSQL.

### Statistics & Search (STATS)
- [ ] **STATS-01**: Dashboard Tổng quan: Hiển thị tổng số thùng đã đóng, số lượng sản phẩm đã xử lý trong ngày.
- [ ] **STATS-02**: Báo cáo theo sản phẩm: Thống kê số lượng carton/qty theo từng sản phẩm trong khoảng thời gian.
- [ ] **STATS-03**: Tìm kiếm nâng cao: Tìm kiếm vị trí của một S/N sản phẩm (thuộc Carton nào, ngày nào, khách hàng nào).
- [ ] **STATS-04**: Export dữ liệu (Excel/CSV) cho các báo cáo thống kê.
### Internationalization (I18N)
- [ ] **I18N-01**: Hỗ trợ đa ngôn ngữ (Tiếng Anh & Tiếng Việt) cho toàn bộ giao diện hệ thống.

## Future Requirements
- [ ] Quản lý người dùng và phân quyền chi tiết (RBAC).
- [ ] Auto-update product catalog từ ERP từ xa.
- [ ] Quản lý cấu hình hệ thống (Settings) tập trung tại Backend.

## Out of Scope
- [ ] **Inventory Management**: Không quản lý tồn kho tổng (chỉ quản lý dữ liệu đã đóng gói).
- [ ] **User Authentication**: Phân quyền chi tiết (chỉ làm placeholder ở milestone này).

## Traceability
| REQ-ID | Phase | Status |
|--------|-------|--------|
| ADMIN-01 | 21 | Pending |
| ADMIN-02 | 21 | Pending |
| ADMIN-03 | 24 | Pending |
| DATA-01 | 22 | Pending |
| DATA-02 | 22 | Pending |
| DATA-03 | 23 | Pending |
| DATA-04 | 22, 23 | Pending |
| STATS-01 | 24 | Pending |
| STATS-02 | 24 | Pending |
| STATS-03 | 23 | Pending |
| STATS-04 | 24 | Pending |
| I18N-01 | 26 | Pending |
| UI-CLEANUP | 28 | Pending |
| UI-RESPONSIVE | 27 | Pending |
