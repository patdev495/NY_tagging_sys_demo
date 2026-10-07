# 0002. Chuẩn Hóa Thời Gian Đóng Gói Theo Giờ Cục Bộ Nhà Máy (Local Time Standardization)

## Context
Hệ thống NY Tagging vận hành trong mạng nội bộ (On-Premise) tại nhà máy sản xuất.
Trước đây, model `Carton` trong SQLAlchemy sử dụng giá trị mặc định:
`created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None))`

Điều này dẫn đến:
1. **Lệch 7 tiếng trên giao diện**: Dữ liệu lưu vào MSSQL/SQLite là giờ UTC không có tzinfo. Khi FastAPI trả về chuỗi ISO không offset (VD: `2026-08-27T01:34:10`), trình duyệt Vue JS parse thành giờ cục bộ, khiến công nhân/quản lý thấy thời gian đóng gói bị chậm 7 tiếng so với thực tế (thực tế 08:34:10).
2. **Bất nhất nội bộ Backend**: Trong khi `Carton.created_at` lưu UTC, thì `JobOrderCartonSlot.scanned_at`, `Date Code` (`YYWW`), và tiền tố tháng `YYMM` lại dùng `datetime.datetime.now()` (Local Time).
3. **Sai lệch thống kê ca sản xuất theo ngày**: API thống kê `get_packaging_statistics` lọc theo ngày cục bộ (`00:00:00 - 23:59:59`), khiến các thùng đóng trong ca đêm (00:00 - 06:59) bị tính sang ngày hôm trước do timestamp UTC.

## Quyết định
Chúng tôi quyết định **Chuẩn hóa toàn bộ hệ thống lưu và xử lý theo Giờ Cục bộ (Local Server Time - UTC+7)**:
1. Đổi giá trị mặc định của `Carton.created_at` sang `datetime.datetime.now` (Local Time).
2. Thực hiện migration một lần tự động trong `init_db` để cộng 7 tiếng (`DATEADD(hour, 7, created_at)`) cho các bản ghi Carton cũ trong Database.
3. Đồng bộ hoàn toàn logic thống kê, truy vấn lịch sử, quét slot, và hiển thị giao diện theo giờ thực tế tại nhà máy.

## Hậu quả (Consequences)
- Màn hình trạm đóng gói (`A11LastCartonCard`), lịch sử thùng hàng (`CartonHistoryPage`), và tra cứu S/N (`SNLookupPage`) hiển thị chính xác 100% thời gian thực tế đóng gói.
- Báo cáo thống kê sản lượng theo ngày phản ánh đúng ca làm việc thực tế, không còn bị lệch ngày đối với các ca sản xuất đêm/rạng sáng.
- Việc truy vấn trực tiếp cơ sở dữ liệu MSSQL qua SQL Management Studio khớp hoàn toàn với báo cáo sản xuất của nhà máy.
