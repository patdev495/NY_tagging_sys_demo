# TÀI LIỆU THIẾT KẾ VÀ HƯỚNG DẪN XÂY DỰNG HỆ THỐNG WEB BÁN DATA 4G / VPN TẠI NHẬT BẢN

> **Mục đích tài liệu:** Tài liệu kỹ thuật chi tiết dành cho Agent / Lập trình viên để triển khai một hệ thống web hoàn chỉnh: Bán tài khoản VPN/Proxy vượt giới hạn băng thông 4G của các nhà mạng Nhật Bản, tự động hóa thanh toán, tự động render key/link subscription theo tháng và dung lượng.

---

## 1. TỔNG QUAN & NGUYÊN LÝ HOẠT ĐỘNG KỸ THUẬT

### 1.1. Bối cảnh nghiệp vụ
* **Khách hàng mục tiêu:** Người Việt Nam sinh sống, học tập và làm việc tại Nhật Bản (du học sinh, kỹ sư, tu nghiệp sinh).
* **Vấn đề của khách hàng:** Sử dụng các gói SIM 4G hữu hạn dung lượng (như Docomo, SoftBank, AU, UQ Mobile, Rakuten, LINEMO...). Khi dùng hết dung lượng tốc độ cao trong tháng, nhà mạng sẽ kích hoạt bộ lọc DPI (Deep Packet Inspection) bóp băng thông xuống còn 128 kbps - 1 Mbps, khiến việc xem video, lướt web hoặc gọi về gia đình bị giật lag.
* **Mục tiêu của hệ thống:** Cung cấp đường truyền VPN vượt qua lớp bóp băng thông, duy trì tốc độ cao liên tục trong suốt chu kỳ đăng ký (1 tháng, 3 tháng, 6 tháng...).

### 1.2. Nguyên lý vượt giới hạn băng thông (Zero-Rating & SNI Bug Spoofing)
1. **Lớp mạng của nhà mạng Nhật:** Dù bóp băng thông các trang web thông thường, nhà mạng bắt buộc phải "thả lỏng" (không bóp hoặc ưu tiên băng thông) cho một số tên miền nội bộ (cổng nạp tiền, trang portal quản lý tài khoản của nhà mạng, hoặc dịch vụ miễn cước như ứng dụng LINE trên mạng SoftBank/LINEMO).
2. **Kỹ thuật SNI Spoofing (Ngụy trang gói tin):**
   * Ứng dụng VPN Client trên điện thoại (Shadowrocket trên iOS, v2rayNG trên Android) chặn toàn bộ lưu lượng mạng máy khách.
   * Dữ liệu được mã hóa và đóng gói thành giao thức **VMess** hoặc **VLESS** qua giao thức mạng **WebSocket (WS)** hoặc **TCP/XTLS**.
   * Trong phần tiêu đề gói tin (TLS Handshake Header), app sẽ chèn trường **SNI (Server Name Indication)** và **Host Header** là tên miền "được thả lỏng" của nhà mạng Nhật.
3. **Cơ chế chuyển tiếp qua VPS Nhật:**
   * Nhà mạng kiểm tra gói tin, thấy SNI thuộc danh sách ưu tiên $\rightarrow$ Cho phép truyền đi với tốc độ 4G tối đa mà không bị bóp.
   * Gói tin thực chất được gửi thẳng đến địa chỉ IP của VPS tại Nhật (hiện tại là: `160.251.143.195`, cổng `443` hoặc `80`).
   * Lõi **Xray-core** trên VPS nhận diện gói tin, giải mã VMess, dùng đường truyền cáp quang tốc độ cao nội địa Nhật của VPS tải dữ liệu từ YouTube/TikTok/Facebook, sau đó mã hóa trả ngược về điện thoại của khách.

---

## 2. HIỆN TRẠNG MÁY CHỦ PROXY HIỆN CÓ

