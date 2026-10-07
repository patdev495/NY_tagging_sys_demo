# Project Structure

## Root Directory
- `backend_v2/`: Modular FastAPI backend.
- `frontend_v2/`: Vue 3 + TypeScript + Tailwind frontend.
- `print_agent_v2/`: Python-based print agent for local label triggering.
- `.planning/`: GSD workflow state and codebase mapping.
- `temp_pdf/`: Temporary storage for generated PDF files.
- `release/`: Production build artifacts and executables.

## Backend Layout (`backend_v2/`)
- `main.py`: Entry point and app factory.
- `src/core/`: Configuration, database setup, and shared utilities.
- `src/features/`: Feature-sliced modules (Customer, Product, History, Box, Print).
  - `router.py`: API endpoints for the feature.
  - `service.py`: Business logic.
  - `models.py`: SQLAlchemy models.
  - `schemas.py`: Pydantic validation schemas.
- `requirements.txt`: Python dependencies.

## Frontend Layout (`frontend_v2/src/`)
- `main.ts`: Entry point.
- `App.vue`: Root component.
- `core/`: Global components, API clients, and stores (Pinia).
- `features/`: Feature-sliced UI logic (Packing, Catalog, History, Settings).
  - `components/`: Feature-specific components.
  - `api.ts`: Feature-specific API calls.
  - `composables/`: Reusable logic (e.g., `useScanLogic`).
- `views/`: Main page components.
- `types/`: Global TypeScript interfaces.
- `i18n/`: Internationalization files (EN, VI).

## Print Agent Layout (`print_agent_v2/`)
- `agent.py`: Core logic for receiving BTXML and automating BarTender.
- `NY_Print_Agent.spec`: PyInstaller specification for building the EXE.
