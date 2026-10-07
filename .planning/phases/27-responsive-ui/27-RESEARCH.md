# Phase 27: Responsive UI - Research

<domain>
## Phase Boundary
Fix responsive layout issues on PackingPage and its subcomponents (SessionHeader, ScannedList, ScanBuffer) across PC, Laptop, and Mobile resolutions.
</domain>

## Current Issues
1. **No Flex Wrap in SessionHeader**: The `.session-info` and `.header-inputs` containers use `display: flex` without `flex-wrap: wrap`. On screens smaller than 1550px (like 1366px or 1280px laptops), the product name and the inputs (Job Order, Origin, SN, Date) are forced onto a single line, causing them to squish and overlap.
2. **ScannedList Sidebar Breakpoint**: The `ScannedList` sidebar has a fixed width of `380px` and only stacks vertically below `1100px`. However, `PackingPage` stacks them vertically at `1000px`. This mismatch causes layout breaking between 1000px and 1100px.
3. **Hardcoded Input Widths**: Some inputs (`sn-input` 160px, `date-input` 90px) cause the `header-inputs` to overflow if there is no wrap.

## Architectural Tradeoffs
- **Option A (Wrap Inputs)**: Add `flex-wrap: wrap` to `.header-inputs` and `.session-info`. This is the least invasive and allows items to naturally flow to the next line on laptops.
- **Option B (Stack Earlier)**: Change the breakpoint from `1000px` to `1280px` for stacking the workspace vertically.

**Decision**: Combine both. Add `flex-wrap: wrap` to `.session-info` and `.header-inputs` so they wrap gracefully on medium screens, and align the `PackingPage` and `ScannedList` breakpoints to stack at `1200px` for consistent mobile/tablet viewing.

## Validation Architecture
- Verify that `.session-info` has `flex-wrap: wrap`.
- Verify `.header-inputs` has `flex-wrap: wrap`.
- Ensure breakpoints in `PackingPage.vue` and `ScannedList.vue` match (e.g., both use `1200px` for vertical stacking).
