from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from freight.db.session import get_db

router = APIRouter(
    prefix="/webhook",
    tags=["Webhooks"],
)


@router.post("/")
async def receive_webhook(db: Session = Depends(get_db)):
    """
    Receive a GitHub webhook.

    Database access is now available through `db`.
    """

    return {
        "message": "Database session acquired"
    }