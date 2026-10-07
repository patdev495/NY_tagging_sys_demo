# Phase 11 Research: Backend Scaffold & Read-Only Features

## 1. Existing System Analysis
- **Current Structure:** All backend logic resides in `backend/main.py`. It uses FastAPI with a single `api_router`.
- **Database Connection:** Driven by `database.py`. Endpoints use `Depends(database.get_db)`.
- **Data Models:** Defined in `models.py` (SQLAlchemy).
- **Data Schemas:** Defined in `schemas.py` (Pydantic).
- **Static Files:** `main.py` also mounts and serves the Vue frontend (`/assets` and index fallback).
- **Target Endpoints for Phase 11:**
  - `GET /api/customers`
  - `GET /api/customers/{customer_id}/products`
  - `GET /api/cartons/search?carton_sn=...`
  - `GET /api/health`

## 2. Technical Approach & V2 Structure

Per the constraints in `11-CONTEXT.md`, we must NOT touch the existing `backend` folder. We must create `backend_v2` and copy/adapt the code there.

**Proposed Directory Structure (`backend_v2/`):**
```text
backend_v2/
├── src/
│   ├── core/
│   │   ├── config.py         # App settings & env
│   │   ├── database.py       # Session management (copied from old)
│   │   ├── exceptions.py     # Global error handler
│   │   └── models.py         # SQLAlchemy models (copied from old to maintain DB schema)
│   ├── features/
│   │   ├── customer/
│   │   │   ├── router.py     # /api/customers endpoints
│   │   │   ├── service.py    # DB logic
│   │   │   └── schemas.py    # Customer Pydantic models
│   │   ├── product/
│   │   │   ├── router.py     # /api/customers/{id}/products
│   │   │   ├── service.py    
│   │   │   └── schemas.py    
│   │   └── history/
│   │       ├── router.py     # /api/cartons/search
│   │       ├── service.py    
│   │       └── schemas.py    
│   └── main.py               # create_app() factory
├── pyproject.toml / requirements.txt
```

## 3. Implementation Details

- **App Factory (`create_app`):** The new `main.py` should implement `def create_app() -> FastAPI`.
- **Global Error Handling:** Implement a custom exception handler in `src/core/exceptions.py` that formats exceptions into a standard JSON payload.
- **Service Layer Pattern:** 
  - The router will inject the DB session: `def get_customers(db: Session = Depends(get_db))`.
  - It will immediately pass it to the service: `return customer_service.get_all_customers(db)`.
- **Schema Extraction:** We need to carefully copy only the relevant Pydantic models from the old `schemas.py` into the respective feature folders. E.g., `Customer` schema goes to `customer/schemas.py`. Note that some schemas reference each other (e.g., `Carton` references `Product` and `CartonItem`). Since this phase only deals with Read-Only features, we should start segregating them without breaking circular dependencies. For shared base models, we can keep them in the feature where they belong, or temporarily in `core/schemas.py` if shared extensively.

## 4. Risks & Dependencies
- **Risk:** Copying `models.py` into `backend_v2/src/core/models.py`. If we change it, the DB will break. It must be an exact copy.
- **Risk:** Serving the static frontend. The old `main.py` handles serving `../frontend/dist`. For `backend_v2`, we need to make sure this logic is either removed (if we use a dev server for frontend during development) or updated to point to `frontend_v2/dist`.
- **Dependency:** The `database.py` requires connection strings (often hardcoded or using `.env`). We must ensure `backend_v2` runs properly on the local environment without clashing ports with the old backend. We should configure `backend_v2` to run on port `8001` or another port during development to allow side-by-side comparison.
