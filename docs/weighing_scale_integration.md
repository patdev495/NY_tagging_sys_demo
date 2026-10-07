# Tài Liệu Kỹ Thuật: Tích Hợp Cân Điện Tử & Quy Trình Đóng Gói Theo Trọng Lượng (Weight-Based Packaging)

> **Dự án**: NY Tagging System  
> **Phiên bản**: 2.0  
> **Tham chiếu mã nguồn cân**: `D:\Workspace\weighing-scale`  
> **Ngày lập**: 2026-08-21  

---

## 1. Tổng quan (Executive Summary)

Nhằm phục vụ các khách hàng mới với mô hình đóng gói **không quét mã sê-ri từng sản phẩm con** (Bulk / Weight-based), hệ thống NY Tagging bổ sung chế độ đóng gói **`weight_scale`** bên cạnh chế độ truyền thống **`item_scan`**. 

Ở chế độ này:
- **Print Agent** (chạy trên máy trạm Windows tại xưởng) kết nối trực tiếp với **Cân điện tử** (Scale) qua cổng nối tiếp **RS-232 / USB-to-Serial COM Port**.
- Dữ liệu trọng lượng được đọc và chuẩn hóa theo thời gian thực (Live Stream).
- Công nhân kích hoạt lệnh đóng thùng thông qua **Global Hotkey** (ví dụ: `F9` / Bàn đạp footswitch) hoặc thao tác trên **Web UI**.
- Hệ thống chỉ cấp phát mã sê-ri thùng (**Carton SN**) và in tem nhãn khi trọng lượng thực tế nằm trong dải sai số chuẩn (**Weight Tolerance**: `min_weight <= weight <= max_weight`).

---

## 2. Giao thức Truyền thông Vật lý & Cấu hình Serial RS-232

### 2.1. Cấu hình cổng COM chuẩn
* **Cổng giao tiếp**: `COM1` .. `COM32` (tự động quét và liệt kê qua `serial.tools.list_ports`).
* **Baud rate**: Mặc định `9600` (Hỗ trợ cấu hình: `2400`, `4800`, `9600`, `19200`, `38400`, `115200`).
* **Data bits**: `8` (`serial.EIGHTBITS`).
* **Parity**: `None` (`serial.PARITY_NONE`).
* **Stop bits**: `1` (`serial.STOPBITS_ONE`).
* **Hardware Handshaking / Control Lines**:
  * `DTR = True` (Data Terminal Ready)
  * `RTS = True` (Request to Send)
  * `XON/XOFF = False`, `RTS/CTS = False`, `DSR/DTR = False`.
* **Read Timeout**: `0.5s`.

### 2.2. Cơ chế Tự phục hồi Kết nối (Auto-Reconnect Worker Loop)
Module `SerialEngine` chạy trên một background thread độc lập (`daemon=True`), quản lý kết nối và tự động phục hồi khi có sự cố phần cứng:
1. Liên tục kiểm tra trạng thái mở cổng `ser.is_open`.
2. Khi xảy ra `serial.SerialException` hoặc `OSError` (tuột cáp, mất nguồn cân, rút USB):
   - Đóng an toàn descriptor hiện tại.
   - Chuyển trạng thái sang `RECONNECTING`.
   - Chờ `reconnect_interval = 2.0s` rồi tự động mở lại cổng mà không làm treo ứng dụng hay ngắt luồng UI.

```
[Disconnected / Error] ---> (Thử kết nối lại sau 2s) ---> [Connected]
                                                               |
                                                          (Đọc dữ liệu)
                                                               |
  [Reconnecting] <--- (Phát hiện tuột cáp / lỗi cổng) <-------+
```

---

## 3. Cấu trúc Gói tin & Logic Bóc tách (Packet Parsing Engine)

### 3.1. Phân định ranh giới gói tin (Frame Delimiters)
Cân truyền dữ liệu dạng chuỗi byte liên tục. Engine sử dụng bộ đệm `bytearray` tích lũy và cắt gói dựa theo các ký tự kết thúc:
* `\r\n` (CRLF - 0x0D 0x0A)
* `\n` (LF - 0x0A)
* `\r` (CR - 0x0D)
* `\x03` (ETX - End of Text)
* Loại bỏ ký tự mở đầu `\x02` (STX - Start of Text) nếu có.

### 3.2. Bộ lọc nhiễu (Noise & Header Filtering)
Trước khi parse trọng lượng, gói tin được lọc bỏ các dòng rác hoặc metadata không mang giá trị cân:
* Header phiếu in: `DATE`, `TIME`, `YEAR`, `MONTH`, `DAY`, `HOUR`, `MIN`, `SEC`, `NO.`, `NUM`, `TOTAL`, `COUNT`, `TICKET`.
* Dấu thời gian / Định dạng ngày giờ: `AM`, `PM`, `DD/MM/YYYY`, `HH:MM:SS`.
* Dòng kẻ phân cách: `===`, `---`, `***`, `###`.

### 3.3. Trích xuất chỉ số & Cờ trạng thái (`ScalePacketInfo`)
Biểu thức chính quy trích xuất số cân:
```python
_WEIGHT_PATTERN = re.compile(r"(?P<weight>[+-]?\s*\d+(?:[.,]\d+)?)")
```

