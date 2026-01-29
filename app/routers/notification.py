"""
Notification Router
====================
Issue #50: Push Notifications
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.utils import require_admin
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# =============================================================================
# SCHEMAS
# =============================================================================

class DeviceRegistration(BaseModel):
    token: str = Field(..., description="FCM/APNs token")
    platform: str = Field(..., description="android, ios, or web")
    device_id: str = Field(..., description="Unique device identifier")


class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "SYSTEM"
    user_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class BroadcastNotification(BaseModel):
    title: str
    message: str
    type: str = "SYSTEM"
    target_users: Optional[str] = "all"  # "all" or comma-separated user IDs
    data: Optional[Dict[str, Any]] = None


class NotificationPreferencesUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    notification_types: Optional[Dict[str, bool]] = None


# =============================================================================
# USER ENDPOINTS
# =============================================================================

@router.get("")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's notifications."""
    return db.query(Notification).filter(
        Notification.user_id == current_user.user_id
    ).order_by(Notification.created_at.desc()).all()


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unread notification count."""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.is_read == False
    ).count()
    return {"count": count}


@router.patch("/{noti_id}/read")
def mark_read(
    noti_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read."""
    noti = db.query(Notification).filter(
        Notification.id == noti_id, 
        Notification.user_id == current_user.user_id
    ).first()
    if not noti:
        raise HTTPException(404, "Notification not found")
    noti.is_read = True
    db.commit()
    return {"status": "ok", "notification_id": noti_id}


@router.post("/mark-all-read")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "ok", "message": "All notifications marked as read"}


@router.delete("/{noti_id}")
def delete_notification(
    noti_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    noti = db.query(Notification).filter(
        Notification.id == noti_id,
        Notification.user_id == current_user.user_id
    ).first()
    if not noti:
        raise HTTPException(404, "Notification not found")
    db.delete(noti)
    db.commit()
    return {"status": "ok", "deleted_id": noti_id}


# =============================================================================
# DEVICE TOKEN ENDPOINTS
# =============================================================================

@router.post("/devices")
def register_device(
    device: DeviceRegistration,
    current_user: User = Depends(get_current_user)
):
    """Register device for push notifications."""
    result = notification_service.register_device(
        user_id=current_user.user_id,
        token=device.token,
        platform=device.platform,
        device_id=device.device_id
    )
    return result


@router.delete("/devices/{device_id}")
def unregister_device(
    device_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove device from push notifications."""
    result = notification_service.unregister_device(device_id, current_user.user_id)
    if not result["success"]:
        raise HTTPException(404, result["message"])
    return result


@router.get("/devices")
def get_my_devices(
    current_user: User = Depends(get_current_user)
):
    """Get user's registered devices."""
    return notification_service.get_user_devices(current_user.user_id)


# =============================================================================
# PREFERENCES ENDPOINTS
# =============================================================================

@router.get("/preferences")
def get_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get notification preferences."""
    prefs = notification_service.get_preferences(current_user.user_id)
    return prefs.to_dict()


@router.put("/preferences")
def update_preferences(
    prefs: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update notification preferences."""
    updated = notification_service.update_preferences(
        user_id=current_user.user_id,
        email_notifications=prefs.email_notifications,
        push_notifications=prefs.push_notifications,
        notification_types=prefs.notification_types
    )
    return {"status": "ok", "preferences": updated.to_dict()}


@router.patch("/preferences")
def patch_preferences(
    prefs: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user)
):
    """Partially update notification preferences."""
    updated = notification_service.update_preferences(
        user_id=current_user.user_id,
        email_notifications=prefs.email_notifications,
        push_notifications=prefs.push_notifications,
        notification_types=prefs.notification_types
    )
    return {"status": "ok", "preferences": updated.to_dict()}


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.post("")
async def create_notification(
    notif: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a notification for a user (admin only)."""
    require_admin(current_user)
    
    if not notif.user_id:
        raise HTTPException(400, "user_id is required")
    
    # Create in database
    notification = Notification(
        user_id=notif.user_id,
        title=notif.title,
        message=notif.message,
        type=notif.type
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Send push notification
    await notification_service.send_notification(
        user_id=notif.user_id,
        title=notif.title,
        message=notif.message,
        notification_type=notif.type,
        data=notif.data
    )
    
    return {"status": "ok", "notification_id": notification.id}


@router.post("/send")
async def send_push_notification(
    notif: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a push notification (admin only)."""
    require_admin(current_user)
    
    if not notif.user_id:
        raise HTTPException(400, "user_id is required")
    
    result = await notification_service.send_notification(
        user_id=notif.user_id,
        title=notif.title,
        message=notif.message,
        notification_type=notif.type,
        data=notif.data
    )
    return result


@router.post("/broadcast")
async def broadcast_notification(
    notif: BroadcastNotification,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Broadcast notification to multiple users (admin only)."""
    require_admin(current_user)
    
    # Parse target users
    target_users = None
    if notif.target_users and notif.target_users != "all":
        try:
            target_users = [int(uid.strip()) for uid in notif.target_users.split(",")]
        except ValueError:
            raise HTTPException(400, "Invalid target_users format")
    
    # Also create notifications in database for each target
    if target_users is None:
        # Get all user IDs
        all_users = db.query(User.user_id).all()
        target_users = [u.user_id for u in all_users]
    
    for user_id in target_users:
        notification = Notification(
            user_id=user_id,
            title=notif.title,
            message=notif.message,
            type=notif.type
        )
        db.add(notification)
    
    db.commit()
    
    # Send push notifications
    result = await notification_service.broadcast_notification(
        title=notif.title,
        message=notif.message,
        notification_type=notif.type,
        target_users=target_users,
        data=notif.data
    )
    
    return result

