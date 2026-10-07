---
phase: 31
name: deploy-to-render-unified-service
wave: 1
depends_on: []
files_modified:
  - backend_v2/main.py
  - backend_v2/Dockerfile
  - render.yaml
autonomous: true
---

# Plan: Phase 31 - Deploy to Render (Unified Service)

Triển khai hệ thống lên Render với một service duy nhất phục vụ cả Backend và Frontend.

## Wave 1: Backend & Frontend Integration

### Task 1: Update Backend to serve Frontend static files
<read_first>
- backend_v2/main.py
</read_first>
<action>
Cập nhật `backend_v2/main.py` để:
1. Mount thư mục `static` (nếu tồn tại) cho các file tĩnh.
2. Thêm catch-all route để trả về `index.html` cho bất kỳ đường dẫn nào không bắt đầu bằng `/api` hoặc không phải file tĩnh, hỗ trợ Vue Router (SPA).
3. Đảm bảo port được lấy từ biến môi trường `PORT` (mặc định 8001).
</action>
<acceptance_criteria>
- `backend_v2/main.py` có sử dụng `StaticFiles` và `FileResponse`.
- Có route xử lý catch-all cho SPA.
- Code không bị lỗi syntax.
</acceptance_criteria>

### Task 2: Create Unified Dockerfile for Render
<read_first>
- backend_v2/Dockerfile
- frontend_v2/package.json
</read_first>
<action>
Tạo hoặc cập nhật `backend_v2/Dockerfile` (hoặc tạo một cái mới ở root nếu cần, nhưng Render thường trỏ vào subfolder được).
Ở đây, ta sẽ cập nhật `backend_v2/Dockerfile` để trở thành Multi-stage build:
- Stage 1: Build Vue 3 app từ `frontend_v2`.
- Stage 2: Cài đặt Python backend và copy thư mục `dist` từ Stage 1 vào thư mục `static` của Backend.
- Đảm bảo copy cả file `database.db` hiện tại vào image.
</action>
<acceptance_criteria>
- Dockerfile có ít nhất 2 stage (`FROM node` và `FROM python`).
- Thư mục `dist` của frontend được copy vào thư mục `static` của backend.
- File `database.db` được copy vào image.
- `CMD` sử dụng biến `$PORT`.
</acceptance_criteria>

### Task 3: Create render.yaml
<read_first>
- None
</read_first>
<action>
Tạo file `render.yaml` ở thư mục gốc của dự án để định nghĩa service trên Render.
Cấu hình:
- type: web
- name: ny-tagging-sys
- env: docker
- dockerContext: .
- dockerfilePath: backend_v2/Dockerfile
- plan: free
- envVars:
  - key: PORT
    value: 8001
</action>
<acceptance_criteria>
- File `render.yaml` tồn tại ở root.
- Cấu hình đúng định dạng Blueprint của Render.
</acceptance_criteria>

## Verification

### Automated Verification
- Chạy build docker local: `docker build -t ny-tagging-unified -f backend_v2/Dockerfile .`
- Chạy thử container: `docker run -p 8001:8001 -e PORT=8001 ny-tagging-unified`
- Kiểm tra truy cập:
    - `http://localhost:8001/` (Phải thấy giao diện Frontend)
    - `http://localhost:8001/api/v1/health` (Phải thấy JSON response)

### Success Metrics
- Hệ thống chạy offline thành công với 1 container duy nhất.
- Dữ liệu cũ (Customers/Products) hiển thị đúng trong giao diện.

## must_haves
- [ ] Frontend hoạt động hoàn chỉnh (routing, assets).
- [ ] Backend API hoạt động.
- [ ] SQLite database chứa dữ liệu hiện tại.
