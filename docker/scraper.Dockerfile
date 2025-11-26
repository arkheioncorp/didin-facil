# ============================================================================
# TikTrend Finder - Scraper Worker Dockerfile
# ============================================================================
# Python scraper with Playwright for browser automation
# Build: docker build -f docker/scraper.Dockerfile -t tiktrend-scraper .
# ============================================================================

# Use Playwright base image (includes browsers)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd --gid 1001 tiktrend \
    && useradd --uid 1001 --gid tiktrend --shell /bin/bash --create-home tiktrend

# Set working directory
WORKDIR /app

# ============================================================================
# Stage 2: Dependencies
# ============================================================================
FROM base as dependencies

# Copy requirements first for better caching
COPY backend/requirements-scraper.txt ./requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ============================================================================
# Stage 3: Development image
# ============================================================================
FROM dependencies as development

# Install development dependencies
RUN pip install \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    mypy

# Copy application code
COPY --chown=tiktrend:tiktrend backend/scraper /app/scraper
COPY --chown=tiktrend:tiktrend backend/shared /app/shared

# Create cache directory
RUN mkdir -p /app/.cache && chown -R tiktrend:tiktrend /app/.cache

# Switch to non-root user
USER tiktrend

# Run worker in development mode
CMD ["python", "-m", "scraper.main", "--mode", "development"]

# ============================================================================
# Stage 4: Production image
# ============================================================================
FROM dependencies as production

# Copy application code
COPY --chown=tiktrend:tiktrend backend/scraper /app/scraper
COPY --chown=tiktrend:tiktrend backend/shared /app/shared

# Create cache directory
RUN mkdir -p /app/.cache && chown -R tiktrend:tiktrend /app/.cache

# Switch to non-root user
USER tiktrend

# Run worker in production mode
CMD ["python", "-m", "scraper.main", "--mode", "production"]
