# 0007. Bộ đếm Carton Sequence dùng chung, không reset cho Erro 04

Tem `erro_04` cấp phát một Erro 04 Carton Sequence tăng đơn điệu, không reset, dùng chung cho các Product CAT6A (tiền tố `H`) và CAT5E (tiền tố `K`). Chuỗi `NNNN` không phải số thập phân mà là mã base-32 bốn ký tự, loại bỏ `I`, `L`, `O`, `U`; chọn một bộ đếm duy nhất thay vì reset theo ngày hoặc tách theo tiền tố để đáp ứng yêu cầu kiểm soát số tem liên tục trong toàn bộ mẫu Erro 04.

Khi đưa vào vận hành, bộ đếm cấp giá trị tiếp theo sau Carton ID `erro_04` lớn nhất trong cơ sở dữ liệu; nếu chưa có dữ liệu thì bắt đầu `0001`. Các tem `erro_04` đã in ngoài hệ thống phải được bootstrap bằng Carton ID lớn nhất trước khi cấp phát mới.

## Considered Options

- Reset theo ngày: loại vì làm gián đoạn chuỗi tem và không phải yêu cầu đã chốt.
- Bộ đếm riêng cho `H` và `K`: loại vì phải duy trì hai chuỗi dù cùng một mẫu tem Erro 04.
