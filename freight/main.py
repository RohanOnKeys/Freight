from fastapi import FastAPI

from freight.routers import (
    artifacts,
    jobs,
    pipelines,
    runners,
    secrets,
    webhooks,
)


def create_app() -> FastAPI:
    """
    Application factory.

    Creates and configures the Freight FastAPI application,
    registers all API routers, and exposes the health endpoint.
    """

    app = FastAPI(
        title="Freight CI/CD API",
        description="Distributed CI/CD server built with FastAPI.",
        version="0.1.0",
    )

    @app.get("/health", tags=["Health"])
    async def health():
        """
        Health check endpoint.

        Returns the operational status of the Freight API server.
        """
        return {"status": "ok"}

    # Register API routers.

    # GitHub webhook endpoints.
    app.include_router(webhooks.router)

    # Pipeline management and status endpoints.
    app.include_router(pipelines.router)

    # Job lifecycle endpoints.
    app.include_router(jobs.router)

    # Runner registration and heartbeat endpoints.
    app.include_router(runners.router)

    # Artifact upload and download endpoints.
    app.include_router(artifacts.router)

    # Secret management endpoints.
    app.include_router(secrets.router)

    return app


app = create_app()