"""
Notification Service
====================
Provides push notification functionality for AESP platform.

Features:
- Device token registration (FCM/APNs)
- Notification broadcasting
- User preferences management
- Push delivery (mock/FCM)
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from app.core.config import settings


# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# Check for FCM credentials
FCM_ENABLED = getattr(settings, 'FCM_SERVER_KEY', None) is not None


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class NotificationType(str, Enum):
    SYSTEM = "SYSTEM"
    PAYMENT = "PAYMENT"
    BOOKING = "BOOKING"
    FEEDBACK = "FEEDBACK"
    REMINDER = "REMINDER"


class Platform(str, Enum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"


@dataclass
class DeviceToken:
    """Device token for push notifications."""
    user_id: int
    token: str
    platform: Platform
    device_id: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class NotificationPayload:
    """Push notification payload."""
    title: str
    body: str
    notification_type: NotificationType = NotificationType.SYSTEM
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_fcm_format(self) -> Dict[str, Any]:
        """Convert to FCM message format."""
        return {
            "notification": {
                "title": self.title,
                "body": self.body,
            },
            "data": {
                "type": self.notification_type.value,
                **self.data
            }
        }


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    email_notifications: bool = True
    push_notifications: bool = True
    notification_types: Dict[str, bool] = field(default_factory=lambda: {
        "SYSTEM": True,
        "PAYMENT": True,
        "BOOKING": True,
        "FEEDBACK": True,
        "REMINDER": True
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "notification_types": self.notification_types
        }


# =============================================================================
# SERVICE CLASS
# =============================================================================

class NotificationService:
    """
    Push notification service.
    
    Supports:
    - Firebase Cloud Messaging (FCM) for Android/Web
    - Apple Push Notification Service (APNs) for iOS (via FCM)
    - Mock mode for development
    """
    
    def __init__(self):
        """Initialize notification service."""
        self._device_tokens: Dict[str, DeviceToken] = {}  # device_id -> token
        self._user_preferences: Dict[int, NotificationPreferences] = {}  # user_id -> prefs
        self._fcm_client = None
        
        if FCM_ENABLED:
            self._init_fcm()
        else:
            logger.info("📢 Notification service running in mock mode")
    
    def _init_fcm(self):
        """Initialize Firebase Cloud Messaging client."""
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
            
            # Initialize FCM (assuming credentials file exists)
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS', None)
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self._fcm_client = messaging
                logger.info("✅ FCM initialized successfully")
            else:
                logger.warning("⚠️ FIREBASE_CREDENTIALS not set, using mock mode")
        except ImportError:
            logger.warning("⚠️ firebase-admin not installed, using mock mode")
        except Exception as e:
            logger.error(f"❌ FCM initialization failed: {e}")
    
    # =========================================================================
    # DEVICE TOKEN MANAGEMENT
    # =========================================================================
    
    def register_device(
        self,
        user_id: int,
        token: str,
        platform: str,
        device_id: str
    ) -> Dict[str, Any]:
        """
        Register a device for push notifications.
        
        Args:
            user_id: User's ID
            token: FCM/APNs token
            platform: Device platform (android, ios, web)
            device_id: Unique device identifier
            
        Returns:
            Registration result
        """
        device_token = DeviceToken(
            user_id=user_id,
            token=token,
            platform=Platform(platform.lower()),
            device_id=device_id
        )
        
        self._device_tokens[device_id] = device_token
        logger.info(f"📱 Device registered: {device_id} for user {user_id}")
        
        return {
            "success": True,
            "device_id": device_id,
            "platform": platform,
            "message": "Device registered for push notifications"
        }
    
    def unregister_device(self, device_id: str, user_id: int) -> Dict[str, Any]:
        """
        Remove a device from push notifications.
        
        Args:
            device_id: Device to unregister
            user_id: User's ID (for verification)
            
        Returns:
            Unregistration result
        """
        if device_id in self._device_tokens:
            token = self._device_tokens[device_id]
            if token.user_id == user_id:
                del self._device_tokens[device_id]
                logger.info(f"📱 Device unregistered: {device_id}")
                return {"success": True, "message": "Device unregistered"}
        
        return {"success": False, "message": "Device not found"}
    
    def get_user_devices(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all registered devices for a user."""
        devices = [
            {
                "device_id": dt.device_id,
                "platform": dt.platform.value,
                "created_at": dt.created_at.isoformat(),
                "is_active": dt.is_active
            }
            for dt in self._device_tokens.values()
            if dt.user_id == user_id
        ]
        return devices
    
    # =========================================================================
    # NOTIFICATION PREFERENCES
    # =========================================================================
    
    def get_preferences(self, user_id: int) -> NotificationPreferences:
        """Get user's notification preferences."""
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = NotificationPreferences()
        return self._user_preferences[user_id]
    
    def update_preferences(
        self,
        user_id: int,
        email_notifications: Optional[bool] = None,
        push_notifications: Optional[bool] = None,
        notification_types: Optional[Dict[str, bool]] = None
    ) -> NotificationPreferences:
        """
        Update user's notification preferences.
        
        Args:
            user_id: User's ID
            email_notifications: Enable/disable email
            push_notifications: Enable/disable push
            notification_types: Dict of type -> enabled
            
        Returns:
            Updated preferences
        """
        prefs = self.get_preferences(user_id)
        
        if email_notifications is not None:
            prefs.email_notifications = email_notifications
        if push_notifications is not None:
            prefs.push_notifications = push_notifications
        if notification_types:
            prefs.notification_types.update(notification_types)
        
        self._user_preferences[user_id] = prefs
        logger.info(f"📢 Preferences updated for user {user_id}")
        return prefs
    
    # =========================================================================
    # PUSH NOTIFICATION DELIVERY
    # =========================================================================
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "SYSTEM",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a user.
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            data: Additional data payload
            
        Returns:
            Send result
        """
        # Check user preferences
        prefs = self.get_preferences(user_id)
        if not prefs.push_notifications:
            return {"success": False, "reason": "Push notifications disabled"}
        
        if not prefs.notification_types.get(notification_type, True):
            return {"success": False, "reason": f"{notification_type} notifications disabled"}
        
        # Get user's devices
        user_devices = [dt for dt in self._device_tokens.values() if dt.user_id == user_id]
        
        if not user_devices:
            return {"success": False, "reason": "No registered devices"}
        
        payload = NotificationPayload(
            title=title,
            body=message,
            notification_type=NotificationType(notification_type),
            data=data or {}
        )
        
        # Send to each device
        sent_count = 0
        for device in user_devices:
            result = await self._send_to_device(device.token, payload, device.platform)
            if result:
                sent_count += 1
        
        return {
            "success": sent_count > 0,
            "devices_sent": sent_count,
            "total_devices": len(user_devices)
        }
    
    async def _send_to_device(
        self,
        token: str,
        payload: NotificationPayload,
        platform: Platform
    ) -> bool:
        """Send notification to a specific device."""
        if self._fcm_client:
            try:
                message = self._fcm_client.Message(
                    notification=self._fcm_client.Notification(
                        title=payload.title,
                        body=payload.body
                    ),
                    data=payload.data,
                    token=token
                )
                response = self._fcm_client.send(message)
                logger.info(f"📤 FCM sent: {response}")
                return True
            except Exception as e:
                logger.error(f"FCM send error: {e}")
                return False
        else:
            # Mock mode
            logger.info(f"📤 [MOCK] Push sent to {platform.value}: {payload.title}")
            return True
    
    async def broadcast_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "SYSTEM",
        target_users: Optional[List[int]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Broadcast notification to multiple users.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            target_users: List of user IDs (None = all)
            data: Additional data payload
            
        Returns:
            Broadcast result
        """
        if target_users is None:
            # Get all unique user IDs with registered devices
            target_users = list(set(dt.user_id for dt in self._device_tokens.values()))
        
        results = {"sent": 0, "failed": 0, "skipped": 0}
        
        for user_id in target_users:
            result = await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data
            )
            
            if result.get("success"):
                results["sent"] += 1
            elif result.get("reason") == "No registered devices":
                results["skipped"] += 1
            else:
                results["failed"] += 1
        
        return {
            "success": results["sent"] > 0,
            "total_users": len(target_users),
            **results
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

notification_service = NotificationService()
