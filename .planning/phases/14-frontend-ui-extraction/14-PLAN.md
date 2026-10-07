---
wave: 1
depends_on: []
files_modified:
  - frontend_v2/package.json
  - frontend_v2/src/main.js
  - frontend_v2/src/core/stores/settings.js
  - frontend_v2/src/core/stores/system.js
  - frontend_v2/src/core/components/AppHeader.vue
  - frontend_v2/src/core/components/Notification.vue
  - frontend_v2/src/features/catalog/components/CatalogSelection.vue
  - frontend_v2/src/features/packing/components/SessionHeader.vue
  - frontend_v2/src/features/packing/components/ScanBuffer.vue
  - frontend_v2/src/features/packing/components/ScannedList.vue
  - frontend_v2/src/features/print/components/PrintStatusBanner.vue
  - frontend_v2/src/features/settings/components/SettingsModal.vue
  - frontend_v2/src/features/print/components/EmergencyReprintModal.vue
  - frontend_v2/src/views/PackingPage.vue
  - frontend_v2/src/App.vue
autonomous: true
---

# Phase 14: Frontend UI Extraction

## Goal
Tách `PackingStation.vue` thành các component nhỏ, sử dụng Pinia để quản lý state và Scoped CSS để đóng gói giao diện.

## Requirements Covered
- FRONT-02, FRONT-03, FRONT-05, FRONT-07, FRONT-08, FRONT-09.

## Verification Criteria
- [ ] Ứng dụng chạy được bằng lệnh `npm run dev` trong `frontend_v2`.
- [ ] Các tính năng: Chọn sản phẩm, quét mã, hiển thị lỗi, in tem, cài đặt đều hoạt động như cũ.
- [ ] Không còn component `PackingStation.vue` nguyên khối.

## Tasks

```xml
<task id="pinia_setup" title="Setup Pinia and Global Stores">
  <action>
    - Cập nhật `package.json` thêm `pinia`.
    - Cập nhật `main.js` để sử dụng Pinia.
    - Tạo `src/core/stores/settings.js` để quản lý cấu hình station.
    - Tạo `src/core/stores/system.js` để quản lý kết nối và thông báo.
  </action>
</task>

<task id="ui_extraction_core" title="Extract Core UI Components">
  <action>
    - Tạo `src/core/components/AppHeader.vue`.
    - Tạo `src/core/components/Notification.vue`.
    - Trích xuất HTML/CSS tương ứng từ `PackingStation.vue`.
  </action>
</task>

<task id="ui_extraction_catalog" title="Extract Catalog Components">
  <action>
    - Tạo `src/features/catalog/components/CatalogSelection.vue`.
    - Di chuyển logic chọn khách hàng/sản phẩm sang đây.
  </action>
</task>

<task id="ui_extraction_packing" title="Extract Packing Components">
  <action>
    - Tạo `src/features/packing/components/SessionHeader.vue`.
    - Tạo `src/features/packing/components/ScanBuffer.vue`.
    - Tạo `src/features/packing/components/ScannedList.vue`.
    - Kết nối với `useScanLogic` composable.
  </action>
</task>

<task id="ui_extraction_modals" title="Extract Modals and Print Status">
  <action>
    - Tạo `src/features/settings/components/SettingsModal.vue`.
    - Tạo `src/features/print/components/EmergencyReprintModal.vue`.
    - Tạo `src/features/print/components/PrintStatusBanner.vue`.
  </action>
</task>

<task id="orchestration" title="Build Orchestrator (PackingPage)">
  <action>
    - Tạo `src/views/PackingPage.vue`.
    - Lắp ghép tất cả các component trên thành một trang hoàn chỉnh.
    - Cập nhật `App.vue` để render `PackingPage.vue`.
    - Xóa `PackingStation.vue` sau khi hoàn tất.
  </action>
</task>
```
