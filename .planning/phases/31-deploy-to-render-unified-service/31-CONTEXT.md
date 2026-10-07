# Phase 31: Deploy to Render (Unified Service) - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning
**Source:** User Request

<domain>
## Phase Boundary

Triển khai toàn bộ hệ thống NY Tagging System lên nền tảng Render sử dụng gói miễn phí. Hệ thống sẽ được đóng gói dưới dạng một Web Service duy nhất (Dockerized) chứa cả Backend (FastAPI) và Frontend (Vue 3).

</domain>

<decisions>
## Implementation Decisions

### 1. Deployment Architecture
- **Unified Service**: Thay vì tách biệt Frontend (Vercel/Netlify) và Backend (Render), chúng ta sẽ gộp chung. Backend sẽ đóng vai trò là server phục vụ (serve) các file tĩnh của Frontend.
- **Docker-based**: Sử dụng Dockerfile để đảm bảo môi trường đồng nhất giữa local và Render.

### 2. Frontend Integration
- **Static Folder**: Frontend sau khi build (`npm run build`) sẽ được copy vào thư mục `static` bên trong `backend_v2`.
- **FastAPI Static Mount**: Cấu hình FastAPI để mount thư mục `static` và phục vụ `index.html` cho các route không phải API (SPA support).

### 3. Database & Data
- **SQLite Persistence**: Sử dụng SQLite (`database.db`). Vì Render Free Tier có ổ đĩa tạm thời (ephemeral), dữ liệu sẽ bị reset mỗi khi service restart hoặc deploy mới.
- **Initial Data**: Đính kèm file `database.db` hiện tại vào image Docker để khi deploy lên Render, hệ thống đã có sẵn dữ liệu cũ. 
- *Lưu ý*: Nếu người dùng muốn lưu dữ liệu mới phát sinh trên Render, họ cần dùng Render Disk (có phí) hoặc cloud DB khác. Ở phase này, ưu tiên "Lấy hết dữ liệu hiện tại lên" và chạy "miễn phí".

### 4. Build Pipeline
- **Multi-stage Dockerfile**: 
    - Stage 1: Build Frontend (Node.js).
    - Stage 2: Cài đặt Python dependencies và copy build từ Stage 1.
    - Stage 3: Chạy Backend.

</decisions>

<canonical_refs>
## Canonical References

### Backend
- `backend_v2/main.py` — Điểm khởi đầu của FastAPI app.
- `backend_v2/Dockerfile` — Cấu hình Docker hiện tại.

### Frontend
- `frontend_v2/package.json` — Scripts build frontend.

</canonical_refs>

<specifics>
## Specific Ideas
- Cần cập nhật `main.py` để xử lý fallback route cho SPA (khi người dùng F5 tại một route frontend, server vẫn phải trả về `index.html`).

</specifics>

<deferred>
## Deferred Ideas
- Persistent Database (PostgreSQL/Managed SQLite).
- HTTPS/Domain riêng (Render tự cấp HTTPS).
</deferred>

---

*Phase: 31-deploy-to-render-unified-service*
*Context gathered: 2026-05-14*