Cấu trúc dữ liệu đầu ra sau khi parse:
```python
@dataclass(frozen=True)
class ScalePacketInfo:
    weight: str         # Chuỗi số đã chuẩn hóa (VD: "12.450", bỏ dấu '+', thay ',' thành '.')
    unit: str = "kg"    # Đơn vị đo: "kg", "g", hoặc "lb"
    is_stable: bool     # True nếu chứa "ST" / False nếu chứa "US" hoặc "UNSTABLE"
    is_net: bool        # True nếu là trọng lượng tịnh sau trừ bì ("NT", "NET")
    is_tare: bool       # True nếu đã trừ bì ("PT", "TARE")
    is_zero: bool       # True nếu trị tuyệt đối < 1e-6
    is_hold: bool       # True nếu cân đang ở chế độ giữ số
```

---

## 4. Cơ Chế Điều Khiển Cân & Định Chuẩn Điểm Không (Scale Calibration & Tare/Zero)

Trong thực tế vận hành tại xưởng:
* Đầu cân điện tử (OKS, Yaohua XK3190, CAS,...) được cấu hình ở chế độ **Continuous Streaming Mode** (Phát luồng dữ liệu liên tục 10-20 gói/giây qua chân `TX -> PC RX`).
* Cáp truyền thông USB-to-RS232 đa số là cáp 1 chiều (Simplex: Scale TX -> PC RX + GND).
* **Quy tắc vận hành**: Các thao tác định chuẩn điểm không (**Zero**) và **Trừ bì (Tare)** được công nhân thực hiện trực tiếp bằng **phím bấm vật lý trên bàn phím màng của đầu cân**. Giao diện Web tự động đọc và hiển thị cờ `TARE` (`is_tare = true`) hoặc `ZERO` (`is_zero = true`) từ chuỗi dữ liệu phản hồi của cân mà không can thiệp lệnh gửi xuống.

| Tên Thao Tác | Vị Trí Thực Hiện | Chức Năng |
| :--- | :--- | :--- |
| **Tare (Trừ bì)** | Phím bấm vật lý `[TARE]` trên đầu cân | Đưa số cân hiện tại của bao bì/khay về 0.000, đầu cân phát cờ `PT` / `NT` / `TARE` lên Web |
| **Zero (Về 0)** | Phím bấm vật lý `[ZERO]` trên đầu cân | Định chuẩn lại điểm không tuyệt đối khi bàn cân trống |

---

## 5. Cơ chế Bắt Phím Toàn Cục (Global Hotkey & Foot Switch)

Nhằm tối ưu tốc độ đóng gói trên chuyền, công nhân không cần chạm chuột vào màn hình:
* **Win32 `RegisterHotKey` Engine**:
  * Đăng ký phím tắt cấp OS (mặc định: `F9`, `F12`, `Ctrl+F9`, hoặc tín hiệu từ bàn đạp chân chuyển đổi thành phím).
  * Chạy trên luồng Windows Message Pump (`GetMessageW`), hoạt động độc lập ngay cả khi trình duyệt Web hoặc phần mềm khác đang mất focus (Inactive Window).
* **Cơ chế Chống dội phím (Debounce)**:
  * Ngưỡng `debounce_ms = 400ms` ngăn chặn triệt để hiện tượng dập phím 2 lần làm in lặp 2 tem cho cùng 1 thùng hàng.

---

## 6. Kiến trúc Tích hợp Hệ thống (End-to-End Architecture)

```mermaid
flowchart TD
    subgraph PhysicalStation ["Trạm Đóng Gói (Physical Hardware)"]
        ScaleDevice["Cân Điện Tử OKS (RS-232 / USB)"]
        FootSwitch["Bàn Phím / Bàn Đạp Chân (F9)"]
        ZebraPrinter["Máy In Nhãn Zebra / BarTender"]
    end

    subgraph PrintAgentLayer ["Print Agent V2 (Chạy ngầm trên máy trạm)"]
        SerialEngine["Serial Engine (Background Thread)"]
        PacketParser["Scale Packet Parser"]
        HotkeyEngine["Global Hotkey Listener (Win32)"]
        ScaleService["Scale Feature Manager"]
        FastAPIApp["FastAPI Agent Server (Port 8080)"]
        COMManager["BarTender COM Automation Engine"]
    end

    subgraph FrontendApp ["Giao Diện Web (Vue 3)"]
        PackingStore["Packing Store / Composable"]
        LiveWeightGauge["Component Hiển Thị Cân Trực Tiếp"]
        PackingView["Packing Page (Chế độ weight_scale)"]
    end

    subgraph BackendApp ["Backend Máy Chủ (FastAPI + Database)"]
        CartonRouter["Carton Router"]
        CartonService["Carton Service & Slot Allocator"]
        PrintService["Print Service & BTXML Generator"]
        Database[("Cơ sở dữ liệu (cartons, products, slots)")]
    end

    %% Luồng đọc cân
    ScaleDevice -->|Dòng dữ liệu Serial| SerialEngine
    SerialEngine --> PacketParser
    PacketParser -->|ScalePacketInfo| ScaleService
    ScaleService --> FastAPIApp

    %% Luồng phím bấm
    FootSwitch -->|Phím F9| HotkeyEngine
    HotkeyEngine -->|Trigger Event| ScaleService

    %% Giao tiếp Agent <-> Frontend Web
    FastAPIApp <-->|SSE / Polling / REST /scale/current| PackingStore
    PackingStore --> LiveWeightGauge
    LiveWeightGauge --> PackingView

    %% Luồng xác thực & in tem
    PackingView -->|1. POST /api/v1/carton/weigh-pack (weight, slot_id)| CartonRouter
    CartonRouter --> CartonService
    CartonService --> Database
    CartonService -->|2. Validate dải cân & Cấp Carton SN| PrintService
    PrintService -->|3. Tạo XML BarTender chứa trường Weight| CartonRouter
    CartonRouter -->|4. Trả lệnh in XML về Web| PackingStore
    PackingStore -->|5. POST /print (xml_content)| FastAPIApp
    FastAPIApp --> COMManager
    COMManager -->|6. Lệnh in nhiệt| ZebraPrinter
```

