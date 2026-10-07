# Phase 29: Migrate frontend to TypeScript - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 29-migrate-frontend-to-typescript-for-better-maintainability
**Areas discussed:** Migration Strategy, TypeScript Config, Vue SFC Script Setup, Type Definitions

---

## Migration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Big-bang (toàn bộ) | Chuyển đổi tất cả 30 files trong 1 phase | ✓ |
| Incremental (từng bước) | Chuyển từng module, dùng allowJs | |

**User's choice:** Để agent quyết định (best for maintain & scale)
**Agent's rationale:** Với 30 files, big-bang tránh mixed JS/TS confusion và không cần maintain `allowJs: true` lâu dài.

---

## TypeScript Config

| Option | Description | Selected |
|--------|-------------|----------|
| strict: true từ đầu | Bật toàn bộ strict checks ngay | ✓ |
| Nới lỏng dần | Bắt đầu loose, tăng dần strictness | |

**User's choice:** Để agent quyết định (best for maintain & scale)
**Agent's rationale:** strict mode từ đầu catches bugs early, tránh technical debt khi phải tighten later.

---

## Vue SFC Script Setup

| Option | Description | Selected |
|--------|-------------|----------|
| `<script setup lang="ts">` | Modern syntax, ít boilerplate | ✓ |
| `defineComponent()` | Classic syntax, verbose hơn | |

**User's choice:** Để agent quyết định (best for maintain & scale)
**Agent's rationale:** `<script setup>` là recommended approach của Vue 3, type inference tốt hơn.

---

## Type Definitions

| Option | Description | Selected |
|--------|-------------|----------|
| Centralized per feature + shared | `src/types/` + `features/*/types.ts` | ✓ |
| Single global types folder | Tất cả types trong `src/types/` | |
| Inline only | Types chỉ define trong file sử dụng | |

**User's choice:** Để agent quyết định (best for maintain & scale)
**Agent's rationale:** Centralized per feature giữ types gần code sử dụng, shared types cho common interfaces.

---

## Agent's Discretion

- Thứ tự migrate files
- Chi tiết type annotations
- interface vs type cho từng trường hợp cụ thể

## Deferred Ideas

None
