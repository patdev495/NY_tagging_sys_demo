# Testing Guide

## Automated All-in-One Test
You can run all tests (Backend + Frontend) using the automated script in the root directory:
```bash
.\run_tests.bat
```

## Backend (Pytest)

```bash
cd backend_v2
uv run pytest
```

### Test files
- `tests/test_health.py` — API health check endpoint
- `tests/test_print_service.py` — BTXML generation, SN grid, origin text logic

### Adding new tests
1. Create `tests/test_<module>.py`
2. Use `pytest-mock` for mocking DB sessions
3. Use `pytest-asyncio` for async endpoint tests

## Frontend (Vitest)

```bash
cd frontend_v2
npm run test        # single run
npm run test:watch  # watch mode
```

### Test files
- `src/features/packing/__tests__/scanLogic.spec.ts` — scan validation, bulk splitting, SN preview

### Adding new tests
1. Create `__tests__/<name>.spec.ts` next to the module being tested
2. For pure logic: import and test directly
3. For Vue components: use `@vue/test-utils` with `mount()`

## Architecture
- **Backend**: `pytest.ini` sets `pythonpath = .` so imports work from project root
- **Frontend**: `vitest.config.ts` uses `pool: 'threads'` (required for Windows) and `jsdom` environment
- **Extractable logic**: Core validation lives in `src/features/packing/utils/scanLogic.ts` for easy testing without component overhead
