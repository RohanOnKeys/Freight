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

    Creates and configures the Freight FastAPI application.
    """

    app = FastAPI(
        title="Freight CI/CD API",
        description="Distributed CI/CD server built with FastAPI.",
        version="0.1.0",
    )

    # Health check
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok"}

    # Register routers
    app.include_router(webhooks.router)
    app.include_router(pipelines.router)
    app.include_router(jobs.router)
    app.include_router(runners.router)
    app.include_router(artifacts.router)
    app.include_router(secrets.router)

    return app


app = create_app()