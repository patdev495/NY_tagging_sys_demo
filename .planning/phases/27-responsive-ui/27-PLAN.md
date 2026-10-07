---
wave: 1
depends_on: []
files_modified:
  - frontend_v2/src/features/packing/components/SessionHeader.vue
  - frontend_v2/src/features/packing/components/ScannedList.vue
  - frontend_v2/src/views/PackingPage.vue
autonomous: true
---

# Phase 27: Responsive UI Implementation

## Goal
Implement responsive layout adjustments so the Packing Station works perfectly on all screen sizes, from large desktop monitors to laptops and smaller devices.

## Tasks

### 1. Enable CSS Flex Wrapping in SessionHeader
Modify `SessionHeader.vue` to allow the product details and inputs to wrap gracefully on smaller screens.
<read_first>
- frontend_v2/src/features/packing/components/SessionHeader.vue
</read_first>
<action>
Modify `frontend_v2/src/features/packing/components/SessionHeader.vue`:
1. In the `<style scoped>` section, find `.session-info` and add `flex-wrap: wrap;`
2. Find `.header-inputs` and add `flex-wrap: wrap;`
3. Update the media query `@media (max-width: 600px)` to `@media (max-width: 768px)` to apply mobile stacking slightly earlier.
</action>
<acceptance_criteria>
- `frontend_v2/src/features/packing/components/SessionHeader.vue` contains `flex-wrap: wrap;` in both `.session-info` and `.header-inputs` classes.
- Media query `@media (max-width: 768px)` is used instead of `600px` for `.session-info`.
</acceptance_criteria>

### 2. Synchronize Layout Breakpoints
Modify `PackingPage.vue` and `ScannedList.vue` to share a consistent breakpoint (1200px) for switching to a vertical layout, preventing the sidebar from overlapping the main workspace on laptops.
<read_first>
- frontend_v2/src/views/PackingPage.vue
- frontend_v2/src/features/packing/components/ScannedList.vue
</read_first>
<action>
Modify `frontend_v2/src/views/PackingPage.vue`:
1. Find `@media (max-width: 1000px)` and change it to `@media (max-width: 1200px)`.
2. Inside that media query, ensure `.packing-workspace { flex-direction: column; align-items: stretch; }` is preserved.

Modify `frontend_v2/src/features/packing/components/ScannedList.vue`:
1. Find `@media (max-width: 1100px)` and change it to `@media (max-width: 1200px)`.
2. Ensure `.scanned-sidebar { width: 100% !important; height: 450px !important; ... }` is preserved.
</action>
<acceptance_criteria>
- `frontend_v2/src/views/PackingPage.vue` contains `@media (max-width: 1200px)` instead of `1000px`.
- `frontend_v2/src/features/packing/components/ScannedList.vue` contains `@media (max-width: 1200px)` instead of `1100px`.
</acceptance_criteria>

## Verification
- UI elements wrap on laptop screens (1366px / 1280px) and do not overflow off-screen.
- Below 1200px, the ScannedList moves to the bottom of the workspace instead of squeezing the sides.
