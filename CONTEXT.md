# NY Tagging System

Hệ thống quản lý đóng gói và in ấn nhãn thùng hàng (Carton) tích hợp với phần mềm BarTender qua giao thức COM Automation.

## Language

**Customer**:
Tổ chức hoặc đối tác sở hữu các sản phẩm cần được đóng gói và dán nhãn. Mỗi Customer có mã định danh kỹ thuật (`code`, ví dụ: `UI`, `ERRO`) và tên hiển thị chính thức (`name`, ví dụ: `Universal Instruments`, `Erro`). Erro là Customer duy nhất cho năm mẫu tem `erro_01`–`erro_05`; A11 chỉ là tên lịch sử cần nhận diện khi chuyển dữ liệu, không phải Customer hoặc nhánh cần hiển thị/lọc báo cáo.
_Avoid_: Client, đối tác, đối tác mua hàng

**Erro Label Template Code**:
Mã kỹ thuật ổn định xác định một trong năm mẫu tem của Customer Erro: `erro_01`, `erro_02`, `erro_03`, `erro_04`, hoặc `erro_05`. Ba mã đang hoạt động ánh xạ từ hệ thống cũ theo thứ tự: `a11` → `erro_01`, `a11_tem2` → `erro_02`, và `a11_tem3` → `erro_03`. `erro_04` áp dụng cho tem eero Mỹ (PD027032). `erro_05` áp dụng cho tem thùng ngoài PEGATRON (PD016906). Mọi Reprint của Erro yêu cầu quyền Admin; số Carton SN gốc được giữ nguyên.
_Avoid_: Tem A11, loại tem A11

**Product**:
Một loại sản phẩm thuộc về một Customer, định nghĩa các quy tắc đóng gói (như số lượng mỗi thùng, đường dẫn file tem nhãn, tiền tố số sê-ri).
_Avoid_: SKU, mã hàng

**Customer Project**:
Tên dự án của khách hàng được cấu hình riêng cho một Product Tem 3 của Customer Erro, ví dụ `Andy Town/ Firefly`. Giá trị này được in ở phần dự án trên nhãn Luxshare.
_Avoid_: Item khách hàng, Project Stage

**Production Stage**:
Giai đoạn sản xuất được cấu hình riêng cho một Product Tem 3 của Customer Erro, ví dụ `QB/CR` hoặc `MP`. Giá trị này được in cạnh Customer Project trên nhãn Luxshare.
_Avoid_: Project Stage, giai đoạn mặc định

**Luxshare Part Number**:
Mã liệu nội bộ của Luxshare, được cấu hình riêng cho Product Tem 3 của Customer Erro và in tại trường `PartNo`, ví dụ `LLERJ014-NC-R`. Giá trị này khác với **APN-Rev**.
_Avoid_: APN-Rev, mã liệu khách hàng

**Carton**:
Một thùng hàng vật lý chứa các sản phẩm (Product), được đại diện bởi một mã số sê-ri thùng duy nhất (Carton SN).
_Avoid_: Hộp, thùng chứa, kiện hàng

