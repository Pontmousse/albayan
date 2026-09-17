from pydantic import BaseModel, ConfigDict, Field


class DonationConfigResponse(BaseModel):
    currency: str
    min_amount_minor: int
    max_amount_minor: int
    minor_unit_divisor: int
    preset_amounts_minor: list[int]


class DonationCheckoutCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    amount_minor: int = Field(gt=0)


class DonationCheckoutResponse(BaseModel):
    client_secret: str
    session_id: str
    amount_minor: int
    currency: str


class DonationSessionStatusResponse(BaseModel):
    session_id: str
    status: str
    amount_minor: int
    currency: str
