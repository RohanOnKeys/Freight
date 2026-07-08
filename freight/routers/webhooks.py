from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/webhooks",
    tags=["Webhooks"],
)


class WebhookPayload(BaseModel):
    ref: str
    repository: dict


@router.post("/")
async def receive_webhook(payload: WebhookPayload):
    return {
        "message": "Webhook received",
        "payload": payload.model_dump(),
    }