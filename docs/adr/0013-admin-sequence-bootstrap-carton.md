# 0013. Admin Carton Creation cho Erro

Khi đưa Product Erro đang có lịch sử in tem vào hệ thống, Admin tạo, in và lưu một Carton thật bằng thao tác Admin Carton Creation thay vì cho trạm đóng gói nhập tay số thứ tự; Customer khác không có thao tác này. Admin chỉ nhập một số thứ tự chưa tồn tại cùng lý do, còn hệ thống dựng và kiểm tra Carton SN cùng các trường của mẫu tem trước khi xác nhận; hệ thống lưu Admin thực hiện và thời điểm tạo, đồng thời ghi `Station ID = ADMIN` để lịch sử nhận diện nguồn tạo. Carton này có thể được Admin Reprint như Carton Erro thông thường; khi in thất bại, Carton vẫn giữ số đã cấp và chỉ được Admin Reprint, không bị xóa hay trả lại số. Luồng tạo Carton vẫn dùng cơ chế cấp số và transaction ở backend; `erro_01` dùng bộ đếm theo Product, `erro_02` phải khóa bộ đếm SSCC dùng chung giữa các Product. Các client sau đó tự cấp số kế tiếp từ số thứ tự hợp lệ lớn nhất trong CSDL theo phạm vi bộ đếm của mẫu tem: `erro_01` theo Product, `erro_02` theo mã công ty SSCC, `erro_04` và `erro_05` dùng chung theo mẫu.

## Considered Options

- Cho trạm đóng gói nhập hoặc sửa số thứ tự: loại vì có thể gây trùng Carton SN giữa ca và máy.
- Lưu một bản ghi bootstrap giả, không in: loại vì nhu cầu vận hành là tạo và in một Carton thật có đầy đủ dữ liệu.
