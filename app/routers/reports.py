from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.services.report_service import generate_weekly_report_html
import logging

logger = logging.getLogger(__name__)

# Learner reports router
learner_router = APIRouter(prefix="/learner/reports", tags=["Learner Reports"])

@learner_router.get("/weekly", response_model=dict)
def get_weekly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get weekly progress report for current user (learner only).
    Returns HTML content with engagement, quality, and gamification metrics.
    """
    # Only learners can access their own reports
    if current_user.role != UserRole.LEARNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only learners can access learner reports"
        )
    
    try:
        html_content = generate_weekly_report_html(current_user.user_id, db)
        return {
            "status": "success",
            "report_type": "weekly",
            "user_id": current_user.user_id,
            "html_content": html_content,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to generate weekly report for user {current_user.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@learner_router.get("/monthly", response_model=dict)
def get_monthly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get monthly progress report for current user (learner only).
    """
    # Only learners can access their own reports
    if current_user.role != UserRole.LEARNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only learners can access learner reports"
        )
    
    try:
        # For now, return similar structure to weekly
        # In future, implement monthly-specific logic
        html_content = generate_weekly_report_html(current_user.user_id, db)
        return {
            "status": "success",
            "report_type": "monthly",
            "user_id": current_user.user_id,
            "html_content": html_content,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to generate monthly report for user {current_user.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")