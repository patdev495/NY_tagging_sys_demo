# Conventions

## Coding Standards
- **Python**: PEP 8 followed. Uses 4 spaces for indentation. Strict typing via `typing` module.
- **TypeScript**: 
  - Prefer `interface` for data shapes, `type` for unions/fixed sets.
  - Strict mode enabled in `tsconfig.json`.
  - Use PascalCase for components and camelCase for variables/functions.
- **Vue**: 
  - Composition API with `<script setup lang="ts">`.
  - Single Responsibility Principle for components.
- **CSS**: 
  - Tailwind CSS 4 utility-first approach.
  - Custom styles in `index.css` using `@theme` and `@utility` layers.

## Naming Conventions
- **Files**: 
  - Python: `snake_case.py`
  - TypeScript: `camelCase.ts`
  - Vue: `PascalCase.vue`
- **Database**: PascalCase for table names (e.g., `Products`, `Cartons`).

## Architecture Patterns
- **Feature-Sliced Design (FSD-lite)**: Code is organized by feature rather than layer to improve maintainability.
- **Thin Views**: Logic moved to composables (frontend) or services (backend).
- **Graceful Error Handling**: Global exception handlers on both ends (FastAPI + Axios interceptors).

## UI/UX Patterns
- **Responsiveness**: Mobile-first grid/flex layouts via Tailwind.
- **Efficiency**: Auto-focus on scan inputs, multi-line bulk scan support.
- **Feedback**: Toast notifications and clear visual states (loading, error, success).
