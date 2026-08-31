from fastapi import APIRouter, Request

from app.services import clerk_email_webhook_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def receive_clerk_webhook(request: Request) -> dict[str, object]:
    payload = await request.body()
    event = clerk_email_webhook_service.verify_clerk_webhook(
        payload=payload,
        headers=request.headers,
    )
    return clerk_email_webhook_service.handle_clerk_webhook(event)
