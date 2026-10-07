---
phase: 29
slug: migrate-frontend-to-typescript-for-better-maintainability
title: Migrate frontend to TypeScript
wave: 1
depends_on: []
files_modified:
  - frontend_v2/package.json
  - frontend_v2/tsconfig.json
  - frontend_v2/vite.config.ts
  - frontend_v2/src/main.ts
  - frontend_v2/src/core/api.ts
  - frontend_v2/src/core/router/index.ts
  - frontend_v2/src/core/stores/settings.ts
  - frontend_v2/src/core/stores/system.ts
  - frontend_v2/src/features/packing/composables/useScanLogic.ts
  - frontend_v2/src/**/*.vue
autonomous: true
---

# Phase 29: Migrate frontend to TypeScript - Plan

## Goal
Chuyển đổi toàn bộ mã nguồn frontend_v2 sang TypeScript để cải thiện khả năng bảo trì và giảm thiểu lỗi runtime thông qua hệ thống type-safety mạnh mẽ.

## Waves

### Wave 1: Infrastructure & Core Logic
- Cấu hình TypeScript, cài đặt dependencies.
- Migrate các file core (main, api, router, stores).

### Wave 2: Feature Logic & Components
- Migrate feature APIs và composables.
- Migrate toàn bộ Vue components sang `<script setup lang="ts">`.

## Tasks

### Wave 1: Migration

#### [29-01-01] Environment Setup
<read_first>
- frontend_v2/package.json
- frontend_v2/vite.config.js
</read_first>
<action>
1. Cài đặt dependencies: `typescript`, `vue-tsc`, `@types/node`.
2. Tạo `tsconfig.json` với `strict: true`, `target: ES2020`, `module: ESNext`.
3. Đổi tên `vite.config.js` -> `vite.config.ts`.
4. Cập nhật `package.json` script: `"build": "vue-tsc --noEmit && vite build"`.
</action>
<acceptance_criteria>
- `package.json` có devDependencies TS.
- `tsconfig.json` tồn tại.
- `npm run build` gọi `vue-tsc`.
</acceptance_criteria>

#### [29-01-02] Core Files Migration
<read_first>
- frontend_v2/src/main.js
- frontend_v2/src/core/api.js
- frontend_v2/src/core/router/index.js
- frontend_v2/src/core/stores/settings.js
- frontend_v2/src/core/stores/system.js
</read_first>
<action>
1. Rename các file `.js` sang `.ts`.
2. Thêm type annotations cho Axios instance, Router routes, và Pinia stores.
3. Fix các lỗi type errors phát sinh trong core modules.
</action>
<acceptance_criteria>
- Tất cả file core đã được đổi tên thành `.ts`.
- Không còn lỗi type check trong các file này.
</acceptance_criteria>

#### [29-02-01] Feature API & Logic Migration
<read_first>
- frontend_v2/src/features/packing/api.js
- frontend_v2/src/features/packing/composables/useScanLogic.js
- frontend_v2/src/features/catalog/api.js
</read_first>
<action>
1. Rename tất cả `.js` trong features sang `.ts`.
2. Khai báo interfaces cho Customer, Product, Box, ScanItem.
3. Migrate `useScanLogic.ts` với đầy đủ type annotations cho refs và functions.
</action>
<acceptance_criteria>
- Toàn bộ feature logic là TypeScript.
- Type-safety cho các API calls (Promise<T>).
</acceptance_criteria>

#### [29-02-02] Vue Components Migration
<read_first>
- frontend_v2/src/views/PackingPage.vue
- frontend_v2/src/features/packing/components/ScannedList.vue
</read_first>
<action>
1. Thêm `lang="ts"` vào `<script setup>` của tất cả component `.vue`.
2. Chuyển `defineProps` sang generic syntax (e.g. `defineProps<{...}>`).
3. Import types/interfaces thay vì dùng primitive types khi có thể.
</action>
<acceptance_criteria>
- Tất cả component dùng `lang="ts"`.
- `vue-tsc --noEmit` pass sạch lỗi.
</acceptance_criteria>

## Verification Criteria
- [ ] Lệnh `npm run build` thành công.
- [ ] Lệnh `npx vue-tsc --noEmit` trả về 0 lỗi.
- [ ] Ứng dụng chạy bình thường trên trình duyệt (test flow quét hàng).

## must_haves
- **M-01**: Project phải build thành công với TypeScript.
- **M-02**: Không còn file `.js` nào trong thư mục `src/` (trừ phi có lý do đặc biệt).
- **M-03**: `strict: true` được bật trong `tsconfig.json`.
