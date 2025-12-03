# ============================================================================
# TikTrend Finder - API Dockerfile
# ============================================================================
# FastAPI backend service
# Build: docker build -f docker/api.Dockerfile -t tiktrend-api .
# ============================================================================

# Stage 1: Builder (Build dependencies)
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Development (for local development with hot reload)
FROM python:3.11-slim AS development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code (will be overwritten by volume mount)
COPY backend/ /app/

# Expose port
EXPOSE 8000

# Run development server with hot reload
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Stage 3: Runtime (Final production image)
FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 tiktrend \
    && useradd --uid 1000 --gid tiktrend --shell /bin/bash --create-home tiktrend

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=tiktrend:tiktrend backend/api /app/api
COPY --chown=tiktrend:tiktrend backend/modules /app/modules
COPY --chown=tiktrend:tiktrend backend/shared /app/shared
COPY --chown=tiktrend:tiktrend backend/alembic /app/alembic
COPY --chown=tiktrend:tiktrend backend/alembic.ini /app/alembic.ini

# Switch to non-root user
USER tiktrend

# Expose port (Railway uses $PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Default command (Railway overrides this via railway.toml)
CMD ["gunicorn", "api.main:app", \
    "--workers", "2", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--capture-output", \
    "--enable-stdio-inheritance"]

