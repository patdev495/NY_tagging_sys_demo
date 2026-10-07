# Phase 23: Carton Explorer & Advanced Search - Plan

## Goal
Xây dựng công cụ tra cứu lịch sử đóng gói và tìm kiếm nâng cao.

## Requirements
- **DATA-03**: Quản lý Carton (Tra cứu lịch sử, xem chi tiết).
- **DATA-04**: Backend API endpoints hỗ trợ truy vấn lịch sử.
- **STATS-03**: Tìm kiếm nâng cao (Tìm vị trí của S/N sản phẩm).

---

## Execution Plan

### Wave 1: History API Enhancement
- [ ] **Task 1**: Mở rộng History API.
    - **Action**: 
        - Cập nhật `history/router.py`: Thêm `GET /cartons` (list/filter) và `GET /cartons/item-search`.
        - Cập nhật `history/service.py`: Triển khai logic tìm kiếm và join bảng.
        - Cập nhật `history/schemas.py`: Thêm các schema cho list và detail view.

### Wave 2: Frontend Data Access
- [ ] **Task 2**: Cập nhật Frontend History API.
    - **Action**: Tạo/Cập nhật `frontend_v2/src/features/history/api.js`.

### Wave 3: History Explorer UI
- [ ] **Task 3**: Xây dựng trang Lịch sử Carton.
    - **Action**: Tạo `src/views/admin/CartonHistoryPage.vue` với bảng dữ liệu và Modal xem chi tiết nội dung thùng.
- [ ] **Task 4**: Xây dựng trang Tra cứu S/N sản phẩm.
    - **Action**: Tạo `src/views/admin/SNLookupPage.vue` cho phép nhập S/N sản phẩm để tìm thùng tương ứng.
- [ ] **Task 5**: Cấu hình Routing.
    - **Action**: Cập nhật `router/index.js` cho các trang lịch sử.

---

## Verification Plan

### Automated Tests
- Kiểm tra API: 
    - `GET /cartons?limit=10` -> Trả về đúng 10 bản ghi gần nhất.
    - `GET /cartons/item-search?item_sn=XYZ` -> Trả về Carton chứa S/N XYZ.

### Manual Verification (UAT)
- [ ] Tìm kiếm một Carton S/N cụ thể -> Hiển thị đúng thông tin.
- [ ] Click xem chi tiết một thùng -> Hiển thị đủ danh sách S/N sản phẩm bên trong.
- [ ] Dùng công cụ "Tra cứu S/N" -> Nhập một S/N đã quét -> Hệ thống tìm ra đúng thùng chứa nó.
- [ ] Kiểm tra lọc theo Khách hàng / Sản phẩm.

---

## Must Haves (Goal-Backward)
- Người dùng phải xem được danh sách toàn bộ thùng đã đóng.
- Phải xem được nội dung (Item S/Ns) bên trong mỗi thùng.
- Phải tìm được thùng từ mã S/N sản phẩm.