Máy chủ hiện tại đã được cấu hình và kiểm tra thực tế với các thông số sau:
* **Địa chỉ IP:** `160.251.143.195` (Dải mạng GMO Internet Nhật Bản, ping nội địa Nhật cực thấp: ~5 - 15ms).
* **Hệ điều hành:** Ubuntu 24.04.4 LTS (Noble Numbat).
* **Phần cứng:** 2 vCPU (Intel Xeon Icelake 2.0GHz hỗ trợ mã hóa AES-NI cực nhanh), RAM 1GB (kèm 2GB Swap), SSD 100GB.
* **Dịch vụ đang chạy:**
  * Lõi chuyển tiếp: `xray-linux-amd64` (đang lắng nghe cổng `443`, `80`).
  * Quản lý: `x-ui` v0.3.2 (chạy trực tiếp dạng native systemd `x-ui.service`, database SQLite `/etc/x-ui/x-ui.db`, web panel cổng `54321`).
  * Trạng thái tải: Hoàn toàn rảnh rỗi (Load average 0.00).

---

## 3. KIẾN TRÚC HỆ THỐNG BÁN HÀNG TỰ ĐỘNG (TARGET ARCHITECTURE)

Hệ thống bán tài khoản cần được tách bạch thành 2 tầng độc lập:

```
[Khách hàng]
     │
     │ 1. Truy cập web, chọn gói cước (VD: Gói Softbank 300GB/tháng)
     ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1: WEB BÁN HÀNG & THANH TOÁN (Billing Web & Portal)                │
│                                                                        │
│  - Frontend (Next.js / Vue 3): Bảng giá, Hướng dẫn cài đặt, Quản lý    │
│  - Backend (FastAPI / Node.js / Laravel): Quản lý User, Gói, Hóa đơn   │
│  - Cổng thanh toán (PayOS / SePay / VietQR): Bắn Webhook khi tiền vào   │
│  - Database (PostgreSQL / SQLite): Lưu trữ đơn hàng, UUID, Hạn dùng    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   │ 2. Webhook thanh toán thành công
                                   │ 3. Gọi API sinh User & cấp Quota
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2: CỤM PROXY / VPN NODES (Xray Proxy Nodes)                       │
│                                                                        │
│  - Server Nhật (160.251.143.195): Xray-core tiếp nhận kết nối          │
│  - API Controller (Marzban API / XrayR / 3X-UI): Nhận lệnh tạo user,    │
│    giới hạn ngày hết hạn (Expire Date) và giới hạn dung lượng (Quota)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. CƠ CHẾ RENDER KEY / SUBSCRIPTION URL CHO KHÁCH HÀNG

### 4.1. Tại sao KHÔNG gửi key tĩnh rời rạc (`vmess://...` đơn lẻ)?
* Khách hàng không am hiểu kỹ thuật.
* Nếu nhà mạng đổi cơ chế chặn SNI, hoặc server cần đổi IP/thêm node dự phòng, bạn sẽ phải liên hệ từng khách để gửi lại key bằng tay $\rightarrow$ **Vỡ vận hành**.

### 4.2. Giải pháp chuẩn ngành: Link Subscription (Link đăng ký đồng bộ)
Hệ thống web sẽ cấp cho mỗi khách một đường link cá nhân duy nhất, ví dụ:
```text
https://billing.domain.com/api/v1/client/subscribe?token=a8f9c1b2e3d4
```

#### Cách hoạt động:
1. Khách hàng copy link trên vào app **Shadowrocket** (iOS) hoặc **v2rayNG** (Android).
2. App sẽ gửi HTTP GET request đến đường link trên:
   ```http
   GET /api/v1/client/subscribe?token=a8f9c1b2e3d4 HTTP/1.1
   Host: billing.domain.com
   User-Agent: Shadowrocket/1982
   ```
3. Web server kiểm tra `token`:
   * **Nếu đã hết hạn hoặc hết dung lượng:** Trả về danh sách node giả dạng: `⚠️ Gói cước của bạn đã hết hạn, vui lòng gia hạn tại website`.
   * **Nếu còn hiệu lực:**
     * Trả về HTTP Headers đặc biệt chuẩn quốc tế:
       ```http
       Subscription-Userinfo: upload=1073741824; download=15032385536; total=107374182400; expire=1735689600
       ```
       *(Ý nghĩa: App sẽ tự động hiển thị thanh tiến trình: Đã dùng 16GB / 100GB, còn lại 25 ngày ngay trên màn hình app của khách!)*.
     * Body trả về là chuỗi Base64 chứa danh sách các cấu hình server đã chèn sẵn SNI của từng nhà mạng Nhật (Server Softbank 01, Server Docomo 01, Server AU 01...).

