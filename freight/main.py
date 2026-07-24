"""
Freight FastAPI application entrypoint.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from freight.core.heartbeat_monitor import monitor_runners
from freight.core.retry import monitor_retries
from freight.routers import (
    artifacts,
    jobs,
    pipelines,
    runners,
    secrets,
    webhooks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown.

    Starts the heartbeat monitor and the retry monitor as background
    tasks when the API launches, and gracefully stops both during
    shutdown.
    """
    heartbeat_task = asyncio.create_task(
        monitor_runners()
    )

    retry_task = asyncio.create_task(
        monitor_retries()
    )

    try:
        yield

    finally:
        heartbeat_task.cancel()
        retry_task.cancel()

        for task in (heartbeat_task, retry_task):
            try:
                await task
            except asyncio.CancelledError:
                pass


def create_app() -> FastAPI:
    """Create and configure the Freight API."""

    app = FastAPI(
        title="Freight CI/CD API",
        description="Distributed CI/CD server built with FastAPI.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["Health"])
    async def health():
        """Health check endpoint."""
        return {"status": "ok"}

    app.include_router(webhooks.router)
    app.include_router(pipelines.router)
    app.include_router(jobs.router)
    app.include_router(runners.router)
    app.include_router(artifacts.router)
    app.include_router(secrets.router)

    return app


app = create_app()