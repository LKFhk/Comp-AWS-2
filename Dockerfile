# Multi-stage Dockerfile for riskintel360 Platform

# Base stage with common dependencies
FROM python:3.13.7-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install system dependencies for ML and fintech processing
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    pkg-config \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY infrastructure/requirements.txt infrastructure/
COPY requirements-ml.txt .

# Install Python dependencies including ML libraries
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r infrastructure/requirements.txt && \
    pip install --no-cache-dir -r requirements-ml.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    flake8 \
    mypy \
    pre-commit

# Copy source code
COPY . .

# Install the package in development mode
RUN pip install --no-cache-dir -e .

# Set development environment
ENV ENVIRONMENT=development
ENV DEBUG=true
ENV API_RELOAD=true
ENV LOG_LEVEL=DEBUG

# Expose port
EXPOSE 8000

# Health check for development
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command with hot-reload
CMD ["uvicorn", "riskintel360.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Create non-root user
RUN groupadd -r riskintel360 && useradd -r -g riskintel360 riskintel360

# Copy source code
COPY . .

# Install the package
RUN pip install --no-cache-dir .

# Change ownership to non-root user
RUN chown -R riskintel360:riskintel360 /app

# Switch to non-root user
USER riskintel360

# Set production environment
ENV ENVIRONMENT=production
ENV DEBUG=false
ENV API_RELOAD=false
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check for production
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uvicorn", "riskintel360.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
