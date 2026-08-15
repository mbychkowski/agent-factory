# Multi-stage build for minimal image size and fast layer caching
FROM python:3.12-slim AS builder

WORKDIR /build

# 1. Install modern package manager
RUN pip install --no-cache-dir uv==0.8.13

# 2. Cache dependency installation layer
COPY pyproject.toml README.md ./
RUN uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --no-cache --target=/install -r requirements.txt

# --- Final Production Image ---
FROM python:3.12-slim AS runner

# Create non-root user for security compliance
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy dependencies and application source
COPY --from=builder /install /usr/local/lib/python3.12/site-packages/
COPY . /app/surface_gateway

# Environment configuration
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=8080

USER appuser

EXPOSE 8080

CMD ["uvicorn", "surface_gateway.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips=*"]
