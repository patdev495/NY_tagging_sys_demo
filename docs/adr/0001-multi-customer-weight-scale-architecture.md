# 0001. Kiến Trúc Hợp Nhất Đa Khách Hàng & Đa Chế Độ Đóng Gói (Multi-Customer & Multi-Mode Architecture)

## Context
Ban đầu, hệ thống NY Tagging được xây dựng dành riêng cho khách hàng Ubiquiti (UI) với quy trình quét từng mã sê-ri con (`Carton Item`), sinh mã thùng 5 số reset hàng tháng, và in tem định dạng chuẩn/chi tiết. 

Khi mở rộng thêm khách hàng mới (A11 và các đối tác tương lai) với:
1. Quy trình đóng gói theo cân trọng lượng (`weight_scale`), không quét mã con.
2. Quy tắc sinh mã sê-ri thùng hoàn toàn khác (reset hàng năm, 6 số tự tăng, tiền tố riêng).
3. Cấu trúc tem và trường in khác biệt (bổ sung PO, LOT, Date Code, Mfr P/N, QR Code dạng ghép chuỗi).

Chúng tôi đứng trước 2 phương án:
- **Phương án A**: Dựng một hệ thống phần mềm riêng biệt cho khách hàng mới.
- **Phương án B**: Tích hợp đa khách hàng vào cùng một lõi hệ thống duy nhất sử dụng Strategy Pattern.

## Quyết định
Chúng tôi quyết định chọn **Phương án B: Tích hợp vào cùng một hệ thống duy nhất**.

### Các lý do cốt lõi:
1. **Tái sử dụng hạ tầng BarTender COM & Print Agent**: Module giao tiếp BarTender COM, xử lý máy in nhiệt Zebra/PDF, quản lý Station ID đã ổn định và hoàn toàn dùng chung được cho mọi mẫu tem.
2. **Trải nghiệm vận hành tại xưởng**: Công nhân tại các trạm đóng gói chỉ cần mở 1 ứng dụng web duy nhất. Khi chọn Job Order/Product của khách hàng nào, giao diện tự động thích ứng với quy trình đóng gói đó (`item_scan` hay `weight_scale`).
3. **Mô hình kiến trúc dạng cắm rút (Strategy Pattern)**:
   - `PackingModeStrategy`: Tách biệt luồng quét sê-ri con (`ItemScanStrategy`) và luồng kiểm soát cân (`WeightScaleStrategy`).
   - `CartonSNStrategy`: Tách biệt logic sinh mã sê-ri theo khách hàng (`UISNStrategy` reset theo tháng, `A11SNStrategy` reset theo năm).
   - `TemplateMapperStrategy`: Tách biệt ánh xạ NamedSubStrings theo từng mẫu tem `.btw`.

## Hậu quả (Consequences)
- Bảng `products` được bổ sung các trường cấu hình trọng lượng (`target_weight`, `min_weight`, `max_weight`, `packing_mode`) và thông số mã (`mfr_pn`, `pkg_prefix`).
- Bảng `cartons` lưu trữ thêm thông tin trọng lượng thực tế `weight`, `po_number`, `lot_number`, `date_code`.
- `Print Agent` được tích hợp module đọc cổng nối tiếp RS-232 và Win32 Global Hotkey để phục vụ chế độ cân.