**Carton SN**:
Mã số sê-ri duy nhất của Carton, được sinh theo quy tắc cấu hình của từng Customer/Product:
- Với khách hàng UI: Tiền tố `start_part` (mặc định `CN` - Carton Number), theo sau là ngày tháng (`YYMM`), ký tự phân biệt sản phẩm và số thứ tự 5 chữ số reset hàng tháng.
- Với khách hàng Erro - `erro_01` (`PD014736`): Tiền tố định danh sản phẩm (VD: `VHK0010237`), theo sau là ngày tháng (`YYMM`) và số thứ tự 6 chữ số reset hàng năm (PKG ID). Bộ đếm là riêng theo Product; Carton SN Tem 1 có thể trùng giữa các Product khác nhau.
- Với khách hàng Erro - `erro_02` (`PD027504`): Mã định danh SSCC gồm 17 chữ số theo bản vẽ khách hàng (`0` + mã công ty 8 chữ số + số thứ tự 7 chữ số + mã kiểm tra Modulo 10: `037033907{seq:07d}{cd}`) với số thứ tự sê-ri tăng liên tục không reset.
- Với khách hàng Erro - `erro_03` (`PD024364`): Mã định danh thùng xuất xưởng Luxshare NME gồm 17 ký tự: mã nhà cung ứng 7 chữ số (mặc định xưởng Việt Nam là `1012665`), thời gian sản xuất 6 chữ số (`YYMMDD`), và số thứ tự 4 chữ số reset theo năm (bắt đầu lại từ `0001` vào ngày 01/01 hàng năm). Bộ đếm là riêng theo Product và mã nhà cung ứng.
- Với khách hàng Erro - `erro_04` (`PD027032`): Mã định danh thùng xuất eero Mỹ gồm 8 ký tự: tiền tố cáp (`H` hoặc `K`), ngày sản xuất mã hóa base-32 (`YMD`), và chuỗi base-32 4 ký tự dùng chung cho toàn bộ Product erro_04, tự động reset về `0001` vào ngày 01/01 đầu năm dương lịch.
- Với khách hàng Erro - `erro_05` (`PD016906`): Mã định danh thùng PEGATRON gồm 18 ký tự: mã nhà cung ứng (`MC220TW1`), số cố định `2`, năm (`YY`), tuần (`WW`) và số thứ tự 5 chữ số dùng chung cho mọi Product erro_05, reset về `50001` vào đầu mỗi tháng đối với xưởng Việt Nam (dải `50001`–`99999`).
_Avoid_: Box SN, mã vạch thùng, PKG ID (trừ phi gọi theo tên trường trên tem Erro 01)

**Admin Carton Creation**:
Thao tác chỉ dành cho Admin để tạo, in và lưu một Carton Erro thật với đầy đủ dữ liệu nhằm thiết lập hoặc bổ sung lịch sử Carton SN cho Product Erro. Admin chỉ nhập số thứ tự chưa tồn tại và lý do; hệ thống dựng Carton SN và các trường tem từ Product cùng quy tắc của mẫu để Admin xác nhận. Carton này được xử lý như Carton thông thường, gồm quyền Reprint của Admin; nếu in thất bại, Carton vẫn giữ số đã cấp để Admin Reprint. Client cấp phát tự động theo số thứ tự hợp lệ lớn nhất trong phạm vi bộ đếm. Hệ thống lưu Admin thực hiện, thời điểm và lý do để truy vết; đây không phải cơ chế sửa số thứ tự thủ công trong quá trình đóng gói.
_Avoid_: Nhập số tay khi in, reset tùy ý, chỉnh số theo ca

**Erro 04 Carton Sequence**:
Bộ đếm chung cho mọi Product dùng Erro Label Template Code `erro_04`, tăng đơn điệu trong từng năm và reset về `0001` vào đầu năm dương lịch theo Giờ Cục bộ máy chủ. Bộ đếm được biểu diễn bằng bốn ký tự base-32 từ `0001` đến `ZZZZ`, dùng `0`-`9` và chữ cái trừ `I`, `L`, `O`, `U`; tiền tố `H` (CAT6A) hoặc `K` (CAT5E) không tạo bộ đếm riêng.
_Avoid_: Số thứ tự theo ngày, bộ đếm H/K riêng, bộ đếm không reset, số thập phân bốn chữ số

**Erro 05 Carton Sequence**:
Bộ đếm chung cho mọi Product dùng Erro Label Template Code `erro_05`, biểu diễn bằng năm chữ số từ `50001` đến `99999` cho xưởng Việt Nam, tự động reset về `50001` vào 00:00 ngày đầu tiên mỗi tháng theo Giờ Cục bộ máy chủ; không reset theo tuần hay tách bộ đếm riêng theo từng mã hàng. Tiền tố nhà cung ứng (mặc định `MC220TW1`) được cấu hình trong trường `pkg_prefix` tại phân hệ Quản trị (Admin) và không được phép chỉnh sửa tại giao diện trạm đóng gói.
_Avoid_: Sê-ri reset theo tuần, bộ đếm riêng theo Product, sê-ri bắt đầu từ 00001 tại Việt Nam, sửa mã nhà cung ứng tại trạm cân

