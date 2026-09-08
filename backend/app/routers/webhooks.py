from fastapi import APIRouter, Request

from app.services import clerk_email_webhook_service, email_delivery_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def receive_clerk_webhook(request: Request) -> dict[str, object]:
    payload = await request.body()
    event = clerk_email_webhook_service.verify_clerk_webhook(
        payload=payload,
        headers=request.headers,
    )
    return clerk_email_webhook_service.handle_clerk_webhook(event)


@router.post("/resend")
async def receive_resend_webhook(request: Request) -> dict[str, object]:
    payload = await request.body()
    event = email_delivery_service.verify_resend_webhook(
        payload=payload,
        headers=request.headers,
    )
    return email_delivery_service.handle_resend_webhook(
        event,
        provider_event_id=request.headers.get("svix-id"),
    )
