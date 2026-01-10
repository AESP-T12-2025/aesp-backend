from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

router = APIRouter(prefix="/payment", tags=["Payment"])


class PaymentMockRequest(BaseModel):
    user_id: int
    package_id: int
    status: Literal["success", "fail"]


@router.post("/mock")
def mock_payment(payload: PaymentMockRequest):
    transaction = {
        "user_id": payload.user_id,
        "package_id": payload.package_id,
        "status": payload.status,
        "created_at": datetime.utcnow()
    }

    if payload.status == "fail":
        return {
            "message": "Payment failed",
            "transaction": transaction
        }

    subscription = {
        "user_id": payload.user_id,
        "package_id": payload.package_id,
        "start_date": datetime.utcnow(),
        "status": "ACTIVE"
    }

    return {
        "message": "Payment success",
        "transaction": transaction,
        "subscription": subscription
    }
