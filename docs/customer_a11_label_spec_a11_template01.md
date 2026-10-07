# Đặc Tả Kỹ Thuật Sinh Mã & Tem Nhãn Khách Hàng A11 (A11 Standard)

> **Khách hàng**: A11  
> **Tiêu chuẩn tem**: Bản vẽ A11 (PD014736 REV.H) - Kích thước 3" x 5" (inch)  
> **Chế độ đóng gói**: `weight_scale` (Đóng gói theo cân trọng lượng, không quét mã con)  
> **Số lượng quy chuẩn**: 190 PCS / Thùng  
> **Danh sách sản phẩm ban đầu**: `840-00083`, `840-00091`, `840-00092`  

---

## 1. Bảng Quy Tắc Sinh Mã Của Từng Trường Trên Tem

| STT | Tên trường | Nguồn dữ liệu | Nhãn hiển thị (Text Display) | Nội dung Mã Vạch 1D | Quy tắc & Công thức sinh mã | Ví dụ mẫu |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Customer Part Number (CPN)** | `Product.item_name` | `(P)C P/N:{CPN}` | `P{CPN}` | Tiền tố `P` + Mã sản phẩm | `P840-00092` |
| **2** | **Quantity (QTY)** | `Product.packed_qty` | `(Q)QTY:{QTY}` | `Q{QTY}` | Tiền tố `Q` + Số lượng đóng gói (190) | `Q190` |
| **3** | **Mfr P/N (Spec No)** | `Product.mfr_pn` | `(M)Mfr P/N:{MfrPN}` | `M{MfrPN}` | Tiền tố `M` + Mã giấy chứng nhận / NYS Spec | `MNYS5998` |
| **4** | **Date Code** | `datetime.now()` | `(D)Date Code:{YYWW}` | `D{YYWW}` | Tiền tố `D` + 2 số cuối năm + 2 số tuần ISO (`YYWW`) | `D2634` (Năm 2026, tuần 34) |
| **5** | **Lot Number (Lot#)** | Người dùng nhập trên Web UI | `(L)Lot#:{LotNo}` | `L{LotNo}` | Tiền tố `L` + Số lô sản xuất | `L92608521` |
| **6** | **PO Number (P.O.)** | Người dùng nhập trên Web UI | `(K)P.O. :{PONo}` | `K{PONo}` | Tiền tố `K` + Số đơn hàng | `KB432-22156381` |
| **7** | **PKG ID (Carton SN)** | Backend Allocator | `(S)PKG ID:{CartonSN}` | `S{CartonSN}` | Tiền tố `S` + `{Prefix}{YYMM}{Seq:06d}` *(Reset hàng năm)* | `SVHK00102372608000081` |
| **8** | **Revision** | `Product.revision` | `Rev:{Rev}` | *(Không có)* | Phiên bản bản vẽ khách hàng | `Rev:B` |
| **9** | **Origin** | `Carton.carton_origin` | `Made in Vietnam` | *(Không có)* | `Made in Vietnam` hoặc `Made in China` | `Made in Vietnam` |
| **10** | **Company Name** | Cố định | `NIEN YI ELECTRONICS CO LTD` | *(Không có)* | Cố định | `NIEN YI ELECTRONICS CO LTD` |
| **11** | **RoHS** | Cố định | `RoHS` | *(Không có)* | Biểu tượng tiêu chuẩn bảo vệ môi trường | `RoHS` |

---

## 2. Quy Tắc Sinh Mã 2D (QR Code)

* **Kích thước in**: `13 x 13 mm` (Dung sai: `+2 / -0 mm`).
* **Cấu trúc ghép chuỗi**: Nối toàn bộ 7 mã vạch 1D ở trên theo thứ tự nghiêm ngặt, phân tách bằng dấu phẩy `,` (ASCII half-width, không có dấu cách):
  
$$\text{QRCode} = \text{P}\{\text{CPN}\} + \text{,Q}\{\text{QTY}\} + \text{,M}\{\text{MfrPN}\} + \text{,D}\{\text{DateCode}\} + \text{,L}\{\text{LotNo}\} + \text{,K}\{\text{PONo}\} + \text{,S}\{\text{PKG\_ID}\}$$

* **Ví dụ chuỗi QR Code thực tế**:
  ```text
  P840-00092,Q190,MNYS5998,D2634,L92608521,KB432-22156381,SVHK00102372608000081
  ```

---

## 3. Quy Tắc Sinh Số Sê-ri Thùng (PKG ID / Carton SN)

* **Công thức**:
  $$\text{CartonSN} = \text{pkg\_prefix} + \text{YYMM} + \text{sequence (6 chữ số)}$$
  * `pkg_prefix`: Cấu hình cho từng sản phẩm (Ví dụ: `VHK0010237`).
  * `YYMM`: 2 chữ số năm + 2 chữ số tháng tại thời điểm in (Ví dụ: Tháng 8/2026 ➔ `2608`).
  * `sequence`: Số thứ tự tự tăng 6 chữ số, bắt đầu từ `000001` đến `999999`.
* **Chu kỳ Reset**:
  * **Reset về `000001` vào đầu mỗi năm mới (`01/01`)**.
  * Trong cùng 1 năm (ví dụ năm 2026), dãy số tự tăng tiếp tục tăng dần qua các tháng (`2601000001` ... `2608000081` ... `2612000500`).

---

## 4. Điều Kiện Kiểm Soát Trọng Lượng Cân (Weight Scale Gatekeeper)

* **Trạng thái**: Chế độ `weight_scale`.
* **Điều kiện in**:
  $$\text{min\_weight} \le \text{Weight Reading} \le \text{max\_weight} \quad \text{và} \quad \text{is\_stable} = \text{True}$$
* **Quy trình**:
  1. Khi thùng hàng 190 con được đặt lên cân, Print Agent liên tục đọc số cân qua RS-232.
  2. Giao diện Web hiển thị số cân thời gian thực.
  3. Khi công nhân nhấn `F9` (hoặc click nút In):
     - Nếu thỏa mãn dải trọng lượng ➔ Backend sinh `CartonSN`, tạo lệnh in BarTender và lưu log `weight` vào DB.
     - Nếu không thỏa mãn (thừa/thiếu) ➔ Chặn in, màn hình cảnh báo đỏ, không sinh mã sê-ri.
