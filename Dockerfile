# Multi-stage build: Cold path (Python) + Hot path (Rust)
FROM python:3.11-slim as schema-builder

# Install Poetry and Python dependencies
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Copy cold path and export schemas
COPY cold_path ./cold_path
RUN poetry run python -m cold_path.cli export-schemas

FROM rust:1.75 as rust-builder

WORKDIR /app
COPY hot_path/Cargo.toml hot_path/Cargo.lock ./
COPY hot_path/src ./src
COPY hot_path/build.rs ./
COPY --from=schema-builder /app/assets ./assets

# Build the Rust hot path service with generated schemas
RUN cargo build --release

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy Poetry files and install Python dependencies (cold path only)
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy Python cold path code
COPY cold_path ./cold_path

# Copy Rust binary from builder stage
COPY --from=rust-builder /app/target/release/familiar-pattern-classifier /usr/local/bin/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run the Rust hot path service
CMD ["familiar-pattern-classifier"] 