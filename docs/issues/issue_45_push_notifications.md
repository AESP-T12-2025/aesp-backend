# Issue #45: Push Notifications

## 📋 Description
Implement push notification system for real-time updates to mobile and web clients.

## 🎯 Requirements
- **REQ-SYSTEM-5**: Push notification mechanism
- Support notification types: SYSTEM, PAYMENT, BOOKING, FEEDBACK, REMINDER
- Device token registration for FCM (Android/Web) and APNs (iOS)
- User notification preferences

## 📌 Acceptance Criteria
- [ ] `POST /notifications/devices` - Register device token
- [ ] `DELETE /notifications/devices/{device_id}` - Unregister device
- [ ] `POST /notifications/broadcast` - Admin broadcasts to all users
- [ ] `GET /notifications/preferences` - Get user preferences
- [ ] `PUT /notifications/preferences` - Update preferences
- [ ] `GET /notifications/unread-count` - Get unread count
- [ ] `POST /notifications/mark-all-read` - Mark all as read

## 🔧 Technical Details
```python
# Device Registration
POST /notifications/devices
{
    "token": "fcm_device_token",
    "platform": "android",  # android | ios | web
    "device_id": "unique_device_id"
}

# Broadcast Notification
POST /notifications/broadcast
{
    "title": "System Update",
    "message": "New features available!",
    "type": "SYSTEM",
    "data": {"action": "open_updates"}
}

# User Preferences
PUT /notifications/preferences
{
    "email_notifications": true,
    "push_notifications": true,
    "notification_types": {
        "SYSTEM": true,
        "PAYMENT": true,
        "BOOKING": true,
        "FEEDBACK": true,
        "REMINDER": false
    }
}
```

## 📦 Dependencies
- `firebase-admin` for FCM
- OR `pyfcm` for FCM (simpler)
- Task queue (Celery/ARQ) for async delivery

## 🧪 Tests
Tests are prepared in: `tests/unit/test_issue_45_push_notifications.py`

## 📊 Priority
🟢 **Nice to Have** - Enhances user engagement

## 🏷️ Labels
`enhancement`, `backend`, `notifications`, `priority-medium`
