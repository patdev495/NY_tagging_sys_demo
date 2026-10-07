# Phase 25: Database Schema Auto-Initialization - Plan

**Goal**: Ensure that all database tables are automatically created on backend startup.
**Phase**: 25
**Slug**: database-schema-auto-initialization

<files_modified>
- backend_v2/src/core/database.py
- backend_v2/main.py
</files_modified>

<threat_model>
- **Threat**: Database connection failure if DB doesn't exist.
  - **Mitigation**: Add try-except block and clear logging during initialization.
- **Threat**: Data loss during `create_all`.
  - **Mitigation**: SQLAlchemy's `create_all` is idempotent and does not drop existing tables or data.
</threat_model>

<plans>

## Wave 1: Implementation

### Task 1: Create Database Initialization Function
**Action**: Add `init_db` function to `src/core/database.py` that imports all models and calls `Base.metadata.create_all(bind=engine)`.
**Read First**:
- `backend_v2/src/core/database.py`
- `backend_v2/src/core/models.py`
**Acceptance Criteria**:
- `backend_v2/src/core/database.py` contains `from src.core import models`.
- `backend_v2/src/core/database.py` contains `def init_db():`.
- `init_db()` calls `models.Base.metadata.create_all(bind=engine)`.

### Task 2: Call Initialization on Startup
**Action**: Update `main.py` to call `init_db()` during the FastAPI startup event.
**Read First**:
- `backend_v2/main.py`
- `backend_v2/src/core/database.py`
**Acceptance Criteria**:
- `backend_v2/main.py` imports `init_db` from `src.core.database`.
- `backend_v2/main.py` calls `init_db()` inside the `@app.on_event("startup")` handler.

</plans>

<verification>
## Verification Criteria
1. Backend starts up without errors when the database exists but is empty.
2. All tables (`customers`, `products`, `cartons`, `carton_items`) are created in the database.
3. Subsequent restarts do not error or affect existing data.
</verification>

<must_haves>
- [ ] Tables are created automatically on first run.
- [ ] No data loss on subsequent runs.
- [ ] Clear error logging if DB connection fails.
</must_haves>
