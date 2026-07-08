from fastapi import APIRouter

router = APIRouter(
    prefix="/api/secrets",
    tags=["Secrets"],
)
