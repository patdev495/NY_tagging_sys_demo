# PLAN - Phase 27: Responsive UI Optimization

## Objective
Restore and optimize the responsive layout for all screen sizes (Desktop, Laptop, Mobile) following the TypeScript and Tailwind CSS 4 migration. Ensure high information density and usable interfaces on lower-resolution laptop displays (e.g., 1366x768).

## User Acceptance Criteria (UAT)
1. [ ] **Sidebar Persistence**: On laptop resolutions (>= 1024px), the `ScannedList` must appear as a sticky sidebar.
2. [ ] **Vertical Optimization**: On laptop screens, the main UI (headers + scan area) must fit within the viewport without excessive scrolling.
3. [ ] **Compact Headers**: `AppHeader` and `SessionHeader` must reduce padding and font sizes on screens smaller than 1440px.
4. [ ] **Grid Alignment**: Scan buffer buttons and inputs must align correctly across all breakpoints.
5. [ ] **Mobile View**: On mobile (< 768px), the UI should be a single column with full-width inputs and a scrollable scanned list below.

## Proposed Changes

### 1. Global Layout (`PackingPage.vue`)
- Change `xl:flex-row` to `lg:flex-row` to enable sidebar layout on standard laptops.
- Adjust `max-w-[1100px]` and `max-w-[1550px]` to be more fluid.
- Implement responsive padding for the main container.

### 2. Header Compaction (`AppHeader.vue`, `SessionHeader.vue`)
- Use Tailwind responsive classes (e.g., `lg:px-4 lg:py-1`) to reduce vertical space.
- Reduce font sizes for labels and titles on laptop screens.
- Ensure buttons (Audio, Emergency, Settings) don't wrap prematurely.

### 3. Sidebar Optimization (`ScannedList.vue`)
- Change `xl:w-[380px]` to `lg:w-[320px]` or `xl:w-[380px]`.
- Adjust sticky top offset for better alignment with the header.
- Use `h-[calc(100vh-160px)]` to prevent overflow issues on small height screens.

### 4. Component Refinement
- **ScanBuffer.vue**: Ensure the "Pack Now" and "Next Carton" buttons are visible and properly sized.
- **CatalogSelection.vue**: Optimize the search bar and product grid for smaller viewports.

## Implementation Steps

### Step 1: Research & Audit
- Identify exact breakpoints where the layout currently "breaks" or becomes unusable.
- Verify Tailwind 4 breakpoint behaviors.

### Step 2: Global Layout Adjustments
- Update `PackingPage.vue` container and flex classes.

### Step 3: Header Optimization
- Apply compact styles to `AppHeader.vue`.
- Apply compact styles to `SessionHeader.vue`.

### Step 4: Sidebar & Component Polish
- Update `ScannedList.vue` breakpoints and dimensions.
- Minor tweaks to `ScanBuffer.vue` and `CatalogSelection.vue`.

### Step 5: Verification
- Test on 1920x1080 (Desktop), 1366x768 (Laptop), and 375x812 (Mobile).
- Ensure "Pack Now" button is reachable without scrolling on 768px height.

## Risk Assessment
- **Risk**: Tailwind 4 might have different default breakpoints if not configured.
- **Mitigation**: Verify breakpoint values in `index.css` or use explicit values.
- **Risk**: Over-compaction might make the UI hard to use for operators with gloves/touchscreens.
- **Mitigation**: Maintain minimum touch target sizes (44x44px).
