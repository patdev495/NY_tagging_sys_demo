# Phase 28: Convert all CSS to Tailwind CSS - Research

## Current State Analysis

- **Framework**: Vue 3 + Vite.
- **Current CSS Architecture**:
  - `index.css`: A custom utility-first CSS file (approx. 276 lines) that mimics Tailwind naming conventions (e.g., `.flex`, `.p-4`, `.bg-indigo-600`).
  - `style.css`: Base styles and some component-specific styles (approx. 297 lines).
  - **Scoped Styles**: Most Vue components use `<style scoped>` with a mix of flexbox, grid, and hardcoded colors/spacing.
- **Icons**: FontAwesome is used via CDN/classes.

## Tailwind CSS Integration Strategy

### 1. Dependencies
Install the following packages:
```bash
npm install -D tailwindcss postcss autoprefixer
```

### 2. Configuration
Initialize Tailwind:
```bash
npx tailwindcss init -p
```
Configure `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Map existing custom colors if they don't match default Tailwind exactly
        // Based on index.css, most match Tailwind palette (indigo, slate, etc.)
      },
    },
  },
  plugins: [],
}
```

### 3. CSS Entry Point
Update `src/index.css` to use Tailwind directives and remove redundant custom utilities:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Keep custom @keyframes or complex animations that are hard to do in pure Tailwind */
```

## Migration Plan

1. **Infrastructure**: Install and configure Tailwind.
2. **Global Cleanup**: 
   - Identify all classes in `index.css` and verify their Tailwind equivalents.
   - Most classes like `.flex`, `.justify-between`, `.p-4` are 1:1 matches.
   - Some custom classes like `.glass-card` or `.btn-icon` should be moved to `@layer components` or converted to utility strings in components.
3. **Component Migration**:
   - Start with core components: `AppHeader`, `Sidebar`, `Notification`.
   - Move to feature components: `CatalogSelection`, `SessionHeader`, `ScanBuffer`, `ScannedList`.
   - Finally, update view pages: `PackingPage`, `SNLookupPage`, `LoginPage`, `DashboardPage`.
4. **Validation**:
   - Focus on responsive breakpoints (sm, md, lg, xl).
   - Verify dark mode support (if applicable, `style.css` has some dark mode logic).

## Potential Risks & Mitigations

- **Risk**: Breaking complex layouts (e.g., the `wide-layout` in `PackingPage`).
- **Mitigation**: Use a side-by-side comparison during migration and verify against the current "Responsive" phase (Phase 27) requirements.
- **Risk**: Missing custom animations or transitions.
- **Mitigation**: Preserve specific `@keyframes` in `index.css` and use Tailwind's `animate-` or arbitrary values.

## Validation Architecture
- **Visual Check**: Manual verification of all pages on 1920x1080 (Desktop), 1366x768 (Laptop), and 375x667 (Mobile).
- **Build Check**: Ensure `npm run build` generates a minified CSS bundle without errors.
