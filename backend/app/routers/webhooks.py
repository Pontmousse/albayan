from fastapi import APIRouter, Request

from app.core.clerk import DbDep
from app.services import clerk_email_webhook_service, donation_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def receive_clerk_webhook(request: Request) -> dict[str, object]:
    payload = await request.body()
    event = clerk_email_webhook_service.verify_clerk_webhook(
        payload=payload,
        headers=request.headers,
    )
    return clerk_email_webhook_service.handle_clerk_webhook(event)


@router.post("/stripe")
async def receive_stripe_webhook(
    request: Request,
    db: DbDep,
) -> dict[str, object]:
    # Stripe signatures are calculated over the exact raw request body.
    payload = await request.body()
    event = donation_service.verify_stripe_webhook(
        payload,
        request.headers.get("stripe-signature", ""),
    )
    return donation_service.handle_stripe_webhook(db, event)
