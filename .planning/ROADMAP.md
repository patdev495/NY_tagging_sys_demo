# ROADMAP.md

## Milestone 1: Foundation & Packing Station MVP
**Goal**: Build a functional packing station that can scan items, generate S/Ns, and record data to MSSQL 2008.
- [x] Phase 1-3: Completed

## Milestone 2: Feature-Based Architecture Refactoring (v2.0)
**Goal**: Modularize the codebase into feature-based modules.
- [x] Phase 11-14: Completed

---
## Milestone 3: Admin Dashboard & Statistics (v3.0)
**Goal**: Xây dựng hệ thống quản lý và thống kê dữ liệu toàn diện.

### Phase 21: Admin UI Shell & Navigation
**Goal**: Thiết lập khung giao diện Admin và hệ thống điều hướng.
**Requirements**: ADMIN-01, ADMIN-02
**Success Criteria**:
1. Có Sidebar cho phép chuyển đổi giữa "Packing Station" và "Admin Dashboard".
2. Hệ thống routing (Vue Router) hoạt động ổn định.
3. Giao diện khung (Layout) đồng nhất và hiện đại.

### Phase 22: Customer & Product Management
**Goal**: Triển khai các tính năng CRUD cho Khách hàng và Sản phẩm.
**Requirements**: DATA-01, DATA-02, DATA-04
**Success Criteria**:
1. Backend hỗ trợ các phương thức POST, PUT, DELETE cho Customer/Product.
2. Frontend có các form thêm/sửa và bảng danh sách.
3. Dữ liệu được cập nhật trực tiếp vào MSSQL 2008.

### Phase 23: Carton Explorer & Advanced Search
**Goal**: Quản lý lịch sử đóng gói và tra cứu chi tiết.
**Requirements**: DATA-03, DATA-04, STATS-03
**Success Criteria**:
1. Trang tra cứu Carton cho phép xem chi tiết nội dung (Item S/Ns) bên trong.
2. Công cụ tìm kiếm S/N sản phẩm hoạt động chính xác (tìm ra Carton chứa S/N đó).
3. Hiệu suất truy vấn SQL được tối ưu hóa cho dữ liệu lớn.

### Phase 24: Statistics Dashboard & Reports
**Goal**: Hiển thị báo cáo và đồ thị thống kê.
**Requirements**: ADMIN-03, STATS-01, STATS-02, STATS-04
**Success Criteria**:
1. Dashboard hiển thị các biểu đồ (Bar/Pie chart) về lượng carton theo sản phẩm.
2. Thống kê năng suất theo ngày/tháng được hiển thị trực quan.
3. Chức năng Export CSV/Excel hoạt động cho các báo cáo.

### Phase 25: Database Schema Auto-Initialization
**Goal**: Tự động tạo cấu trúc bảng (schema) khi Backend khởi chạy.
**Requirements**: DATA-BOOTSTRAP
**Success Criteria**:
1. Backend tự động tạo các bảng `customers`, `products`, `cartons`, `carton_items` nếu chưa có.
2. Không làm mất dữ liệu nếu các bảng đã tồn tại.
3. Có log thông báo trạng thái khởi tạo DB.

Plans:
- [ ] .planning/phases/25-database-schema-auto-initialization/25-PLAN.md

### Phase 26: Thêm hỗ trợ ngôn ngữ tiếng Việt (Internationalization)
**Goal:** Tích hợp đa ngôn ngữ (EN/VI) cho toàn bộ giao diện Frontend.
**Requirements**: UI-I18N
**Success Criteria**:
1. Hệ thống hỗ trợ chuyển đổi linh hoạt giữa Tiếng Anh và Tiếng Việt.
2. Trạng thái ngôn ngữ được lưu trữ bền vững (persistent) trong LocalStorage.
3. Toàn bộ các chuỗi ký tự cứng trong UI chính (Packing Station, Admin History) được chuyển sang tệp dịch.

Plans:
- [x] .planning/phases/26-internationalization/26-PLAN.md

### Phase 27: Responsive hệ thống với mọi kích thước màn hình
**Goal:** Restore and optimize the responsive layout for Desktop, Laptop, and Mobile following the TS/Tailwind migration.
**Requirements**: UI-RESPONSIVE
**Depends on:** Phase 26
**Status**: [x] Completed

### Phase 28: Convert all CSS to Tailwind CSS for cleaner code
**Goal:** Chuyển đổi toàn bộ mã CSS hiện tại sang Tailwind CSS để mã nguồn gọn gàng và dễ bảo trì hơn.
**Requirements**: UI-CLEANUP
**Status**: [x] Completed

### Phase 29: Migrate frontend to TypeScript for better maintainability
**Goal:** [x] Migrated all frontend logic to TypeScript for better type safety and DX.
**Requirements**: UI-STABILITY
**Depends on:** Phase 28
**Status**: [x] Completed

### Phase 30: Automated Testing Suite Implementation
**Goal**: Implement unit and integration tests for core business logic (S/N generation, Packing logic) to reduce manual regression testing.
**Requirements**: TEST-01, TEST-02
**Depends on:** Phase 29
**Status**: [x] Completed

### Phase 31: Deploy to Render (Unified Service)
**Goal**: Triển khai hệ thống lên Render với một dịch vụ duy nhất, phục vụ cả Backend và Frontend (từ thư mục static) và đính kèm dữ liệu hiện tại.
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03
**Success Criteria**:
1. Frontend được build và copy vào thư mục `static` của Backend.
2. Backend (FastAPI) phục vụ toàn bộ file tĩnh từ thư mục `static`.
3. Dự án chạy được trên Render (môi trường Linux/Docker) với SQLite database đính kèm.
4. Truy cập được qua domain `.onrender.com`.

---

## Milestone 999: Backlog
- [ ] Auto-update product catalog from remote ERP if needed.
- [ ] Support for multiple locations (VN vs CN selection).
- [ ] Phân quyền người dùng chi tiết (RBAC).
