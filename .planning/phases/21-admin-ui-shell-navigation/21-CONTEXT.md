# Phase 21: Admin UI Shell & Navigation - Context

**Gathered:** 2026-04-24
**Status:** Planning

<domain>
## Phase Boundary
This phase establishes the foundational UI architecture for the Admin Dashboard. It transitions the application from a single-page tool into a multi-page management system.

**Deliverables:**
- Vue Router integration.
- Sidebar component with collapse/expand state.
- Main Layout for consistent navigation.
- Initial Admin Dashboard page (shell).
</domain>

<decisions>
## Implementation Decisions

### Navigation (Sidebar)
- **Position**: Fixed left.
- **State**: Persistent state (collapsed/expanded) stored in `useSettingsStore` or local state.
- **Design**: 
    - Dark mode by default for the Sidebar.
    - Blur effect (glassmorphism).
    - Subtle active indicators for current route.
    - Icons from Lucide.

### Routing
- **Base path**: `/` points to the Packing Station.
- **Admin path**: `/admin` is the entry for all management features.
- **History mode**: Use Web History (clean URLs).

### UI/UX
- **Transitions**: Slide-fade transition between pages.
- **Responsive**: Sidebar hides on mobile (mobile menu toggle).
</decisions>

<canonical_refs>
## Canonical References
- `frontend_v2/src/App.vue` — Main entry point.
- `frontend_v2/src/views/PackingPage.vue` — Existing packing logic.
- `frontend_v2/package.json` — Dependency management.
</canonical_refs>

<specifics>
## Specific Ideas
- Sidebar should include a "System Health" indicator (Agent status) similar to the current header.
- The switch to Admin should feel "premium" — perhaps a slight zoom-out or fade effect.
</specifics>
