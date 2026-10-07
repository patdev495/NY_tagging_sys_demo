# Phase 13 Research: Frontend Logic Extraction

## 1. Current State (`frontend`)
- **API Layer**: Nằm toàn bộ trong `src/api.js` (38 dòng). Nó chứa tất cả các lệnh gọi đến `/customers`, `/products`, `/cartons`.
- **Logic Layer**: Tập trung khổng lồ bên trong `src/components/PackingStation.vue` (~2500 dòng). Các State và Logic hiện bị trộn lẫn với giao diện (UI) thông qua `script setup`:
  - **State Khách hàng & Sản phẩm**: `customers`, `products`, `currentProduct`, `loadCustomers()`, `loadProducts()`, `selectProduct()`.
  - **Logic Quét S/N (Scan Buffer)**: `scanBuffer`, `scannedItems`, `handleScan()`, `invalidScans`, regex kiểm tra S/N pattern.
  - **Logic In & Print Agent**: `isAgentConnected`, `checkAgent()`, gọi trực tiếp `fetch('http://127.0.0.1:1234/...')`, `finalizeCarton()`.
  - **Logic Cài đặt (Settings)**: `settings` (template, folder, printer), lưu và tải từ `localStorage`.

## 2. Technical Approach for V2
Theo kiến trúc Feature-Based, chúng ta sẽ tách biệt rạch ròi các khía cạnh. Thay vì viết lại từ đầu, ta sẽ tạo không gian `frontend_v2` bằng cách copy `frontend` hiện tại.

### Tính năng chia theo Domain:
1. **Catalog (Danh mục)**: Khách hàng và Sản phẩm.
2. **Packing (Đóng gói)**: Logic quy trình quét thùng.
3. **Print (In tem)**: Tương tác với Print Agent và lấy BTXML.
4. **Settings (Cài đặt)**: Quản lý cấu hình cục bộ.

### Tách API Layer:
Sẽ loại bỏ file gốc `src/api.js` và chuyển về cấu trúc:
- `src/features/catalog/api.js`: `/customers`, `/products`
- `src/features/packing/api.js`: `/cartons` (create)
- `src/features/print/api.js`: `/cartons/{id}/btxml`, `/cartons/{id}/status`, `/cartons/{id}/reprint`
- `src/core/api.js`: Axios instance base (hoặc `lib/axios.js`).

### Tách Logic Layer (Composables):
Tạo các Composition API custom hooks (Composables) để `PackingStation.vue` chỉ cần gọi dùng chứ không cần tự thân thực thi:
- **`useScanLogic.js`**:
  - Quản lý `scannedItems`, `scanBuffer`, `invalidScans`.
  - Hàm `handleScan(sn, currentProduct, snPattern)`: Validation logic (trùng lặp, pattern AS/...).
- **`usePrintAgent.js`**:
  - Quản lý `isAgentConnected`, `agentErrorMessage`.
  - Hàm `checkAgent()`, `sendPrintJob(btxml_content, folder_path, printer_name)`.

## 3. Implementation Steps
1. Sao chép toàn bộ thư mục `frontend` thành `frontend_v2` (Bảo toàn source cũ).
2. Xây dựng base cấu trúc feature: `src/features/{catalog,packing,print,settings}/`.
3. Tách nhỏ `api.js` vào các domains.
4. Xây dựng các Composables (`useScanLogic`, `usePrintAgent`).
5. (Việc ghép các Composables này vào UI sẽ thực hiện ở Phase 14).
