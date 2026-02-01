from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.policy import SystemPolicy
from app.models.user import User

router = APIRouter(prefix="/policies", tags=["System Policies"])

# --- Schemas ---
class PolicyCreate(BaseModel):
    title: str
    content: str
    type: str = "TERMS"  # TERMS, PRIVACY, REFUND

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None

class PolicyResponse(BaseModel):
    id: int
    title: str
    content: str
    type: str
    last_updated: datetime

    class Config:
        from_attributes = True

# --- Public Endpoints ---
@router.get("/", response_model=List[PolicyResponse])
def get_all_policies(db: Session = Depends(get_db)):
    """Public: Get all system policies"""
    return db.query(SystemPolicy).order_by(SystemPolicy.last_updated.desc()).all()

@router.get("/{policy_type}")
def get_policy_by_type(policy_type: str, db: Session = Depends(get_db)):
    """Public: Get policy by type (TERMS, PRIVACY, REFUND)"""
    policy = db.query(SystemPolicy).filter(SystemPolicy.type == policy_type.upper()).first()
    if not policy:
        raise HTTPException(404, f"Policy '{policy_type}' not found")
    return policy

# --- Admin Endpoints ---
@router.post("/", response_model=PolicyResponse)
def create_policy(
    data: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Create a new policy"""
    if current_user.role.value != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    policy = SystemPolicy(
        title=data.title,
        content=data.content,
        type=data.type.upper()
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.put("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Update an existing policy"""
    if current_user.role.value != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    policy = db.query(SystemPolicy).filter(SystemPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(404, "Policy not found")
    
    if data.title:
        policy.title = data.title
    if data.content:
        policy.content = data.content
    if data.type:
        policy.type = data.type.upper()
    
    db.commit()
    db.refresh(policy)
    return policy

@router.delete("/{policy_id}")
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin: Delete a policy"""
    if current_user.role.value != "ADMIN":
        raise HTTPException(403, "Admin only")
    
    policy = db.query(SystemPolicy).filter(SystemPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(404, "Policy not found")
    
    db.delete(policy)
    db.commit()
    return {"message": "Policy deleted"}
