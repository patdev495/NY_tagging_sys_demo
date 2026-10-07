# Phase 26: Thêm hỗ trợ ngôn ngữ tiếng Việt cho toàn bộ giao diện hệ thống - Plan

**Goal**: Implement full multi-language support (English and Vietnamese) for the entire system interface using `vue-i18n`.
**Phase**: 26
**Slug**: th-m-h-tr-ng-n-ng-ti-ng-vi-t-cho-to-n-b-giao-di-n-h-th-ng

<files_modified>
- frontend_v2/package.json
- frontend_v2/src/main.js
- frontend_v2/src/core/stores/settings.js
- frontend_v2/src/core/components/AppHeader.vue
- frontend_v2/src/features/settings/components/SettingsModal.vue
- frontend_v2/src/views/PackingPage.vue
- frontend_v2/src/features/packing/components/SessionHeader.vue
- frontend_v2/src/features/packing/components/ScanBuffer.vue
- frontend_v2/src/features/print/components/PrintStatusBanner.vue
- frontend_v2/src/features/print/api.js
- frontend_v2/src/views/admin/CartonHistoryPage.vue
- frontend_v2/src/views/admin/CustomerManagementPage.vue
</files_modified>

<threat_model>
- **Threat**: UI breaking due to longer Vietnamese strings compared to English.
  - **Mitigation**: Use flexible layouts (Flexbox/Grid) and test all screens in both languages.
- **Threat**: Language preference lost on reload.
  - **Mitigation**: Persist language in `SettingsStore` (localStorage) and initialize i18n from the store value.
- **Threat**: Missing translations causing empty UI elements.
  - **Mitigation**: Define a fallback language (English) and ensure both `en.json` and `vi.json` are synchronized.
</threat_model>

<plans>

## Wave 1: Foundation

### Task 1: Install `vue-i18n`
**Action**: Install `vue-i18n` version 9.
**Read First**:
- `frontend_v2/package.json`
**Acceptance Criteria**:
- `npm list vue-i18n` shows version 9.x.

### Task 2: Create i18n Structure and Initialization
**Action**: 
- Create `frontend_v2/src/i18n/locales/en.json` and `vi.json`.
- Create `frontend_v2/src/i18n/index.js` to configure i18n.
- Register i18n in `frontend_v2/src/main.js`.
**Read First**:
- `frontend_v2/src/main.js`
**Acceptance Criteria**:
- `frontend_v2/src/i18n/index.js` exists and exports a `createI18n` instance.
- `frontend_v2/src/main.js` contains `app.use(i18n)`.

## Wave 2: State and Settings

### Task 3: Update Settings Store
**Action**: Add `language` property to `useSettingsStore` in `src/core/stores/settings.js`.
**Read First**:
- `frontend_v2/src/core/stores/settings.js`
**Acceptance Criteria**:
- `settings.js` has `language: 'vi'` in state.
- `settings.js` handles persistence for `language`.

### Task 4: Add Language Selection to Settings Modal
**Action**: Add a dropdown or toggle for language selection in `SettingsModal.vue`.
**Read First**:
- `frontend_v2/src/features/settings/components/SettingsModal.vue`
**Acceptance Criteria**:
- `SettingsModal.vue` has a field to change `settings.language`.

## Wave 3: UI Extraction - Core & Packing

### Task 5: Translate App Header
**Action**: Replace hardcoded strings in `AppHeader.vue` with `$t()`.
**Read First**:
- `frontend_v2/src/core/components/AppHeader.vue`
**Acceptance Criteria**:
- `AppHeader.vue` uses `t('header.title')`, `t('header.status_online')`, etc.
- `en.json` and `vi.json` contain these keys.

### Task 6: Translate Packing Page and Components
**Action**: Replace hardcoded strings in `PackingPage.vue`, `SessionHeader.vue`, `ScanBuffer.vue`, and `PrintStatusBanner.vue`.
**Read First**:
- `frontend_v2/src/views/PackingPage.vue`
- `frontend_v2/src/features/packing/components/SessionHeader.vue`
- `frontend_v2/src/features/packing/components/ScanBuffer.vue`
- `frontend_v2/src/features/print/components/PrintStatusBanner.vue`
**Acceptance Criteria**:
- All Vietnamese and English hardcoded strings in these files are replaced with `t()` calls.
- `locales/*.json` contain corresponding entries for `packing`, `scan`, `print_status` categories.

## Wave 4: UI Extraction - Admin & API

### Task 7: Translate Admin Pages
**Action**: Replace hardcoded strings in `CartonHistoryPage.vue` and `CustomerManagementPage.vue`.
**Read First**:
- `frontend_v2/src/views/admin/CartonHistoryPage.vue`
- `frontend_v2/src/views/admin/CustomerManagementPage.vue`
**Acceptance Criteria**:
- Table headers and buttons are translated.

### Task 8: Translate API Error Messages
**Action**: Move hardcoded Vietnamese error messages in `src/features/print/api.js` to translation files and use a mapping or direct call.
**Read First**:
- `frontend_v2/src/features/print/api.js`
**Acceptance Criteria**:
- `api.js` does not contain hardcoded Vietnamese strings.

## Wave 5: Language Switcher Enhancements

### Task 9: Add Language Switcher to Header
**Action**: Add a beautiful language toggle (EN/VI) to `AppHeader.vue` for quick access.
**Read First**:
- `frontend_v2/src/core/components/AppHeader.vue`
**Acceptance Criteria**:
- A toggle exists in the header.
- Clicking it switches the language immediately.

</plans>

<verification>
## Verification Criteria
1. Switching language in Settings or Header updates the entire UI immediately.
2. The chosen language persists after a page refresh.
3. No hardcoded Vietnamese or English strings remain in the main UI components.
4. Tooltips and placeholders are also translated.
</verification>

<must_haves>
- [ ] `vue-i18n` integrated correctly.
- [ ] English and Vietnamese locales fully populated.
- [ ] Language preference persists across sessions.
- [ ] Language switcher accessible in the UI.
</must_haves>
