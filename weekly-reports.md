# Weekly Reports Feature - REDO

## Overview
Redo weekly reports feature with automatic email sending of HTML reports every Monday 00:00.

## Requirements
- Automatic email sending every Monday 00:00
- HTML format emails
- Data: Engagement (lessons completed, minutes studied), Quality (errors corrected), Gamification (XP earned, streak)

## Tasks

### 1. Update Requirements ✅
- Removed reportlab, kept apscheduler
- Added email config to settings

### 2. Create Email Service ✅
- Created `app/services/email_service.py`
- Implemented `send_weekly_report_email()` with SMTP

### 3. Update Report Service ✅
- Modified to `generate_weekly_report_html()`
- Updated data queries for new metrics: lessons completed, errors corrected, XP, streak
- Changed to last week (previous Monday-Sunday)

### 4. Update Scheduled Task ✅
- Changed scheduler to Monday 00:00
- Modified `generate_weekly_reports_for_all` to send emails instead of saving files

### 5. Remove PDF Logic ✅
- Removed PDF generation code
- Removed on-demand API
- Removed reportlab dependency

### 6. Testing ✅
- Test email sending (requires SMTP config)
- Test HTML content generation