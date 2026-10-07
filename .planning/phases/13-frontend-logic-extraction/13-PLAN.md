---
wave: 1
depends_on: []
files_modified:
  - frontend_v2/src/core/api.js
  - frontend_v2/src/features/catalog/api.js
  - frontend_v2/src/features/packing/api.js
  - frontend_v2/src/features/print/api.js
  - frontend_v2/src/api.js
  - frontend_v2/src/features/packing/composables/useScanLogic.js
  - frontend_v2/src/features/print/composables/usePrintAgent.js
autonomous: true
---

# Phase 13: Frontend Logic Extraction

## Goal
Tách layer API nguyên khối và các logic xử lý nghiệp vụ (Composables) từ `PackingStation.vue` sang cấu trúc Feature-Based cho hệ thống Frontend mới (`frontend_v2`).

## Requirements Covered
- FRONT-01: Tách layer API theo domain (Product, Box, Printer)
- FRONT-04: Tách logic scan validation & đếm số lượng
- FRONT-06: Tách logic gọi Print Agent healthcheck

## Verification Criteria
- [ ] Thư mục `frontend_v2` được tạo và chứa đầy đủ cấu hình Vite, src.
- [ ] Không còn tồn tại file `frontend_v2/src/api.js`. Thay vào đó là các file `api.js` chuyên biệt trong từng feature.
- [ ] `useScanLogic.js` và `usePrintAgent.js` được tạo thành công với cấu trúc Composition API chuẩn của Vue.

## Tasks

```xml
<task id="scaffold_frontend" title="Scaffold Frontend V2">
  <read_first>
    - frontend/package.json
  </read_first>
  <action>
    - Copy toàn bộ thư mục `frontend` sang `frontend_v2` (Bao gồm src, public, package.json, vite.config.js...). Loại bỏ node_modules nếu có để nhẹ.
    - Đảm bảo quyền truy cập đọc/ghi bình thường trên thư mục mới.
    - Tạo các thư mục domain: `frontend_v2/src/features/catalog`, `frontend_v2/src/features/packing`, `frontend_v2/src/features/print`, `frontend_v2/src/features/settings`, `frontend_v2/src/core`.
  </action>
  <acceptance_criteria>
    - Thư mục `frontend_v2/src/features/catalog` tồn tại.
  </acceptance_criteria>
</task>

<task id="api_layer" title="Extract API Layer">
  <read_first>
    - frontend_v2/src/api.js
  </read_first>
  <action>
    - Tạo `frontend_v2/src/core/api.js`: Khởi tạo và export Axios instance (`baseURL: '/api/v1'`). Chú ý đã chuyển sang `v1`.
    - Tạo `frontend_v2/src/features/catalog/api.js`: export các hàm `getCustomers`, `getCustomerProducts`.
    - Tạo `frontend_v2/src/features/packing/api.js`: export `createCarton`, `getLastCarton`.
    - Tạo `frontend_v2/src/features/print/api.js`: export `updateCartonStatus`, `searchCarton`, `reprintCarton`.
    - Xóa file `frontend_v2/src/api.js` cũ.
  </action>
  <acceptance_criteria>
    - File `frontend_v2/src/api.js` không còn tồn tại.
    - File `frontend_v2/src/features/catalog/api.js` chứa hàm `getCustomers`.
  </acceptance_criteria>
</task>

<task id="composables_scan" title="Extract Scan Logic Composable">
  <action>
    - Tạo `frontend_v2/src/features/packing/composables/useScanLogic.js`.
    - Viết Composition hook `export function useScanLogic()` trả về các ref: `scannedItems`, `invalidScans`, `scanBuffer`.
    - Cung cấp hàm `validateAndAddScan(sn, currentProduct, snPattern)`:
      - Trả về đối tượng `{ success: boolean, error: string }`.
      - Kiểm tra độ dài, kiểm tra trùng lặp trong mảng hiện tại.
      - Nếu đúng pattern thì cho vào mảng `scannedItems`, sai thì báo lỗi.
    - Cung cấp hàm `resetScan()` xóa sạch state.
  </action>
  <acceptance_criteria>
    - File `useScanLogic.js` tồn tại và export `useScanLogic`.
  </acceptance_criteria>
</task>

<task id="composables_print" title="Extract Print Agent Composable">
  <action>
    - Tạo `frontend_v2/src/features/print/composables/usePrintAgent.js`.
    - Viết Composition hook `export function usePrintAgent()` trả về `isAgentConnected`, `agentErrorMessage`.
    - Viết hàm `checkAgentHealth()` dùng fetch ping `http://127.0.0.1:1234/status`. Timeout ngắn (1-2s). Update state `isAgentConnected`.
    - Viết hàm `sendPrintJob(btxml_content, carton_sn, folder_path, printer_name)` gửi POST request chứa type "print", content btxml tới Print Agent.
  </action>
  <acceptance_criteria>
    - File `usePrintAgent.js` tồn tại và chứa hàm fetch tới cổng `1234`.
  </acceptance_criteria>
</task>
```
