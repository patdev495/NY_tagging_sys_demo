---
status: superseded by ADR-0006
---

# 0005. Cấm In Lại Tem và Cấm Sửa Số Thứ Tự Thùng Đối Với Khách Hàng A11

## Bối cảnh và Động lực

Khách hàng A11 (áp dụng chế độ đóng gói theo cân `weight_scale`, quy tắc sê-ri năm tự tăng 6 chữ số) có yêu cầu kiểm soát tem nhãn đặc thù nhằm triệt tiêu hoàn toàn rủi ro trùng tem và lẫn hàng trong chuỗi cung ứng.

Khác với khách hàng UI (sử dụng chế độ `item_scan` theo `Job Order`, cho phép chọn số thùng `JobOrderCartonSlot` và in lại tem `Reprint` khi tem bị mờ/hỏng), khách hàng A11 yêu cầu:
1. **Tuyệt đối không in lại tem (`No Reprint`)**: Một tem đã in ra mang số sê-ri duy nhất, không bao giờ được phép in bản sao thứ hai.
2. **Không cho phép can thiệp thủ công số thứ tự thùng (`No Manual Sequence`)**: Số sê-ri thùng phải tăng đơn điệu tự động (Strict Monotonic Sequence) từ hệ thống cơ sở dữ liệu.
3. **Quy tắc xử lý tem rách/hỏng (Damaged Label / Burned Sequence SOP)**: Nếu tem in ra bị kẹt giấy, rách hoặc nhòe mực không thể sử dụng, công nhân không in lại tem cũ mà thực hiện thao tác in ngay tem với số thứ tự kế tiếp và dán vào thùng hàng. Số sê-ri hỏng được coi là "cháy số" tự nhiên trong hệ thống, không xóa và không tái sử dụng.

## Quyết định

Chúng tôi quyết định áp đặt quy tắc này đồng bộ ở cả hai tầng:

1. **Tầng Backend API (Domain Enforcement)**:
   - Trong dịch vụ in lại `reprint_carton` (`/print/carton/{id}/reprint`): Kiểm tra nếu Carton thuộc về Customer có mã `A11` (hoặc bí danh `UX`), chặn yêu cầu và trả về mã lỗi HTTP `400 Bad Request` với thông điệp từ chối in lại tem.
   - Trong dịch vụ cân đóng thùng `weigh_pack_carton` (`/carton/weigh-pack`): Chặn mọi yêu cầu truyền `custom_sn` hoặc `custom_yymm` đối với sản phẩm của Customer `A11`, chỉ cho phép cấp phát số tiếp theo tự động qua `plan_next_a11_carton_sn`.

2. **Tầng Giao diện Frontend (`frontend_v2`)**:
   - Màn hình đóng gói A11 (`A11PackingPage.vue`): Gỡ bỏ hoàn toàn nút "In Lại" trên thanh Header, modal `EmergencyReprintModal` và nút "In Lại Thùng Này" trên thẻ thông tin thùng vừa đóng (`A11LastCartonCard.vue`).
   - Thẻ hiển thị sê-ri (`A11SerialControl.vue`): Loại bỏ nút "Sửa Thủ Công" và ô nhập số thứ tự; chuyển thành chế độ thuần chỉ đọc (Read-only) hiển thị sê-ri tự động kế tiếp.
   - Trải nghiệm SOP: Bổ sung chỉ dẫn vận hành trực quan trên màn hình cân: *"💡 Lưu ý: Tem rách/hỏng -> Nhấn F9 để in tem số tiếp theo, không dán tem trùng lặp"*.
   - Khách hàng UI (`UIPackingPage.vue`): Giữ nguyên 100% chức năng in lại và chọn số thùng thủ công theo Job Order.

## Hậu quả (Consequences)

- Loại bỏ hoàn toàn nguy cơ xuất hiện 2 tem có cùng số sê-ri A11 ngoài sàn sản xuất.
- Khi tem bị hỏng, cơ sở dữ liệu sẽ ghi nhận số sê-ri đó như một bản ghi đã tạo; số sê-ri thùng vật lý được dán tem mới sẽ nhảy cách 1 đơn vị so với tem hỏng mà không gây gián đoạn dây chuyền.
- Đảm bảo tính toàn vẹn dữ liệu ngay cả khi client cố tình gửi request API can thiệp số sê-ri hoặc yêu cầu reprint cho A11.
