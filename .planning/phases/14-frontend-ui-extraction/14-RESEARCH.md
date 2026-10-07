# Phase 14 Research: Frontend UI Extraction

## 1. Dependency Updates
- Cần cài đặt `pinia` vào `frontend_v2`.
- Cần cài đặt `@lucide/vue-next` (nếu cần, nhưng hiện tại codebase đang dùng FontAwesome).

## 2. Store Design (Pinia)
### `useSettingsStore`
- **State**: `stationId`, `templatePath`, `printerName`, `printFolder`, `audioDeviceId`, `serverPrint`.
- **Actions**: `loadSettings()`, `saveSettings(newSettings)`.
- **Persistence**: `localStorage`.

### `useSystemStore`
- **State**: `isOnline`, `isAgentConnected`, `notification`.
- **Actions**: `setNotification(text, type)`, `setAgentStatus(status)`.

## 3. Component Extraction Map
Dựa trên `PackingStation.vue`, ta sẽ bóc tách các đoạn HTML/CSS tương ứng:

| Component | Lines (Approx) | Purpose |
| --- | --- | --- |
| `AppHeader.vue` | 4-23 | Top bar, badges |
| `CatalogSelection.vue` | 37-78 | Customer/Product selection |
| `SessionHeader.vue` | 84-143 | Session inputs (Job Order, etc.) |
| `ProgressBar.vue` | 145-153 | Progress bar |
| `PrintStatusBanner.vue` | 155-183 | Result indicator |
| `ScanBuffer.vue` | 185-225 | Main scan input |
| `ScannedList.vue` | 229-248 | Sidebar |
| `SettingsModal.vue` | 335-408 | Settings UI |
| `EmergencyReprintModal.vue` | 261-332 | Reprint UI |

## 4. Orchestration Logic
`PackingPage.vue` sẽ điều phối luồng:
1. Load Settings & Customers khi mounted.
2. Quản lý `currentProduct`.
3. Khi `currentProduct` thay đổi, reset `useScanLogic`.
4. Lắng nghe event từ `ScanBuffer` để thực hiện `finalizeCarton`.

## 5. CSS Strategy
- Copy các block CSS liên quan từ `index.css` vào `<style scoped>` của từng file `.vue`.
- Giữ lại các biến màu (CSS Variables) và reset cơ bản trong `index.css` (hoặc `core/styles/main.css`).
