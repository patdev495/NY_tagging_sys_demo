# Phase 21: Admin UI Shell & Navigation - Plan

## Goal
Thiết lập hệ thống điều hướng và khung giao diện Admin Dashboard.

## Requirements
- **ADMIN-01**: Thiết lập Dashboard Layout với Sidebar navigation.
- **ADMIN-02**: Quản lý trạng thái xác thực/phân quyền cơ bản.

## User Review Required
> [!IMPORTANT]
> Việc chuyển đổi sang Vue Router sẽ làm thay đổi cách ứng dụng khởi chạy. Tôi sẽ di chuyển logic từ `App.vue` sang các file layout chuyên biệt.

---

## Execution Plan

### Wave 1: Infrastructure & Routing
- [ ] **Task 1**: Cài đặt `vue-router`.
    - **Action**: Chạy `npm install vue-router@4` trong thư mục `frontend_v2`.
- [ ] **Task 2**: Thiết lập Router configuration.
    - **Action**: Tạo `frontend_v2/src/core/router/index.js` định nghĩa các route cho `/` và `/admin`.
    - **Read First**: `frontend_v2/src/main.js`
- [ ] **Task 3**: Tích hợp Router vào Main entry.
    - **Action**: Cập nhật `frontend_v2/src/main.js` để sử dụng router.

### Wave 2: Layout & Navigation
- [ ] **Task 4**: Xây dựng Sidebar component.
    - **Action**: Tạo `frontend_v2/src/core/components/Sidebar.vue` với thiết kế premium (glassmorphism, collapsible).
    - **Read First**: `frontend_v2/src/index.css`
- [ ] **Task 5**: Xây dựng Main Layout.
    - **Action**: Tạo `frontend_v2/src/core/layouts/MainLayout.vue` chứa Sidebar và `<router-view>`.
- [ ] **Task 6**: Cập nhật `App.vue`.
    - **Action**: Thay thế nội dung `App.vue` bằng `<router-view>` (hoặc bọc trong Layout nếu cần).

### Wave 3: Admin Dashboard Shell
- [ ] **Task 7**: Tạo trang Admin Dashboard ban đầu.
    - **Action**: Tạo `frontend_v2/src/views/admin/DashboardPage.vue` với các thống kê nhanh (Quick Stats placeholders).

---

## Verification Plan

### Automated Tests
- Kiểm tra build: `npm run build` không lỗi.
- Kiểm tra Router: Truy cập `/` và `/admin` không bị lỗi 404 trên dev server.

### Manual Verification (UAT)
- [ ] Mở ứng dụng, kiểm tra Sidebar có hiển thị không.
- [ ] Click vào nút "Admin" trên Sidebar -> Chuyển sang trang Dashboard.
- [ ] Click vào nút "Packing" -> Quay lại trạm đóng gói.
- [ ] Kiểm tra tính năng thu gọn/mở rộng Sidebar.
- [ ] Kiểm tra giao diện trên màn hình nhỏ.

---

## Must Haves (Goal-Backward)
- Ứng dụng phải có thanh Sidebar điều hướng.
- Người dùng có thể chuyển đổi giữa Packing và Admin Dashboard mà không mất trạng thái (Pinia store).
- Giao diện Admin phải mang lại cảm giác cao cấp và chuyên nghiệp.