---

## 7. Thiết Kế API & Mô Hình Dữ Liệu

### 7.1. Bổ sung API trên `Print Agent` (Client-side)
* `GET /scale/status`: Trả về trạng thái kết nối cổng COM (`connected`, `port`, `baudrate`, `is_streaming`).
* `GET /scale/current`: Trả về giá trị cân hiện tại và cờ ổn định:
  ```json
  {
    "weight": 12.450,
    "unit": "kg",
    "is_stable": true,
    "is_net": false,
    "timestamp": 1771667820.12
  }
  ```
* `POST /scale/tare`: Gửi lệnh trừ bì `b"T\r\n"`.
* `POST /scale/zero`: Gửi lệnh zero `b"Z\r\n"`.
* `POST /scale/config`: Cập nhật cổng COM, baudrate, phím tắt hotkey.

### 7.2. Bổ sung Trường Dữ Liệu trong Database (Backend)

#### Bảng `products`:
* `packing_mode`: `"item_scan"` | `"weight_scale"` (Mặc định `"item_scan"`).
* `target_weight`: Khối lượng quy chuẩn 1 thùng đầy (VD: `12.500` kg).
* `min_weight`: Khối lượng tối thiểu chấp nhận in tem (VD: `12.300` kg).
* `max_weight`: Khối lượng tối đa chấp nhận in tem (VD: `12.700` kg).
* `weight_unit`: `"kg"` | `"g"` (Mặc định `"kg"`).

#### Bảng `cartons`:
* `weight`: Khối lượng thực tế lúc in tem (VD: `12.480`).
* `weight_unit`: Đơn vị đo (`"kg"`).

---

## 8. Quy Trình Nghiệp Vụ Tại Xưởng (Operational Workflow)

```
[Bắt đầu ca làm việc]
         │
         ▼
[Chọn Job Order & Sản phẩm] ──► Hệ thống nhận diện packing_mode = "weight_scale"
         │
         ▼
[Đặt thùng hàng lên cân]
         │
         ▼
[Giao diện Web hiển thị số cân Live]
   ├── Nếu Chưa ổn định / Ngoài dải (Weight < Min hoặc Weight > Max):
   │     └── Màn hình màu Vàng/Đỏ, Nút in bị KHÓA, F9 bị VÔ HIỆU HÓA.
   │
   └── Nếu Ổn định & Nằm trong dải [Min, Max]:
         └── Màn hình chuyển XANH LÁ, sẵn sàng in.
         │
         ▼
[Công nhân ấn F9 hoặc Click "In Tem Thùng"]
         │
         ├──► 1. Web gửi số cân + Slot ID lên Backend
         ├──► 2. Backend kiểm tra lại Tolerance, cấp phát Carton SN
         ├──► 3. Backend gán biến "Weight" = "12.48 kg" vào template BarTender
         ├──► 4. Print Agent gửi lệnh in tới BarTender COM
         └──► 5. Máy in nhả tem, hoàn tất đóng thùng.
```

---

## 9. Kế Hoạch Triển Khai (Implementation Steps)

1. **Bước 1 (Print Agent)**: Sao chép và tích hợp các module `serial_engine.py`, `parser.py`, `hotkey.py` từ `weighing-scale` vào `print_agent_v2`, mở các endpoint REST API cho cân.
2. **Bước 2 (Backend)**: Bổ sung các cột cấu hình trọng lượng trong `Product`, trường `weight` trong `Carton`, và cập nhật `BTXMLDocument` để truyền số cân sang file `.btw`.
3. **Bước 3 (Frontend)**: Xây dựng giao diện đồng hồ cân thời gian thực (Weight Gauge Indicator), tích hợp cơ chế bắt phím `F9` và cảnh báo sai lệch trọng lượng trực quan.
4. **Bước 4 (Customer SN Strategy)**: Gắn module sinh mã sê-ri chuyên biệt của khách hàng mới khi nhận được mẫu file tem và quy tắc từ người dùng.
