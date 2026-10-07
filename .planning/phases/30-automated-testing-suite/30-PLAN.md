# PLAN - Phase 30: Automated Testing Suite Implementation

## Objective
Establish a robust automated testing foundation to prevent regressions in core business logic, specifically focusing on Serial Number (S/N) generation, BTXML mapping, and scan validation logic.

## User Acceptance Criteria (UAT)
1. [ ] **Backend Test Suite**: `uv run pytest` executes and passes for core services.
2. [ ] **Frontend Test Suite**: `npm run test` executes and passes for core logic.
3. [ ] **BTXML Verification**: Tests confirm correct XML generation for both standard and detailed templates.
4. [ ] **Scan Validation Verification**: Tests confirm that duplicate scans and invalid patterns are blocked in the frontend.
5. [ ] **Documentation**: A `TESTING.md` file (or updated codebase/TESTING.md) explaining how to run and add tests.

## Proposed Changes

### 1. Backend Infrastructure (`backend_v2/`)
- Add `pytest`, `pytest-asyncio`, and `pytest-mock` to dev dependencies.
- Create `backend_v2/tests/` directory.
- Configure `conftest.py` for FastAPI app and DB session mocking (using SQLite in-memory for testing).

### 2. Frontend Infrastructure (`frontend_v2/`)
- Add `vitest`, `@vue/test-utils`, and `jsdom` to dev dependencies.
- Configure `vitest.config.ts`.
- Update `package.json` with a `test` script.

### 3. Core Logic Tests
- **Backend (`PrintService`)**:
  - Test `generate_btxml` with "standard" template.
  - Test `generate_btxml` with "detailed" template (verifying SN_1 to SN_30).
  - Test `reprint_carton` correctly clones items and flags as reprint.
- **Frontend (`PackingPage`)**:
  - Test `processSingleScan` for valid/invalid/duplicate scans.
  - Test bulk scan splitting logic.
  - Test S/N preview generation.

## Implementation Steps

### Step 1: Backend Setup
- Run `uv init` (if not done) or update `pyproject.toml`.
- Install dependencies: `uv add --dev pytest pytest-asyncio pytest-mock`.
- Create `tests/conftest.py` and a simple `tests/test_print_service.py`.

### Step 2: Backend Logic Implementation
- Implement unit tests for `PrintService.generate_btxml`.
- Implement integration tests for `Reprint` using an in-memory DB.

### Step 3: Frontend Setup
- Install dependencies: `npm install -D vitest @vue/test-utils jsdom`.
- Setup `vite.config.ts` integration or separate `vitest.config.ts`.

### Step 4: Frontend Logic Implementation
- Refactor `PackingPage.vue` logic into a composable `usePackingSession.ts` if needed for easier testing (recommended).
- Implement tests for scan processing and S/N generation.

## Risk Assessment
- **Risk**: Database tests might fail due to MSSQL specific syntax in models.
- **Mitigation**: Use `sqlite` for simple unit tests and mock complex DB operations.
- **Risk**: BarTender templates are not available during testing.
- **Mitigation**: Use dummy XML templates in the `tests/` directory to verify string formatting.
