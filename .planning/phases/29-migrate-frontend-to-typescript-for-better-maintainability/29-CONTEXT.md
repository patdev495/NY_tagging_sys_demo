# Phase 29: Migrate frontend to TypeScript for better maintainability - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Chuyển đổi toàn bộ mã nguồn JavaScript (.js) và Vue SFC (.vue) của frontend_v2 sang TypeScript (.ts/.vue với lang="ts"). Bao gồm cấu hình TypeScript, rename files, thêm type annotations, và đảm bảo build thành công.

Không thay đổi logic, không thêm tính năng mới, không refactor kiến trúc.

</domain>

<decisions>
## Implementation Decisions

### D-01: Migration Strategy — Big-bang (toàn bộ cùng lúc)
- Với quy mô nhỏ (~30 files), chuyển đổi toàn bộ trong 1 phase tránh tình trạng mixed JS/TS gây confusion.
- Không cần duy trì `allowJs: true` lâu dài — clean migration.

### D-02: TypeScript Config — Strict mode từ đầu
- `strict: true` bật toàn bộ strict checks (noImplicitAny, strictNullChecks, strictFunctionTypes, etc.)
- Target: `ES2020` (phù hợp với browser support hiện tại)
- Module: `ESNext` (tương thích Vite)
- Path alias: `@/*` → `src/*` (nếu chưa có)
- `compilerOptions.types`: bao gồm `vite/client`

### D-03: Vue SFC — `<script setup lang="ts">` 
- Sử dụng `<script setup lang="ts">` cho tất cả component (modern Vue 3 recommended approach)
- Props: dùng `defineProps<{...}>()` với type-based declaration
- Emits: dùng `defineEmits<{...}>()` với type-based declaration  
- Không dùng `defineComponent()` — ít boilerplate hơn, type inference tốt hơn

### D-04: Type Definitions — Centralized per feature + shared types
- Tạo thư mục `src/types/` cho shared types (API responses, common interfaces)
- Mỗi feature module có file `types.ts` riêng nếu cần (e.g., `features/packing/types.ts`)
- API response types đặt cùng với API module (e.g., `features/catalog/api.ts` export cả types)
- Store state types define inline trong store files

### D-05: File Renaming Convention
- `.js` → `.ts` cho tất cả file logic (api, router, stores, composables, i18n)
- `.vue` giữ nguyên extension, chỉ thêm `lang="ts"` vào `<script setup>`
- `main.js` → `main.ts`
- `vite.config.js` → `vite.config.ts`

### D-06: Dependencies cần thêm
- `typescript` (devDependency)
- `vue-tsc` (devDependency — type checking cho Vue SFC)
- Cập nhật script build: `"build": "vue-tsc --noEmit && vite build"`
- Cập nhật script dev: giữ nguyên `"dev": "vite"` (Vite tự handle TS)

### Agent's Discretion
- Thứ tự migrate các file (agent tự quyết định thứ tự hợp lý)
- Chi tiết type annotations cho từng function/variable
- Xử lý các edge case khi convert (any → proper types)
- Quyết định dùng `interface` vs `type` cho từng trường hợp cụ thể

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above.

### Project Config
- `frontend_v2/package.json` — Current dependencies and scripts
- `frontend_v2/vite.config.js` — Current Vite configuration (will be renamed to .ts)

### Core Architecture
- `frontend_v2/src/main.js` — App entry point
- `frontend_v2/src/core/router/index.js` — Router config
- `frontend_v2/src/core/stores/settings.js` — Pinia store pattern
- `frontend_v2/src/core/stores/system.js` — Pinia store pattern
- `frontend_v2/src/core/api.js` — Axios instance setup

### Feature Modules (representative files)
- `frontend_v2/src/features/packing/composables/useScanLogic.js` — Composable pattern
- `frontend_v2/src/features/packing/api.js` — Feature API pattern
- `frontend_v2/src/features/catalog/api.js` — Feature API pattern

### Vue Components (representative)
- `frontend_v2/src/views/PackingPage.vue` — Largest component (~27KB)
- `frontend_v2/src/features/packing/components/ScannedList.vue` — Feature component pattern
- `frontend_v2/src/core/components/AppHeader.vue` — Core component pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Current File Inventory (30 files to migrate)
**JS files (7):**
- `src/main.js` — Entry point
- `src/core/api.js` — Axios instance
- `src/core/router/index.js` — Vue Router config
- `src/core/stores/settings.js` — Settings Pinia store
- `src/core/stores/system.js` — System Pinia store
- `src/features/packing/composables/useScanLogic.js` — Scan logic composable
- `src/i18n/index.js` — i18n configuration
- Plus all feature `api.js` files (catalog, history, packing, print)

**Vue SFC files (23):**
- Core components: AppHeader, Notification, Sidebar
- Core layouts: AdminLayout
- Feature components: CatalogSelection, ScanBuffer, ScannedList, SessionHeader, EmergencyReprintModal, PrintStatusBanner, SettingsModal
- Views: PackingPage, CartonHistoryPage, CustomerManagementPage, DashboardPage, LoginPage, ProductManagementPage, SNLookupPage
- Root: App.vue

### Established Patterns
- Feature-based architecture: `features/{name}/api.js`, `features/{name}/components/*.vue`
- Pinia stores with Options API style
- Composables pattern: `useScanLogic.js`
- Axios-based API layer with centralized instance
- Vue Router with lazy-loaded routes

### Integration Points
- `vite.config.js` — needs TS support config
- `package.json` — needs typescript, vue-tsc devDependencies
- `tsconfig.json` — new file, needs creation
- All import paths need `.js` extension removal if present

</code_context>

<specifics>
## Specific Ideas

- User yêu cầu chuyển sang TypeScript để dễ maintain → focus vào type-safety thực tế, không over-engineer types
- Project quy mô nhỏ-trung bình → big-bang migration khả thi và sạch hơn incremental

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 29-migrate-frontend-to-typescript-for-better-maintainability*
*Context gathered: 2026-05-08*
