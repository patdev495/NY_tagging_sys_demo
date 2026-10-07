---
wave: 1
depends_on: []
files_modified:
  - backend_v2/src/features/print/templates/base.xml
  - backend_v2/src/features/print/schemas.py
  - backend_v2/src/features/print/service.py
  - backend_v2/src/features/print/router.py
  - backend_v2/src/features/box/schemas.py
  - backend_v2/src/features/box/service.py
  - backend_v2/src/features/box/router.py
  - backend_v2/main.py
autonomous: true
---

# Phase 12: Backend Core Workflow

## Goal
Tách logic tạo Box (Carton) và sinh file in (BarTender XML) từ `backend/main.py` sang cấu trúc Feature-Based trong `backend_v2`.

## Requirements Covered
- BACK-03: Scan validation & Box orchestration router/service
- BACK-04: Print XML generation router/service
- BACK-06: Tách Agent healthcheck (đã được bọc chung vào system/health ở `main.py`)

## Verification Criteria
- [ ] Endpoint `POST /api/v1/cartons` hoạt động và tạo được db record cùng với chuỗi `btxml`.
- [ ] Endpoint `POST /api/v1/cartons/{id}/reprint` hoạt động.
- [ ] Giao dịch an toàn: Nếu `generate_btxml` lỗi, Carton sẽ không được lưu vào CSDL.
- [ ] Mã nguồn sử dụng template `base.xml` bên ngoài thay vì chuỗi cứng.

## Tasks

```xml
<task id="print_template" title="Create Print Template">
  <read_first>
    - backend/main.py (dòng 59-82, để lấy mẫu XML)
  </read_first>
  <action>
    - Tạo thư mục `backend_v2/src/features/print/templates`.
    - Tạo file `base.xml` với nội dung chuẩn của BarTender XML.
    - Thay thế các giá trị biến bằng ngoặc nhọn Python format `{{}}` hoặc tương tự. Cụ thể dùng `{template_path}`, `{printer_tag}`, `{item_name}`, `{qty}`, `{carton_sn}`, `{upc}`, `{qr_content}`, `{origin_text}`.
  </action>
  <acceptance_criteria>
    - File `backend_v2/src/features/print/templates/base.xml` tồn tại.
  </acceptance_criteria>
</task>

<task id="print_feature" title="Implement Print Service and Router">
  <read_first>
    - backend/schemas.py (CartonStatusUpdate)
    - backend_v2/src/features/history/schemas.py (Để tái sử dụng Schema Carton gốc, vì Carton nằm chung)
  </read_first>
  <action>
    - Tạo `backend_v2/src/features/print/schemas.py` chứa `CartonStatusUpdate`.
    - Tạo `backend_v2/src/features/print/service.py`. 
      - Viết hàm `generate_btxml(carton, product, items, template_path, printer_name)` đọc file `base.xml`, điền giá trị và trả về string.
      - Viết hàm `update_status(carton_id, status_update, db)` để đổi status SUCCESS/FAILED.
      - Viết hàm `reprint_carton(...)` thực hiện copy carton, tạo items, gen lại XML và lưu DB.
      - Viết hàm `download_carton_btxml(...)` trả về chuỗi XML.
    - Tạo `backend_v2/src/features/print/router.py`:
      - Gồm `PATCH /cartons/{id}/status`
      - Gồm `GET /cartons/{id}/btxml`
      - Gồm `POST /cartons/{id}/reprint`
      - Nhớ cấu trúc prefix phù hợp.
  </action>
  <acceptance_criteria>
    - `print/service.py` chứa hàm `generate_btxml` đọc file `base.xml`.
  </acceptance_criteria>
</task>

<task id="box_feature" title="Implement Box Service and Router">
  <read_first>
    - backend/schemas.py (CartonCreate)
    - backend/main.py (hàm create_carton, get_next_carton_sn)
  </read_first>
  <action>
    - Tạo `backend_v2/src/features/box/schemas.py`: chứa `CartonCreate` (hoặc import tái sử dụng nếu cần).
    - Tạo `backend_v2/src/features/box/service.py`:
      - Copy nguyên hàm `get_next_carton_sn(db, product, custom_sn)` từ `main.py` với logic `with_for_update()`.
      - Viết hàm `create_carton(carton_in, db)` xử lý tạo Carton, gọi `print.service.generate_btxml` để lấy string XML, gán vào record và commit.
    - Tạo `backend_v2/src/features/box/router.py` chứa `POST /cartons` gọi logic `create_carton`.
  </action>
  <acceptance_criteria>
    - `box/service.py` gọi hàm từ `print.service`.
    - Lệnh query `with_for_update()` được giữ nguyên.
  </acceptance_criteria>
</task>

<task id="app_routing" title="Register Routers to Main App">
  <action>
    - Thêm `box_router` và `print_router` vào `backend_v2/main.py`.
    - Mở rộng `/api/v1` namespace.
  </action>
  <acceptance_criteria>
    - `backend_v2/main.py` include_router cho `box` và `print`.
  </acceptance_criteria>
</task>
```
