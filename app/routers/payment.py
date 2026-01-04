from fastapi import APIRouter
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/transactions")
def get_transactions():
    """
    Mock API trả về lịch sử giao dịch giả lập.
    """
    return [
        {
            "transaction_id": "txn_001",
            "amount": 99000,
            "currency": "VND",
            "package": "Premium Monthly",
            "status": "SUCCESS",
            "date": datetime.now().isoformat()
        },
        {
            "transaction_id": "txn_002",
            "amount": 1000000,
            "currency": "VND",
            "package": "Lifetime Access",
            "status": "PENDING",
            "date": datetime.now().isoformat()
        }
    ]
