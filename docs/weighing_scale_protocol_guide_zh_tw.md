# 電子秤串口通信協議與 Web 系統整合指南
# Electronic Weighing Scale Serial Protocol & Web Integration Guide
*(適用於工廠產線稱重包裝與標籤列印系統 / Industrial Weight-based Packaging & Label Printing)*

---

## 1. 適用硬體與儀表型號 (Applicable Scale & Indicator Models)

本指南與協議規範完全基於工廠產線實際部署驗證之標準：

* **OKS 系列電子計重秤 / 工業稱重儀表** (OKS Series Electronic Weighing Scales & Indicators - 產線實時運行型號)
* **耀華 (Yaohua) XK3190 系列儀表** (XK3190-A12, XK3190-A12E, XK3190-A9, XK3190-A27 等)
* **CAS 系列稱重儀表** (CAS CI Series / DB-1H Series)
* **標準 ASCII 連續輸出型工業電子秤** (Standard ASCII Continuous Output Scales & Balances)

---

## 2. 物理連接與串口參數 (Physical Connection & Serial Specs)

### 2.1. 物理介面 (Physical Interface)
* **連接介面**: RS-232 (DB9 公頭/母頭) 或 USB 轉 RS-232 轉接線 (CH340 / FTDI / PL2303 / CP2102 晶片)。
* **線路定義 (Simplex 單向通信模式)**:
  * 秤端 `TXD` (發送腳) ──► 電腦端 `RXD` (Pin 2)
  * 秤端 `GND` (地線腳) ──► 電腦端 `GND` (Pin 5)
  * *(注：連續發送模式下，電腦端只需被動讀取數據，無須反向向秤發送指令)*。

### 2.2. 串口通信參數 (Serial Port Configuration)

| 參數 (Parameter) | 產線標準預設值 (Default) | 支援選項 (Supported) | 說明 (Description) |
| :--- | :--- | :--- | :--- |
| **波特率 (Baud Rate)** | **`9600`** | `2400`, `4800`, `9600`, `19200` | 需與秤端儀表內部設定保持一致 |
| **數據位 (Data Bits)** | **`8`** | `8` | 標準 8 bits |
| **校驗位 (Parity)** | **`None`** (無校驗) | `None` | `serial.PARITY_NONE` |
| **停止位 (Stop Bits)** | **`1`** | `1` | `serial.STOPBITS_ONE` |
| **流控 (Flow Control)** | **`None`** | `None` | `DTR=True`, `RTS=True` (開啟線路供電) |
| **超時時間 (Read Timeout)**| **`0.5 秒`** | `0.2s ~ 1.0s` | 避免讀取阻塞 |

---

## 3. 通信協議與數據幀解構 (Data Frame & Packet Structure)

### 3.1. 傳輸機制：連續發送模式 (Continuous Streaming Mode)
電子秤儀表設定為連續發送模式後，每秒自動向串口推送 **10 ~ 20 次** 實時重量數據包。

### 3.2. 幀分界符與過濾 (Delimiters & Cleaning)
* **幀尾分界符 (Delimiters)**: `\r\n` (`0x0D 0x0A`)、`\n` (`0x0A`) 或 `\r` (`0x0D`)。
* **幀頭控制符**: 部分型號開頭含 `\x02` (STX)，解析前需過濾清除。
* **雜訊與標題過濾**: 自動過濾包含 `DATE`、`TIME`、`TICKET`、`COUNT`、`AM/PM`、分界線 `---` / `===` 等非重量字串。

### 3.3. 典型數據幀範例 (Data Payload Samples)

#### 範例 1: 標準穩定毛重 (Stable Gross Weight)
```text
ST,GS,+  12.450kg\r\n
```
* `ST` : **穩定狀態 (Stable)** - 重量已靜止。
* `GS` : **毛重 (Gross Weight)**。
* `+` : 正數符號 (負數為 `-`)。
* `12.450` : 重量讀數。
* `kg` : 計量單位。

#### 範例 2: 晃動/不穩定狀態 (Unstable Weight)
```text
US,GS,+  12.380kg\r\n
```
* `US` : **不穩定 (Unstable)** - 工人放貨或晃動中，系統應鎖定列印按鈕。

#### 範例 3: 去皮後的淨重 (Net Weight after Tare)
```text
ST,NT,+  10.000kg\r\n
```
* `NT` : **淨重 (Net Weight)** - 已扣除皮重 (Tare)。

