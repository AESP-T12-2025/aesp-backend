from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import deps
from app.models.support import SupportTicket, TicketStatus
from app.models.user import User, UserRole
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/support", tags=["Support"])

# Schemas
class TicketCreate(BaseModel):
    title: str
    description: str
    priority: str = "MEDIUM"

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None

class TicketResponse(BaseModel):
    ticket_id: int
    user_id: int
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Endpoints

@router.post("/", response_model=TicketResponse)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    new_ticket = SupportTicket(
        user_id=current_user.user_id,
        title=ticket.title,
        description=ticket.description,
        priority=ticket.priority
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = db.query(SupportTicket)
    
    # If admin, show all (filtered by status)
    # If learner/mentor, show only their tickets
    if current_user.role != UserRole.ADMIN:
        query = query.filter(SupportTicket.user_id == current_user.user_id)
        
    if status:
        query = query.filter(SupportTicket.status == status)
        
    return query.order_by(SupportTicket.created_at.desc()).all()

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Check permission
    if current_user.role != UserRole.ADMIN and ticket.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return ticket

@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    update_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Only Admin can update status/priority usually
    # But maybe user can close it? Let's restrict to Admin for now or if user cancels
    
    if current_user.role != UserRole.ADMIN:
        # Check if user wants to cancel (close) only
        if update_data.status == "CLOSED" and ticket.user_id == current_user.user_id:
            pass # Allow user to close their own ticket
        else:
             raise HTTPException(status_code=403, detail="Only admins can update tickets")

    if update_data.status:
        ticket.status = update_data.status
    if update_data.priority:
        ticket.priority = update_data.priority
        
    db.commit()
    db.refresh(ticket)
    return ticket
