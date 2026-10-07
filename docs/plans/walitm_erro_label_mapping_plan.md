# Kế hoạch nhận diện tem Erro từ công lệnh ShopFloorDW

## Mục tiêu

Khi công nhân nhập một công lệnh, hệ thống đọc Factory P/N từ trường `walitm` của `ShopFloorDW.DBO.F4801`, nhận diện Product Erro tương ứng và chọn chính xác mẫu tem `erro_01`–`erro_05` để in.

Luồng hàng UI hiện tại không thuộc phạm vi thay đổi này và tiếp tục hoạt động theo cơ chế hiện hành.

## Dữ liệu nguồn công lệnh

Mỗi công lệnh cần lấy tối thiểu các trường sau từ `F4801`:

| Trường | Vai trò |
| --- | --- |
| `wadoco` | Số công lệnh người vận hành nhập. |
| `walitm` | Factory P/N; khóa duy nhất để chọn Product và mẫu tem. |
| `wadl01` | Tên/mã con hàng khách hàng; chỉ dùng để người vận hành đối chiếu. |
| `wauorg` | Số lượng công lệnh, nếu loại tem/quy trình cần kiểm soát sản lượng. |

`F4801` hiện có 136.176 bản ghi và 11.325 giá trị `walitm` khác nhau (đếm sau khi trim khoảng trắng, bỏ null/rỗng).

## Mapping cần cung cấp

Nguồn mapping phải có mỗi dòng cho một Factory P/N Erro:

| Cột | Bắt buộc | Ý nghĩa |
| --- | --- | --- |
| `walitm` | Có | Factory P/N lấy từ công lệnh. |
| `product_identifier` | Có | Product trong danh mục NY Tagging cần chọn. |
| `template_type` | Có | Một trong `erro_01`, `erro_02`, `erro_03`, `erro_04`, `erro_05`. |
| `display_name` | Có | Tên con hàng mong đợi để đối chiếu với `wadl01`. |
| `source_drawing_code` | Có | Mã bản vẽ PD làm căn cứ của mapping. |
| `notes` | Không | Ngoại lệ hoặc hướng dẫn vận hành. |

Mỗi `walitm` chỉ được map đến đúng một Product/Template. Một mapping có thể được dùng bởi nhiều công lệnh.

## Hành vi cần triển khai sau khi có mapping

1. Công nhân nhập hoặc quét `wadoco`.
2. Backend truy vấn `F4801`, lấy `walitm`, `wadl01` và số lượng.
3. Backend tra mapping Factory P/N bằng `walitm`.
4. Nếu mapping hợp lệ, trả Product, `template_type`, dữ liệu đối chiếu công lệnh và cho phép mở trạm cân Erro.
5. Trạm cân hiển thị Factory P/N, tên hàng từ công lệnh, Product đã chọn và preview mẫu tem trước khi in.

## Quy tắc an toàn

- Không tìm thấy `walitm` trong mapping: chặn in và hiển thị mã cần được Admin bổ sung.
- Một `walitm` map nhiều Product hoặc nhiều `template_type`: chặn in tuyệt đối.
- `wadl01` khác tên đối chiếu của mapping: cảnh báo rõ cho người vận hành; không được dùng tên hàng để tự chọn tem.
- Không suy luận mẫu tem từ SKU, Product Description, hay Factory Item Code.
- UI không thay đổi trong đợt này; chỉ áp dụng flow mới sau khi mapping Erro được xác minh.

## Kiểm thử khi triển khai

- Cùng `walitm` từ nhiều công lệnh luôn trả cùng Product và cùng `template_type`.
- Mỗi `walitm` trong mapping trả đúng một loại tem Erro.
- Thiếu mapping hoặc mapping mơ hồ chặn in.
- Sai khác `wadl01` tạo cảnh báo nhưng không làm thay đổi Product/tem được chọn.
- Luồng UI hiện hữu vẫn chọn Product và in tem như trước.
