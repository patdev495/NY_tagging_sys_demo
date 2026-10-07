# Phase 21: Admin UI Shell & Navigation - Research

## Objective
Research the technical approach for implementing a unified navigation system for the NY Tagging System, supporting both the high-focus Packing Station and the data-intensive Admin Dashboard.

## Key Questions
1. **Navigation Structure**: How to provide access to Admin without distracting the packer?
2. **Vue Router Integration**: How to migrate the current component-based entry to a router-based one?
3. **Layout & Aesthetics**: How to design a premium Sidebar using Vanilla CSS?

## Findings

### 1. Navigation & Routing
- Use `vue-router` for clean URL-based navigation.
- Routes:
    - `/`: `PackingPage.vue` (Existing)
    - `/admin`: `AdminDashboardPage.vue` (New)
    - `/admin/customers`: (Future)
    - `/admin/products`: (Future)
- **Switching**: Add a subtle toggle or a Sidebar that can be collapsed to maximize screen space for packers.

### 2. Layout Architecture
- **Main Layout**: A flexible container with:
    - `Sidebar`: Left side, collapsible, containing links to Home (Packing), Customers, Products, Reports, Settings.
    - `Main Content`: Right side, where pages are rendered via `<router-view>`.
- **Aesthetics**:
    - Sidebar: Dark theme with glassmorphism (backdrop-filter: blur).
    - Icons: Use `lucide-vue-next` (already in package.json).
    - Transitions: Use `<transition>` for smooth page changes.

### 3. Dependencies
- Need to install `vue-router@4`.
- No other new dependencies needed for this phase.

## Technical Approach
1. Install `vue-router`.
2. Create `src/core/router/index.js` for routing config.
3. Create `src/core/layouts/MainLayout.vue` to host the Sidebar and `<router-view>`.
4. Refactor `App.vue` to use `MainLayout`.
5. Create a placeholder `AdminDashboardPage.vue` in `src/views/admin/`.

## Validation Architecture
- Verify `npm install` for vue-router.
- Verify routing navigation between `/` and `/admin`.
- Verify Sidebar collapse/expand functionality.
- Verify UI responsiveness.
