"""Spec Engine Surface Gateway - Production Service Entry Point."""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from surface_gateway.app.routes.github import router as github_router
from surface_gateway.app.routes.health import router as health_router
from surface_gateway.app.routes.tasks import router as tasks_router

# Configure Structured Logging for Cloud Run / Container Environments
try:
    import google.cloud.logging

    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging()
    logger = logging.getLogger("gateway.main")
    logger.info("Initialized Google Cloud Structured Logging")
except Exception:  # noqa: BLE001
    logging.basicConfig(
        level=logging.INFO,
        format='{"time":"%(asctime)s", "level":"%(levelname)s", "logger":"%(name)s", "message":"%(message)s"}',
        stream=sys.stdout,
    )
    logger = logging.getLogger("gateway.main")
    logger.info("Initialized JSON console logging")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage lifecycle resources: connection pools and graceful shutdown."""
    logger.info("Initializing HTTP connection pool and Cloud clients...")
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=5.0),
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=200),
    )
    yield
    logger.info("Closing HTTP connection pool...")
    await app.state.http_client.aclose()


app = FastAPI(
    title="Spec Engine Surface Gateway",
    description="Webhook proxy for multi-agent spec deliberation workflows.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Security Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": "An error occurred."},
    )


# Mount routers with tags & dual-compatibility routes
app.include_router(health_router, tags=["Health"])
app.include_router(health_router, prefix="/healthz", tags=["Health"])
app.include_router(github_router, tags=["GitHub"])
app.include_router(github_router, prefix="/api/v1", tags=["GitHub"])
app.include_router(tasks_router, tags=["Tasks"])
app.include_router(tasks_router, prefix="/api/v1", tags=["Tasks"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
