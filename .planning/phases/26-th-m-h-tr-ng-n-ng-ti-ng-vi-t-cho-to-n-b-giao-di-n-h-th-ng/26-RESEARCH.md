# Phase 26: Thêm hỗ trợ ngôn ngữ tiếng Việt cho toàn bộ giao diện hệ thống - RESEARCH

**Date:** 2026-05-06
**Status:** Research Complete

## 1. Hardcoded Strings Assessment

A scan of the frontend codebase reveals extensive use of hardcoded strings in both English and Vietnamese.

### Examples of Hardcoded Strings:
- **Core Components (`AppHeader.vue`):**
    - `NY Packing Station`
    - `System Online` / `Connecting...`
    - `Audio Alert: Active (Click to Test)` / `Audio Alert: Click to Activate/Test`
    - `Emergency Reprint` (Tooltip)
    - `Settings` (Tooltip)
    - `Admin Dashboard` (Tooltip)

- **Packing Station (`PackingPage.vue`):**
    - `RESCAN MODE: Updating Carton`
    - `Cancel`
    - `AGENT OFFLINE: Vui lòng bật agent.py để bắt đầu quét hàng.`
    - `THIẾU FILE TEM: Không tìm thấy {{ templateFilename }} trong thư mục cục bộ.`
    - `Scan S/N here...`
    - `Please enter Job Order!`
    - `Duplicate S/N`
    - `Carton {{ cartonSn }} Printed!`
    - `PDF label downloaded!`

- **Settings (`SettingsModal.vue`):**
    - Labels: `Print Mode`, `Printer Name`, `Local Template Folder`, `Server API URL`, etc.
    - Placeholders and tooltips.

- **Admin Pages:**
    - Table headers: `Date`, `Carton SN`, `Product`, `Customer`, `User`.
    - Buttons: `Add Product`, `Edit`, `Delete`.

- **API Layer (`api.js`):**
    - Error messages: `Không thể kết nối tới Print Agent. Bạn đã bật file agent.py chưa?`

## 2. Technical Approach: `vue-i18n`

We will use **`vue-i18n` (version 9+)** as the standard internationalization library for Vue 3.

### Installation
```bash
npm install vue-i18n@9
```

### Configuration Structure
- `frontend_v2/src/i18n/`
    - `index.js`: Initialization and export of `i18n` instance.
    - `locales/`
        - `en.json`: English translations.
        - `vi.json`: Vietnamese translations.

### Usage in Components (Composition API)
```javascript
import { useI18n } from 'vue-i18n';
const { t, locale } = useI18n();

// In template: {{ t('packing.scan_placeholder') }}
```

## 3. State Management & Persistence

The user's language preference should be stored in the **`SettingsStore` (Pinia)**.

- **New State Property:** `language` (default: 'vi').
- **Persistence:** Ensure the `language` property is saved to `localStorage` (already handled by the store's current persistence logic in `SettingsStore.js`).
- **Sync:** The `i18n.global.locale` should be updated whenever the store's `language` changes.

## 4. UI/UX: Language Switcher

### Placement Options:
1. **AppHeader.vue**: Quick access next to the settings/admin buttons.
2. **SettingsModal.vue**: Part of the system configuration.

**Recommendation:** Place a simple toggle (e.g., "EN | VI") in the **AppHeader** for high visibility and convenience, or a dropdown in the **SettingsModal** if we want to keep the header clean. Given the "Premium" requirement, a beautiful toggle in the header is preferred.

## 5. Backend Considerations

The backend (`backend_v2`) returns raw data and some error details.
- **Error Mapping:** We should create an error mapping system in the frontend that takes backend error codes/messages and translates them.
- **Example:** `if (msg.includes('already in use')) return t('errors.sn_exists');`

## 6. Implementation Strategy

1. **Setup**: Install `vue-i18n`, create the structure, and wrap the app.
2. **Extraction**: Methodically extract strings from components into `en.json` and `vi.json`.
3. **Integration**: Replace hardcoded strings with `$t()` or `t()`.
4. **Settings Update**: Add language choice to `SettingsStore` and `SettingsModal`.
5. **Language Switcher**: Add the toggle to `AppHeader`.

## 7. Validation Strategy

- Verify all screens are fully translated when switching languages.
- Ensure the selected language persists after page reload.
- Check that dynamic strings (e.g., `Carton {sn} Printed`) work correctly with placeholders.

---
**Next Step:** Proceed to planning the phase based on this research.