**Erro 04 Carton ID Prefix**:
Ký tự đầu của Carton SN thuộc Product `erro_04`, được cấu hình bắt buộc theo Product: `H` cho CAT6A và `K` cho CAT5E. Đây là metadata ổn định, không được suy luận từ SKU hay SKU Description.
_Avoid_: Tự nhận diện loại cáp từ tên sản phẩm, pkg_prefix

**SSCC**:
Mã định danh công-ten-nơ vận chuyển theo tiêu chuẩn GS1 (Serial Shipping Container Code), bắt đầu bằng `(00)` trên nhãn hiển thị; đối với tem thùng xuất xưởng CM của khách hàng Erro (`erro_02`, bản vẽ PD027504), Carton SN thực tế gồm 17 chữ số (`0` + 8 số Company Prefix + 7 số Sequence + 1 số Check Digit) tăng liên tục không reset.
_Avoid_: Pallet code, mã công-ten-nơ, mã vận đơn

**ASIN**:
Mã số định danh tiêu chuẩn của Amazon (Amazon Standard Identification Number) gồm 10 ký tự chữ và số, được cấu hình cố định theo từng Product của khách hàng Erro xuất khẩu cho hệ thống Amazon eero.
_Avoid_: Mã Amazon, mã sàn, product ASIN

**Date Code**:
Mã thời gian sản xuất gồm 2 chữ số cuối của năm và 2 chữ số của tuần trong năm theo chuẩn ISO (`YYWW`, ví dụ tuần 34 năm 2026 là `2634`).
_Avoid_: Tuần sản xuất, mã tuần, date text

**Manufacturing Date**:
Ngày sản xuất của Carton, lấy theo Local Server Time tại thời điểm in. Với `erro_04`, trường `Date` in theo `YYMMDD` và các thành phần ngày trong Carton SN được mã hóa từ chính ngày này theo bảng PD027032.
_Avoid_: Date Code, ngày nhập tay, ngày đơn hàng

