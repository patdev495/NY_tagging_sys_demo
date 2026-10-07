# Phase 31: Deploy to Render (Unified Service) - Research

## Technical Approach

### 1. Unified FastAPI + Vue 3 Architecture
- **Structure**: 
    - `backend_v2/`
        - `static/` (Chứa frontend dist)
        - `main.py`
- **FastAPI Configuration**:
    ```python
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # API Routes first
    app.include_router(...)

    # Static files mount
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse("static/index.html")
    ```

### 2. Multi-stage Dockerfile for Render
We need to combine Node.js and Python.
```dockerfile
# Stage 1: Build Frontend
FROM node:18-slim as frontend-builder
WORKDIR /frontend
COPY frontend_v2/package*.json ./
RUN npm install
COPY frontend_v2/ ./
RUN npm run build

# Stage 2: Build Backend & Final Image
FROM python:3.10-slim-bullseye
WORKDIR /app
# Install system deps for MSSQL/SQLite
RUN apt-get update && apt-get install -y curl gnupg2 unixodbc ...
# Copy Backend
COPY backend_v2/requirements.txt .
RUN pip install -r requirements.txt
COPY backend_v2/ .
# Copy Frontend build to backend static
COPY --from=frontend-builder /frontend/dist ./static
# Environment variables
ENV PORT=8001
EXPOSE $PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. SQLite Database Handling
- Since the user wants "existing data", the `database.db` must be copied into the Docker image.
- Render Free Tier doesn't persist disk changes. Each deploy/restart will revert `database.db` to the version in the image. This matches the user's "Get all current data up" requirement for a demo.

### 4. Port Configuration
- Render passes a `PORT` environment variable. The app must listen on that port.

## Validation Architecture

### Verification Strategy
1. **Local Docker Test**: Build and run the unified image locally to ensure frontend is served correctly.
2. **API Health Check**: Ensure `/api/v1/health` returns OK.
3. **Frontend Asset Check**: Ensure `/` returns `index.html` and assets (js/css) load without 404.
4. **Database Check**: Verify `/api/v1/customers` (or similar) returns data from the existing `database.db`.

## Potential Risks
- **Image Size**: Render Free Tier has limits on image size and build time. Using slim images is crucial.
- **MSSQL Dependencies**: The current Dockerfile has heavy MSSQL drivers. If Render only needs SQLite for the demo, we could potentially simplify, but keeping them ensures the app still works as intended.
- **SPA Routing**: Catch-all route in FastAPI must not interfere with `/api/v1` routes.

---
*Research complete: 2026-05-14*