#### 範例 4: 零點狀態 (Zero Point)
```text
ST,GS,+   0.000kg\r\n
```

### 3.4. 狀態標誌位解析表 (Status Flags)

| 標誌代碼 (Flag) | 英文含義 | 業務邏輯處置 (Business Action) |
| :--- | :--- | :--- |
| **`ST`** | Stable (穩定) | **允許** 觸發包裝檢驗、產生箱號、發送列印標籤 |
| **`US`** | Unstable (晃動/跳動中) | **禁止** 觸發包裝，介面顯示黃色/紅色等待穩定 |
| **`GS` / `GROSS`** | Gross Weight (毛重) | 顯示毛重讀數 |
| **`NT` / `NET`** | Net Weight (淨重) | 顯示扣除容器後的淨重 |
| **`PT` / `TARE`** | Tare (已去皮) | 提示當前已扣重 |
| **`ZERO`** | Zero (零點) | 當前秤盤為空 |

---

## 4. 數據提取與正則表達式 (Regex & Normalization)

### 4.1. 數值提取正則表達式
```regex
(?P<weight>[+-]?\s*\d+(?:[.,]\d+)?)
```

### 4.2. 規範化處理流程
1. 將接收到的 Byte 流轉換為 ASCII 字串，移除 `\x02` 與首尾空白。
2. 檢查包含 `ST` 還是 `US` ──► 確定 `is_stable`。
3. 檢查包含 `NT` 還是 `GS` ──► 確定 `is_net`。
4. 檢查單位 (`kg`、`g`、`lb`)。
5. 透過正則提取數值字串，移除所有空格並去除前綴 `+`（如 `+  12.450` ──► `12.450`）。
6. 將 `,` 替換為 `.` 並轉為浮點數進行公差檢驗 (`min_weight <= weight <= max_weight`)。

---

## 5. Web 整合方案一：純前端 Web Serial API (免安裝後台程式)

