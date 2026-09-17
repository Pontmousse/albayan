from fastapi import APIRouter

from app.schemas.donation import (
    DonationCheckoutCreate,
    DonationCheckoutResponse,
    DonationConfigResponse,
    DonationSessionStatusResponse,
)
from app.services import donation_service

router = APIRouter(prefix="/api/v1/public/donations", tags=["donations"])


@router.get("/config", response_model=DonationConfigResponse)
def donation_config() -> DonationConfigResponse:
    return donation_service.public_config()


@router.post("/checkout-session", response_model=DonationCheckoutResponse)
def create_checkout_session(
    payload: DonationCheckoutCreate,
) -> DonationCheckoutResponse:
    return donation_service.create_checkout_session(payload.amount_minor)


@router.get("/session/{session_id}", response_model=DonationSessionStatusResponse)
def donation_session_status(
    session_id: str,
) -> DonationSessionStatusResponse:
    return donation_service.session_status(session_id)
