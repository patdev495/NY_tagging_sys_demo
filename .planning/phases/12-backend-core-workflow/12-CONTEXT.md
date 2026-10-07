# Phase 12 Context

## Domain
Tách hoàn toàn logic tạo Box và Print XML.
Core workflow này là xương sống của ứng dụng, đòi hỏi độ an toàn giao dịch tuyệt đối.

## Decisions

### 1. Ranh giới Giao dịch DB (Transaction Boundary)
* **Quyết định:** Giữ nguyên 1 transaction thống nhất. Endpoint `create_carton` sẽ tạo Box, sinh XML, gán vào Carton, rồi mới `db.commit()`.
* **Lý do:** Bảo vệ tính toàn vẹn dữ liệu. Nếu việc sinh XML thất bại, box sẽ bị rollback và không có rác trong database.

### 2. Cách quản lý mẫu BarTender (XML Template)
* **Quyết định:** Chuyển nội dung XML cứng thành file template (vd: `print/templates/default.xml`) và sử dụng cơ chế truyền Dictionary động (hoặc string formatting nâng cao/Jinja2).
* **Lý do:** Cho phép mở rộng dễ dàng. Khi có khách hàng mới, chỉ cần tạo file `customer2.xml` và viết một map builder mà không phải thay đổi core logic. Khắc phục tình trạng "fix cứng" `<NamedSubString>`.

### 3. Cơ chế Khóa Sinh mã (Sequence Locking)
* **Quyết định:** Giữ nguyên vẹn 100% logic sử dụng `with_for_update()` của code cũ.
* **Lý do:** Đây là cơ chế bảo vệ concurrency (chống trùng S/N khi nhiều client gọi API cùng lúc) đang hoạt động ổn định trên MSSQL. Không thay đổi rủi ro.

## Implementation Constraints & User Notes

> [!WARNING]
> **BẢO TOÀN DATABASE:** Tuyệt đối KHÔNG thay đổi cấu trúc bảng, lược đồ (schema) hoặc dữ liệu của database hiện tại. Mọi service mới phải tương thích hoàn toàn với schema cũ.

> [!IMPORTANT]
> **THƯ MỤC LÀM VIỆC MỚI:** Tiếp tục làm việc trong thư mục `backend_v2/`. Tuyệt đối không xóa hay sửa code trong thư mục `backend` cũ.

## Canonical Refs
- `backend/main.py` (Nguồn logic API cũ: hàm `create_carton`, `generate_btxml`, `reprint_carton`, `get_next_carton_sn`)
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
