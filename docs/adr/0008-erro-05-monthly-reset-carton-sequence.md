# 0008. Bộ đếm Carton Sequence dải 50001-99999 reset hàng tháng cho Erro 05

Tem `erro_05` (Bản vẽ PD016906 / Pegatron NN9) cấp phát một Erro 05 Carton Sequence gồm 5 chữ số thuộc dải `50001`–`99999` cho xưởng Việt Nam, dùng chung cho toàn bộ danh mục sản phẩm của mẫu tem này. Bộ đếm tự động reset về `50001` vào 00:00:00 ngày đầu tiên của mỗi tháng mới (Local Server Time), tuân thủ nghiêm ngặt ghi chú kỹ thuật trên bản vẽ PD016906 Rev I.

Định dạng Carton SN gồm 18 ký tự:
`{pkg_prefix}2{YY}{WW}{Seq:05d}`
Trong đó:
- `pkg_prefix`: Mã nhà cung ứng (mặc định `MC220TW1`), cấu hình trong Admin.
- `2`: Ký tự cố định theo quy cách bản vẽ.
- `YY`: 2 chữ số cuối của năm sản xuất.
- `WW`: 2 chữ số tuần trong năm (ISO week).
- `Seq:05d`: Số thứ tự 5 chữ số từ `50001` đến `99999`.

Theo quyết định ADR-0005, tem `erro_05` tuyệt đối cấm in lại (No Reprint) để tránh trùng lặp mã sê-ri thùng xuất xưởng.

## Considered Options

- Reset theo ngày: loại vì bản vẽ ghi rõ chu kỳ reset là hàng tháng ("流水码每月归零").
- Sê-ri bắt đầu từ `00001`: loại vì dải `00001`–`50000` dành riêng cho xưởng Zhuhai, xưởng Việt Nam bắt buộc dùng dải `50001`–`99999`.
- Tách bộ đếm theo từng mã hàng: loại vì bản vẽ yêu cầu toàn bộ các mã hàng dùng chung một bộ đếm thống nhất hàng tháng ("所有品名的流水码每月统一编排,不可重复").
- Không bao giờ reset: loại vì vi phạm quy chuẩn đánh số thùng của Pegatron.
