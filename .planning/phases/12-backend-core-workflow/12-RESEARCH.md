# Phase 12 Research: Backend Core Workflow

## 1. Existing Workflow Analysis
Hàm `create_carton` trong `backend/main.py` hiện tại thực hiện một luồng công việc khá phức tạp:
1. Validate product.
2. Validate duplicate item S/Ns (chỉ kiểm tra trùng lặp trong mảng đầu vào, chứ không kiểm tra trong toàn DB, đây là điểm cần lưu ý giữ nguyên).
3. Gọi `get_next_carton_sn(db, product, custom_sn)` để sinh Carton S/N. Trong đó sử dụng `with_for_update()` để lock.
4. Kiểm tra `custom_sn` xem có bị trùng hay không.
5. `db.add(new_carton)` với `status="FAILED"`.
6. Thêm các `CartonItem`.
7. Gọi `generate_btxml()` sinh XML cứng.
8. Gán `btxml_content` vào `new_carton.btxml`.
9. `db.commit()` và trả về.

Ngoài ra còn có:
- `update_carton_status`: Cập nhật `SUCCESS`/`FAILED`.
- `download_carton_btxml`: Trả về file `.xml` đính kèm.
- `reprint_carton`: In lại (tạo bản ghi Carton mới với `is_reprint=1` và gen lại XML).

## 2. Technical Approach for V2
Dựa trên quyết định ở `12-CONTEXT.md`:
- **Giao dịch**: Giữ nguyên trong 1 transaction (Box -> sinh XML -> Commit).
- **Template BarTender**: Sẽ sử dụng 1 file `base.xml` nằm ở `features/print/templates/`. Hàm sinh XML sẽ đọc file này và dùng `.format(**data_dict)`.

**Box Feature (`backend_v2/src/features/box/`):**
- **Service**: 
  - `get_next_carton_sn(db, product, custom_sn)`: Chứa logic `with_for_update`.
  - `create_carton(carton_in: CartonCreate, db: Session)`: Gọi DB để insert Carton, sau đó gọi trực tiếp module `print.service.generate_btxml()` để lấy XML, gán vào Carton rồi mới commit.
- **Router**: `POST /cartons`
- **Lưu ý vòng lặp**: Cần tạo trước `print.service` để import vào `box.service` mà không gây lỗi Circular Import.

**Print Feature (`backend_v2/src/features/print/`):**
- **Templates**: Thư mục `templates/` với file `base.xml`.
- **Service**: 
  - `generate_btxml_dict(carton, product, items)`: Đóng gói các biến thành 1 Dictionary.
  - `render_template(template_name, data_dict, template_path, printer_name)`: Đọc file `.xml` và format với chuỗi.
  - `generate_btxml(...)`: Kết hợp 2 hàm trên.
  - `reprint_carton(...)`: Logic in lại.
  - `update_status(...)`: Cập nhật status `SUCCESS`/`FAILED`.
- **Router**:
  - `PATCH /cartons/{id}/status`
  - `GET /cartons/{id}/btxml`
  - `POST /cartons/{id}/reprint`

**Agent Healthcheck (BACK-06):**
- Đầu mục BACK-06 "Tách Agent healthcheck router/service" thực tế ứng với API `GET /health` của hệ thống hiện tại. Do đó, logic này sẽ được đặt vào router `system` hoặc giữ lại trong `main.py` như `health_check`.

## 3. Implementation Steps & Verification
1. Tạo cấu trúc thư mục cho `box` và `print`.
2. Tạo file `base.xml` tại `print/templates/`.
3. Viết `print/service.py` với cơ chế sinh XML từ file template.
4. Chuyển các Schema liên quan đến tạo Carton (`CartonCreate`, `CartonStatusUpdate`, v.v.) vào `box/schemas.py` hoặc `print/schemas.py`. Tuy nhiên, vì Carton là entity chính của Box, toàn bộ Schema Carton nên nằm ở `box/schemas.py` và tái sử dụng.
5. Gắn các Router vào `main.py`.