若您的 Web 系統運行於 **Google Chrome** 或 **Microsoft Edge** (HTTPS 或 localhost 環境)，可直接在前端 Javascript 讀取串口。

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>電子秤 Web Serial 直連測試 (Scale Live Test)</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; padding: 40px; background: #0f172a; color: #f8fafc; }
    .card { background: #1e293b; border-radius: 16px; padding: 32px; max-width: 480px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
    .weight-display { font-size: 64px; font-weight: 800; color: #10b981; font-family: monospace; text-align: center; margin: 24px 0; letter-spacing: -1px; }
    .status-row { display: flex; justify-content: space-around; margin-top: 20px; font-size: 14px; }
    .badge { padding: 6px 16px; border-radius: 9999px; font-weight: 600; }
    .badge-stable { background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid #059669; }
    .badge-unstable { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid #dc2626; }
    .btn { width: 100%; padding: 14px; font-size: 16px; font-weight: 700; border: none; border-radius: 10px; background: #3b82f6; color: white; cursor: pointer; transition: all 0.2s; }
    .btn:hover { background: #2563eb; }
    .btn:disabled { background: #475569; cursor: not-allowed; }
  </style>
</head>
<body>

<div class="card">
  <h2 style="text-align: center; margin-top: 0;">電子秤 Web 直連 (OKS / Yaohua)</h2>
  <button id="btnConnect" class="btn" onclick="connectScale()">連接電子秤 (Connect Serial)</button>
  
  <div class="weight-display" id="weightVal">0.000 kg</div>
  
  <div class="status-row">
    <div>穩定狀態: <span id="stableBadge" class="badge badge-unstable">未連接</span></div>
    <div>計量模式: <span id="modeBadge" style="font-weight: 600;">--</span></div>
  </div>
</div>

<script>
let port;
let reader;
let buffer = "";

async function connectScale() {
  if (!("serial" in navigator)) {
    alert("瀏覽器不支援 Web Serial API，請使用 Google Chrome 或 Edge 瀏覽器！");
    return;
  }
  try {
    port = await navigator.serial.requestPort();
    await port.open({ baudRate: 9600, dataBits: 8, stopBits: 1, parity: "none" });

    document.getElementById("btnConnect").disabled = true;
    document.getElementById("btnConnect").innerText = "已連接電子秤 (Connected)";
    readSerial();
  } catch (err) {
    alert("串口打開失敗: " + err.message);
  }
}

async function readSerial() {
  const textDecoder = new TextDecoderStream();
  port.readable.pipeTo(textDecoder.writable);
  reader = textDecoder.readable.getReader();

  const regex = /([+-]?\s*\d+(?:[.,]\d+)?)/;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    if (value) {
      buffer += value;
      let lines = buffer.split(/[\r\n]+/);
      buffer = lines.pop(); // 保留未完成字串

      for (let rawLine of lines) {
        let line = rawLine.replace(/\x02/g, "").trim();
        if (!line) continue;

        let upper = line.toUpperCase();
        let match = regex.exec(line);
        if (match) {
          let numStr = match[1].replace(/\s+/g, "").replace(/^\+/, "");
          let unit = (upper.includes("G") && !upper.includes("KG")) ? "g" : (upper.includes("LB") ? "lb" : "kg");
          let isStable = !upper.includes("US") && !upper.includes("UNSTABLE");
          let isNet = upper.includes("NT") || upper.includes("NET");

          // 更新 UI
          document.getElementById("weightVal").innerText = `${numStr} ${unit}`;
          const badge = document.getElementById("stableBadge");
          badge.innerText = isStable ? "已穩定 (Stable)" : "跳動中 (Unstable)";
          badge.className = "badge " + (isStable ? "badge-stable" : "badge-unstable");
          document.getElementById("modeBadge").innerText = isNet ? "淨重 (Net)" : "毛重 (Gross)";
        }
      }
    }
  }
}
</script>
</body>
</html>
```

---

## 6. Web 整合方案二：產線 Native Print Agent 架構 (實際部署標準)

在產線複雜環境中（需支援 **全球快捷鍵 F9 / 腳踏板開關** 以及 **BarTender / Zebra 標籤機直接列印**），推薦採用我們目前運行的 **Print Agent (本地服務)** 架構：

### 6.1. 系統架構拓撲 (Architecture Flow)
```
[電子秤 OKS / 耀華] ──(RS-232 / 9600)──► [Print Agent (Python/C# 本地服務 Port 8080)]
[腳踏板 / F9 熱鍵] ────────────────────► [Print Agent] (Win32 全局監聽)
                                                ▲
                                                │ REST API / Polling (每 200ms)
                                                ▼
[Web 前端介面 (Vue / React)] ◄──────────────────┘
```

### 6.2. Print Agent 提供之標準 REST API 端點

#### 1. 取得即時重量 (`GET http://localhost:8080/scale/current`)
* **Request**: `GET /scale/current`
* **Response (JSON)**:
```json
{
  "weight": 12.450,
  "weight_str": "12.450",
  "unit": "kg",
  "is_stable": true,
  "is_net": false,
  "is_tare": false,
  "is_zero": false,
  "is_hold": false,
  "connected": true,
  "is_streaming": true,
  "timestamp": 1771667820.125
}
```

#### 2. 查詢連接狀態 (`GET http://localhost:8080/scale/status`)
* **Response (JSON)**:
```json
{
  "connected": true,
  "status": "connected",
  "port": "COM3",
  "baudrate": 9600,
  "hotkey": "F9",
  "is_streaming": true,
  "available_ports": [
    {"device": "COM3", "description": "USB-SERIAL CH340 (COM3)"}
  ]
}
```

#### 3. 執行去皮 / 置零 (`POST http://localhost:8080/scale/tare` | `POST /scale/zero`)
* **Response**: `{"success": true}`

---

## 7. 產線作業流程與防呆邏輯 (Production Best Practices)

1. **去皮 (Tare) 與 置零 (Zero)**：
   * 產線作業時，作業員直接按壓電子秤儀表上的 **`[TARE]` (去皮)** 或 **`[ZERO]` (歸零)** 實體按鍵。
   * 電子秤會自動在輸出字串中切換標誌（`NT` 淨重），Web 端被動識別即可。
2. **防抖與穩定檢驗 (Debounce & Stability Validation)**：
   * Web 系統在接收到列印觸發（點擊按鈕或踩下腳踏板）時，必須同時滿足：
     1. `is_stable === true` (重量已完全靜止)
     2. `min_weight <= weight <= max_weight` (重量在公差合格範圍內)
   * 若條件不符，介面應鎖定並發出告警音，杜絕產線貼錯標籤或漏裝物品。
