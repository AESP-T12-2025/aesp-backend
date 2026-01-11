from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.support import SupportTicket, TicketStatus
from app.models.user import User

router = APIRouter(prefix="/support", tags=["Support & Help"])

class TicketCreate(BaseModel):
    subject: str
    content: str

class TicketReply(BaseModel):
    status: TicketStatus

@router.post("/tickets")
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = SupportTicket(
        user_id=current_user.user_id,
        subject=data.subject,
        content=data.content
    )
    db.add(ticket)
    db.commit()
    return {"message": "Ticket created", "id": ticket.id}

@router.get("/my-tickets")
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(SupportTicket).filter(SupportTicket.user_id == current_user.user_id).all()

# Admin only
@router.put("/tickets/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: int,
    data: TicketReply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
        
    ticket.status = data.status
    db.commit()
    return {"message": "Ticket updated"}
