# Phase 14 Context: Frontend UI Extraction & Pinia Migration

## Architectural Decisions
1. **Component Modularity**: 
   - `PackingStation.vue` sẽ được tách thành các component nhỏ tại `src/features/*/components/`.
   - Sử dụng `<style scoped>` cho từng component để đảm bảo tính đóng gói (encapsulation).
   - Tên component tuân thủ quy tắc `PascalCase`.

2. **State Management**:
   - Sử dụng **Pinia** để quản lý trạng thái toàn cục thay vì prop drilling.
   - Các Store dự kiến:
     - `useSettingsStore`: Quản lý `stationId`, `templatePath`, `printerName`, v.v. (Lưu/Tải từ localStorage).
     - `useSystemStore`: Quản lý trạng thái kết nối (`isOnline`, `isAgentConnected`).
   - Các logic nghiệp vụ phức tạp (như quét mã) vẫn giữ trong **Composables** để tái sử dụng hoặc test độc lập.

3. **Routing & Orchestration**:
   - `src/App.vue` sẽ đóng vai trò Entry point.
   - `src/views/PackingPage.vue` (tên mới thay cho PackingStation.vue) sẽ là Orchestrator lắp ghép các UI components.

## Component Map
- `core/components/AppHeader.vue`
- `core/components/Notification.vue`
- `features/catalog/components/CatalogSelection.vue`
- `features/packing/components/SessionHeader.vue`
- `features/packing/components/ScanBuffer.vue`
- `features/packing/components/ScannedList.vue`
- `features/print/components/PrintStatusBanner.vue`
- `features/settings/components/SettingsModal.vue`
- `features/print/components/EmergencyReprintModal.vue`