**Lot Number**:
Mã số lô sản xuất (Lot# / 批號) của từng Carton Erro. Với cả năm Erro Label Template Code `erro_01`–`erro_05`, hệ thống backend tự gán `YYYYMMDD` theo **Local Server Time** ngay khi cấp Carton SN; không dùng giá trị LOT giữ từ Job Order hoặc giá trị gửi từ giao diện. Vì vậy, hai Carton cùng Job Order nhưng được cấp mã ở hai ngày khác nhau phải có Lot Number khác nhau. Carton giữ snapshot Lot Number tại lúc cấp mã. Với `erro_04`, Lot Number chỉ phục vụ truy xuất Production Run và không in trên tem; với `erro_05`, Lot Number in tại trường `Lot Code`.
_Avoid_: Mã mẻ, mã batch, số lô con, LOT theo Job Order

**PO Number**:
Mã đơn đặt hàng của khách hàng (Purchase Order / 訂單號) tương ứng với đợt sản xuất, được cấu hình hoặc nhập khi mở ca đóng hàng. Với Erro Label Template Code `erro_04`, đây là trường bắt buộc, được nhập một lần khi mở Production Run và áp dụng cho toàn bộ Carton của đợt đó.
_Avoid_: Mã PO, order ref, mã hợp đồng

**Mfr P/N**:
Mã số chứng nhận sản xuất hoặc tiêu chuẩn nội bộ (承认书编号 / NYS Spec No, ví dụ: `NYS5998`), được cấu hình cố định cho từng Product.
_Avoid_: Mã chứng nhận, mã spec, internal part number

**Revision**:
Phiên bản khách hàng áp dụng cho Product, được in tại trường `Rev` của tem `erro_04`. Revision là metadata bắt buộc theo Product `erro_04`, không có giá trị mặc định dùng chung.
_Avoid_: Revision mặc định, revision của file tem

**Factory P/N**:
Mã số thành phẩm hoặc vật tư nội bộ nhà máy (厂内料号, ví dụ: `1LAE0009D2U004MAAR`), được lưu cho Product trong mapping Factory P/N và xuất hiện tại trường `walitm` của công lệnh ShopFloorDW. Đây là khóa duy nhất để xác định chính xác Product và mẫu tem cần in; `wadl01` chỉ là tên/mã khách hàng để đối chiếu hoặc fallback cho dữ liệu lịch sử chưa mapping. Với Customer Erro, Factory P/N xác định **Erro Label Template Code** theo năm bản vẽ PD; không suy luận mẫu tem từ SKU.
_Avoid_: Mã xưởng, Customer Reference, tên con hàng, Factory Item Code

**Factory Item Code**:
Mã ITEM nội bộ của nhà máy dùng để đối chiếu Product với bảng nguồn, ví dụ `115-00020` của `erro_04`. Đây là metadata riêng không in trên tem và không đồng nhất với SKU hoặc Supplier PN.
_Avoid_: SKU, Supplier PN, mã in nhãn

**Carton Item**:
Một sản phẩm con riêng lẻ được quét bằng máy quét sê-ri để xếp vào thùng (Carton), được định danh bởi một mã sê-ri sản phẩm (Item SN). Một Carton Item chỉ thuộc một Carton UI tại một thời điểm; khi quét lại Carton gốc, mã của chính Carton đó vẫn hợp lệ.
_Avoid_: Serial sản phẩm, sê-ri quét

**Item SN Conflict**:
Trạng thái khi Item SN được quét đã thuộc một hoặc nhiều Carton UI khác. Trạm đóng gói phát hiện ngay khi quét, từ chối thêm mã và mở modal chỉ-tra-cứu thông tin các Carton đang sở hữu mã để người vận hành đối chiếu.
_Avoid_: Mã con trùng, lỗi quét trùng

**Job Order**:
Mã lệnh sản xuất hoặc lệnh đóng gói dùng để nhóm nhiều Carton lại với nhau trong cùng một đợt chạy.
_Avoid_: Lệnh sản xuất, mã lô, Work order

**Job Order Carton Slot**:
Một vị trí thùng được cấp phát trước cho một Job Order, tương ứng với số thứ tự thùng từ 1 đến N (trong đó N là tổng số thùng tính toán được từ tổng số lượng sản phẩm của Job Order chia cho số lượng đóng gói tối đa của Product). Mỗi vị trí thùng có trạng thái là chờ quét hoặc đã quét.
_Avoid_: Số thùng thứ tự, slot thùng, vị trí hộp

**Job Order Slot Allocation Cancellation**:
Việc xoá vật lý toàn bộ Job Order Carton Slot đã cấp phát cho một Job Order UI nhưng chưa bắt đầu đóng gói, để Carton SN được cấp lại liên tiếp cho Job Order sau. Chỉ hợp lệ khi không có Carton nào của Job Order đã được quét và chỉ Role Admin được thực hiện; thao tác này không lưu lịch sử huỷ.
_Avoid_: Huỷ Carton, xoá công lệnh ERP, huỷ một phần slot

**Print Agent**:
Ứng dụng chạy cục bộ trên máy tính client kết nối trực tiếp với động cơ BarTender COM để thực hiện lệnh in nhãn vật lý hoặc xuất PDF.
_Avoid_: Client app, ứng dụng máy in, máy in dịch vụ

**Label Print Preview**:
Bản mô phỏng trên trạm đóng gói của tem Erro sắp in, thể hiện bố cục và toàn bộ giá trị sẽ được nạp vào mẫu tem; sau khi in thành công, Preview tự chuyển sang tem kế tiếp. Barcode và QR chỉ được thể hiện bằng vùng minh hoạ, không cần quét được. Nếu một trường bắt buộc cho mẫu tem chưa có giá trị, Preview phải chỉ rõ trường đó và trạm đóng gói chặn lệnh in. Đây không phải ảnh hoặc PDF render bởi BarTender.
_Avoid_: ảnh BarTender, PDF tem, lịch sử thùng gần nhất

**Printer**:
Thiết bị in nhãn vật lý (hoặc thiết bị ảo xuất PDF) nhận lệnh in từ Print Agent.
_Avoid_: Máy in, print device

**Origin Country**:
Quốc gia sản xuất thực tế của thùng hàng (ví dụ: `VN` - Việt Nam hoặc `CN` - Trung Quốc), quyết định xuất xứ in trên nhãn là "Made in Vietnam" hay "Made in China".
_Avoid_: Quốc gia sê-ri

**Reprint**:
Hành động in lại nhãn của một Carton đã được đóng gói trước đó. Hệ thống sẽ tạo một bản ghi Carton mới nhân bản từ Carton cũ với cờ `is_reprint` đặt là 1, giữ nguyên số Carton SN ban đầu để không làm tăng số thứ tự tự động của lô hàng. Carton UI được phép Reprint trực tiếp tại trạm bất cứ lúc nào, không yêu cầu đăng nhập Admin. Carton Erro yêu cầu tài khoản mang **Role** `Admin` và được kích hoạt từ Lịch sử Carton.
_Avoid_: In bù, in mới, in đè

**Station ID**:
Mã định danh duy nhất của máy tính client hoặc trạm đóng gói thực hiện lệnh in (thường được lưu dưới dạng địa chỉ MAC hoặc địa chỉ IP của Client). Giá trị hệ thống `ADMIN` là ngoại lệ dành riêng cho Carton được tạo từ màn Admin, biểu thị nguồn tạo quản trị chứ không phải máy trạm vật lý.
_Avoid_: MAC ID (trừ phi nói về phần cứng), IP máy, Terminal ID

**Template Type**:
Kiểu định dạng nhãn in được cấu hình cho Product. Hệ thống hỗ trợ hai loại chính: `standard` (chỉ hiển thị thông tin Carton và mã vạch chung) và `detailed` (hiển thị lưới sê-ri chi tiết của từng Carton Item bên trong, tối đa 40 dòng).
_Avoid_: Cấu hình tem, kiểu mẫu

**Template File**:
Tệp thiết kế định dạng nhãn in BarTender vật lý (`.btw`), được lưu trữ trong thư mục tem cục bộ trên máy trạm Windows (`localTemplateDir`, mặc định `D:\PAT\Templates`). Khác với **Template Type** (phân loại nhãn) và **Label Print Preview** (bản mô phỏng web). Trạm đóng gói hỗ trợ kỹ sư và công nhân thao tác mở trực tiếp tệp này trên ứng dụng BarTender của máy tính trạm thông qua **Print Agent** mà không yêu cầu phiên Admin để kiểm tra đối chiếu thiết kế tem.
_Avoid_: File nhãn, tệp BarTender, template nguồn

**Packing Mode**:
Chế độ xác thực và đóng gói của Product để kích hoạt in tem Carton:
- `item_scan`: Quét từng mã sê-ri con (Carton Item) cho đến khi đủ số lượng `packed_qty`.
- `weight_scale`: Đóng gói theo trọng lượng, đọc giá trị cân từ Scale; khi trọng lượng thực tế nằm trong dải `Weight Tolerance` và công nhân kích hoạt lệnh in, hệ thống sẽ sinh mã Carton SN và in tem.
_Avoid_: Kiểu đóng gói, loại scan, scan method

**Scale**:
Thiết bị cân điện tử kết nối với trạm đóng gói qua cổng truyền thông nối tiếp RS-232 / USB-to-Serial ở chế độ phát luồng liên tục (Continuous Streaming). Các thao tác định chuẩn điểm không (Zero) và trừ bì (Tare) được thực hiện trực tiếp trên bàn phím vật lý của đầu cân.
_Avoid_: Cân bàn, máy cân, bộ cảm biến

**Weight Reading**:
Giá trị trọng lượng thực tế đo được từ Scale tại thời điểm cân và in tem cho Carton.
_Avoid_: Số cân, trọng lượng đọc, scale value

**Weight Tolerance**:
Dải trọng lượng hợp lệ của Product (xác định bởi ngưỡng tối thiểu `min_weight` và tối đa `max_weight`), là điều kiện tiên quyết để hệ thống chấp thuận in tem cho Carton ở chế độ `weight_scale`. Các Product `erro_04` được khởi tạo với dải 0–10 kg và có thể được Admin điều chỉnh theo thông số thực tế.
_Avoid_: Biên độ cân, khoảng cân cho phép, dải sai số

**UPC**:
Mã vạch sản phẩm tiêu chuẩn (Universal Product Code) tương ứng với từng Product, được in trực tiếp lên nhãn Carton để nhận diện sản phẩm ở cấp độ bán lẻ.
_Avoid_: Mã vạch thùng, barcode sản phẩm

**Role**:
Vai trò phân quyền của tài khoản truy cập vào phân hệ Quản trị (Admin):
- `Admin`: Toàn quyền thao tác hệ thống (tạo/sửa/xóa Customer, Product, xóa Carton, kích hoạt Reprint, cấu hình).
- `QA`: Quyền chỉ đọc (Read-only). Được phép xem Dashboard, danh mục Customer/Product, theo dõi tiến độ Job Order/PO, tra cứu sê-ri, xem lịch sử và xuất báo cáo dữ liệu. Bị chặn toàn bộ thao tác ghi/sửa/xóa và Reprint Carton Erro.
_Avoid_: Phân quyền động, user type, level, cấp bậc

**Production Run**:
Đợt sản xuất gom nhóm các Carton được đóng trong ca làm việc, được nhận diện qua **Job Order** (ở chế độ `item_scan` hoặc trạm cân Erro kết hợp bộ đôi **PO Number** & **Lot Number**). Với `erro_04`, người vận hành có thể sửa PO Number và Lot Number trong khi chạy; mỗi Carton giữ snapshot của các giá trị này và Job Order tại lúc in, không hồi tố các Carton đã in.
_Avoid_: Phiên làm việc, ca chạy, mẻ hàng

**Shipped Job Order Carton Slot**:
Một **Job Order Carton Slot** đã được hệ thống xuất hàng bên ngoài xác nhận là đã xuất. NY Tagging chỉ sử dụng trạng thái này để áp dụng các quy tắc nghiệp vụ, không quyết định việc xác nhận xuất hàng. Một Carton gắn với Job Order Carton Slot đã xuất hàng không được phép xóa.
_Avoid_: Carton đã in, Carton đã quét, Carton hoàn tất


## Relationships

- Một **Customer** có thể có nhiều **Products** khác nhau.
- Một **Product** xác định chế độ đóng gói (**Packing Mode**), số lượng đóng gói quy chuẩn (`packed_qty`), mẫu tem nhãn, và quy tắc sinh sê-ri (**Carton SN**).
- Với Product ở chế độ `item_scan` (khách hàng UI), một **Carton** thuộc về một **Job Order** thông qua một **Job Order Carton Slot** đã được cấp phát trước. Sau khi một Carton hoàn tất in tem và xác thực, hệ thống phải dừng ở trạng thái chờ mở thùng mới. Công nhân bắt buộc phải xác nhận chuyển sang Job Order Carton Slot tiếp theo (bấm nút "Thùng tiếp theo" hoặc nhấn phím Space) mới được quét hàng tiếp; nếu trạm đang tồn tại lỗi quét thì không được phép chuyển thùng cho đến khi lỗi được xóa.
- Với Product ở chế độ `weight_scale` (khách hàng Erro), trạm đóng gói nhận diện Product thông qua **Job Order** (tra cứu **Factory P/N** từ `ShopFloorDW.DBO.F4801`); một **Carton** được đóng liên tục trong **Production Run** gắn với **Job Order**, **PO Number** và **Lot Number** mà không bắt buộc phải cấp phát Job Order Carton Slot trước. Đối với `erro_02` và `erro_03`, **PO Number** cho phép để rỗng mặc định và người vận hành có thể tùy chọn chỉnh sửa trên giao diện ca đóng gói.
- Một **Carton** gắn với **Shipped Job Order Carton Slot** không được phép xóa.
- Người dùng đăng nhập vào phân hệ Quản trị (Admin) mang một **Role** (`Admin` hoặc `QA`). Tài khoản `QA` chỉ có quyền đọc và xuất báo cáo; các thao tác tạo/sửa/xóa Customer/Product, xóa Carton và kích hoạt Reprint Carton Erro bị chặn ở cả tầng giao diện lẫn API backend. Reprint Carton UI là thao tác vận hành tại trạm, không yêu cầu phiên Admin.
- Mọi mốc thời gian đóng gói (**Carton** `created_at`, **Job Order Carton Slot** `scanned_at`, **Date Code** `YYWW`, sê-ri `YYMM`) đều được ghi nhận theo **Giờ Cục bộ (Local Server Time)** của máy chủ nhà máy để đảm bảo tính nhất quán giữa màn hình vận hành, báo cáo thống kê ca sản xuất và nhãn in BarTender.
- Người vận hành hoặc kỹ sư tại trạm đóng gói (cả UI và Erro) được phép kích hoạt mở **Template File** trực tiếp qua **Print Agent** trên máy trạm để kiểm tra mẫu tem. Nếu tệp không tồn tại trong thư mục cục bộ, hệ thống cảnh báo rõ tên tệp và đường dẫn, đồng thời hỗ trợ mở nhanh thư mục lưu trữ qua trình quản lý tệp tin (File Explorer).

## Example dialogue

> **Developer:** "Khi quét sản phẩm con vào **Carton**, nếu chưa đủ số lượng `packed_qty` quy định của **Product** thì hệ thống có cho phép xuất mã **Carton SN** để in nhãn không?"
> **Domain expert:** "Mặc định là không. Tuy nhiên, nếu cấu hình của **Product** đó cho phép `allow_partial`, chúng ta vẫn cho đóng thùng thiếu và in nhãn **Carton** bình thường."
> 
> **Developer:** "Với sản phẩm đóng gói theo cân (**weight_scale**), nếu số cân không nằm trong dải **Weight Tolerance** thì hệ thống xử lý thế nào?"
> **Domain expert:** "Hệ thống phải chặn lệnh in, cảnh báo lỗi trọng lượng trên màn hình và không cấp phát số **Carton SN**."
> 
> **Developer:** "Khi một **Carton** trong chế độ `item_scan` đã đóng đủ và in tem xong, công nhân có thể quét ngay sản phẩm của thùng tiếp theo không?"
> **Domain expert:** "Không, hệ thống phải yêu cầu bấm xác nhận sang thùng tiếp theo (qua nút trên màn hình hoặc phím tắt Space) để tránh quét nhầm vào thùng cũ hoặc chưa kịp chuẩn bị thùng mới. Đặc biệt, nếu trạm đang có lỗi quét chưa được xóa thì không cho phép chuyển thùng."


## Flagged ambiguities

- **packed_by**: Trường `packed_by` trong bảng cartons thực chất đang lưu tên của **Printer** (Thiết bị in) chứ không phải thông tin của người đóng gói (Packer/Operator).
- **CN**: Ký tự `CN` ở tiền tố số sê-ri (`start_part`) là viết tắt của **Carton Number**, hoàn toàn độc lập với ký tự `CN` đại diện cho Trung Quốc (China) trong trường quốc gia sản xuất (`Origin Country` / `carton_origin`).
- **NYS6248**: Dòng sản phẩm NYS6248 trong Bảng 1 của bản vẽ PD027032 thiếu thông tin UPC và SKU nên chưa được tạo vào danh mục Erro 04; được ghi nhận là dữ liệu chờ bổ sung từ khách hàng (pending source data).
