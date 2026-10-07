# Stage 1: Build Frontend
FROM node:18-slim AS frontend-builder

WORKDIR /frontend
COPY frontend_v2/package*.json ./
RUN npm install
COPY frontend_v2/ ./
RUN npm run build

# Stage 2: Build Backend Stage
FROM python:3.10-slim-bullseye AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    gcc \
    g++ \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update

COPY backend_v2/requirements.txt .
# Build wheels to avoid needing compilers in the final image
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# Stage 3: Runtime stage
FROM python:3.10-slim-bullseye

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8001

# Install only runtime dependencies and Microsoft ODBC Driver 18
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    # Fix for older SQL Server TLS versions (unsupported protocol error)
    && sed -i 's/MinProtocol = TLSv1.2/MinProtocol = TLSv1.0/g' /etc/ssl/openssl.cnf \
    && sed -i 's/CipherString = DEFAULT@SECLEVEL=2/CipherString = DEFAULT@SECLEVEL=1/g' /etc/ssl/openssl.cnf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install them
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy backend files
COPY backend_v2/ .

# Copy frontend build from stage 1 to 'static' directory
COPY --from=frontend-builder /frontend/dist ./static

# Expose port (Render uses dynamic PORT)
EXPOSE $PORT

# Command to run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
