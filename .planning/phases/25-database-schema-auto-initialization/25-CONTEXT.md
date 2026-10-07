# Phase 25: Database Schema Auto-Initialization - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary
This phase focuses on ensuring that the database tables are automatically created if they don't exist when the backend starts.
- User will create the database manually.
- Backend must initialize the schema (tables, relationships) automatically.
</domain>

<decisions>
## Implementation Decisions

### Schema Initialization
- Use SQLAlchemy's `Base.metadata.create_all(bind=engine)` to create tables.
- This should happen during the FastAPI startup event.
- All models must be imported before calling `create_all`.

### Error Handling
- If the database itself doesn't exist, the system should log a clear error (since the user will handle DB creation manually).
</decisions>

<canonical_refs>
## Canonical References
- `backend_v2/src/core/database.py` — Database engine and Base definition.
- `backend_v2/src/core/models.py` — SQLAlchemy models definition.
- `backend_v2/main.py` — FastAPI application and startup events.
</canonical_refs>

<specifics>
## Specific Ideas
- Add a function `init_db()` in `src/core/database.py` or a new file that performs the `create_all` call.
- Call this `init_db()` in `main.py` inside the `@app.on_event("startup")` handler or before `create_app` returns.
</specifics>

<deferred>
## Deferred Ideas
- Automatic Database creation (User requested to do this manually).
- Database migrations (Alembic) — stick to simple `create_all` for now as per current requirements.
</deferred>