---

## 5. THIẾT KẾ DỮ LIỆU & PHÂN HẠNG TÀI KHOẢN (DATA SCHEMA)

### 5.1. Bảng phân loại gói cước (Plans)
Mỗi gói cước cần định nghĩa 3 tham số cốt lõi:
1. **Thời hạn (Duration):** 30 ngày, 90 ngày, 180 ngày, 365 ngày.
2. **Băng thông tối đa (Bandwidth Quota):** 
   * Gói Cơ bản: 100 GB/tháng
   * Gói Nâng cao: 300 GB/tháng
   * Gói Không giới hạn: 1,000 GB/tháng (áp dụng giới hạn mềm FUP để tránh 1 người kéo torrent làm nghẽn cả server).
3. **Giới hạn thiết bị kết nối đồng thời (IP Limit):** Ví dụ 1 thiết bị hoặc 2 thiết bị.

### 5.2. Schema Database đề xuất (SQL / Prisma / SQLAlchemy)

```sql
-- 1. Bảng người dùng
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    telegram_id VARCHAR(64) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng cấu hình gói cước
CREATE TABLE plans (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,            -- VD: "Gói SoftBank VIP 300GB"
    price_vnd INT NOT NULL,                -- Giá tiền VNĐ (VD: 100000)
    duration_days INT NOT NULL,            -- Số ngày sử dụng (VD: 30)
    traffic_limit_bytes BIGINT NOT NULL,   -- Dung lượng tối đa tính bằng Bytes (VD: 300 * 1024^3)
    speed_limit_mbps INT DEFAULT 0,        -- 0 = Không giới hạn tốc độ
    device_limit INT DEFAULT 2,            -- Số thiết bị đồng thời
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. Bảng tài khoản VPN của khách (Subscriptions)
CREATE TABLE user_subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    plan_id VARCHAR(36) REFERENCES plans(id),
    sub_token VARCHAR(64) UNIQUE NOT NULL, -- Token bí mật trên link Subscription
    client_uuid VARCHAR(36) UNIQUE NOT NULL,-- UUID định danh trên Xray core
    upload_bytes BIGINT DEFAULT 0,
    download_bytes BIGINT DEFAULT 0,
    total_allowed_bytes BIGINT NOT NULL,
    expire_at TIMESTAMP NOT NULL,          -- Thời điểm hết hạn chính xác
    status VARCHAR(20) DEFAULT 'ACTIVE',   -- 'ACTIVE', 'EXPIRED', 'SUSPENDED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bảng lịch sử đơn hàng & thanh toán
CREATE TABLE orders (
    id VARCHAR(36) PRIMARY KEY,
    order_code INT UNIQUE NOT NULL,        -- Mã đơn hàng hiển thị cho khách chuyển khoản
    user_id VARCHAR(36) REFERENCES users(id),
    plan_id VARCHAR(36) REFERENCES plans(id),
    amount INT NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'PAID', 'CANCELLED'
    payment_gateway VARCHAR(50) DEFAULT 'PAYOS',
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. HAI HƯỚNG TRIỂN KHAI CHO AGENT TIẾP THEO

Tùy vào định hướng sản phẩm, Agent tiếp theo có thể chọn một trong hai phương án sau:

---

### PHƯƠNG ÁN A: DỰNG HỆ THỐNG MÃ NGUỒN MỞ SẴN CÓ (TRIỂN KHAI TRONG 1 NGÀY - KHUYÊN DÙNG)
Toàn bộ thị trường kinh doanh VPN hiện nay đều sử dụng bộ đôi tiêu chuẩn:
* **Web Bán Hàng & Quản Lý:** Dùng **[XBoard](https://github.com/cedar2025/Xboard)**.
  * Đã có sẵn giao diện người dùng mua hàng cực đẹp, hỗ trợ đa ngôn ngữ (có Tiếng Việt).
  * Đã tích hợp sẵn cổng thanh toán PayOS / VietQR (tự động 100%).
  * Đã có sẵn logic chia gói theo ngày, chia băng thông GB, giới hạn thiết bị, tự động ngắt kết nối khi hết hạn.
  * Tự động sinh link Subscription tương thích tất cả các app: Shadowrocket, v2rayNG, Clash, Sing-box...
* **Node Chuyển Tiếp (VPS Nhật):**
  * Gỡ bỏ `x-ui` cũ, cài đặt **XrayR** (hoặc XrayR-release).
  * Cấu hình XrayR kết nối về web XBoard qua WebAPI: XrayR tự động đồng bộ danh sách khách, kiểm tra hạn dùng theo thời gian thực mà không cần viết code kết nối.

---

### PHƯƠNG ÁN B: TỰ LẬP TRÌNH WEBSITE TỪ ĐẦU (CUSTOM FULLSTACK)
Nếu muốn xây dựng website bán hàng có giao diện riêng biệt theo thương hiệu:

1. **Kiến trúc Công nghệ:**
   * **Frontend:** Vue 3 / Nuxt 3 hoặc Next.js (TailwindCSS, giao diện Dark mode cao cấp, tối ưu cho trình duyệt di động).
   * **Backend:** FastAPI (Python) hoặc NestJS (Node.js).
   * **Database:** PostgreSQL hoặc SQLite.
   * **Cổng thanh toán tự động:** Tích hợp SDK [PayOS](https://payos.vn/) hoặc [SePay](https://sepay.vn/) (quét mã VietQR tự động xác nhận đơn hàng sau 3 giây).

2. **Kết nối điều khiển VPS Nhật:**
   * **Không nên** dùng `x-ui v0.3.2` cũ vì API thiếu token xác thực.
   * **Giải pháp chuẩn:** Cài đặt **[Marzban](https://github.com/Gozargah/Marzban)** lên VPS Nhật.
     * Marzban cung cấp toàn bộ RESTful API tài liệu OpenAPI / Swagger (`/api/user`).
     * Khi có đơn hàng thanh toán thành công, Backend của bạn chỉ cần gửi 1 request HTTP:
       ```bash
       POST https://160.251.143.195:8000/api/user
       Authorization: Bearer <ADMIN_TOKEN>
       Content-Type: application/json

       {
         "username": "khach_hang_01",
         "expire": 1735689600,
         "data_limit": 322122547200,
         "proxies": {
           "vmess": {},
           "vless": {}
         }
       }
       ```
     * Marzban sẽ trả về ngay lập tức đường link Subscription cho khách hàng. Backend của bạn chỉ cần lưu lại và hiển thị lên web cho khách bấm copy.

3. **Xử lý gia hạn và nâng cấp gói:**
   * Khi khách mua thêm 30 ngày $\rightarrow$ Gọi API Marzban cộng thêm `30 * 86400` giây vào trường `expire`.
   * Khi khách mua thêm 50GB dung lượng $\rightarrow$ Gọi API Marzban cộng thêm dung lượng vào `data_limit`.

---

## 7. CHECKLIST BẢO MẬT BẮT BUỘC TRƯỚC KHI BÁN HÀNG

1. **Đổi thông tin đăng nhập mặc định ngay lập tức:**
   * Không sử dụng tài khoản `1 / 1` trên panel hiện tại.
2. **Cấu hình Tên miền & SSL:**
   * Mua 1 tên miền (ví dụ: `vpn-japan4g.com`).
   * Trỏ DNS qua Cloudflare (bật Proxy vàng).
   * Cài đặt SSL Let's Encrypt / Certbot cho Web bán hàng và link Subscription để tránh bị chặn HTTPS.
3. **Chống lạm dụng tài nguyên:**
   * Chặn truy cập vào các trang web đen, torrent hoặc giao thức chia sẻ file P2P trên file cấu hình Xray (để tránh VPS bị nhà cung cấp GMO khóa server vì vi phạm bản quyền mạng tại Nhật Bản).
