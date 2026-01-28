"""
Test script for weekly reports email functionality
Run from project root: python test_weekly_report.py

Requires: Database running and server started
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.user import User
from app.services.report_service import generate_weekly_report_html
from app.services.email_service import send_weekly_report_email

def test_weekly_report():
    """Test generating and sending weekly report"""
    db = SessionLocal()
    
    try:
        # Get first active user
        user = db.query(User).filter(User.is_active == True).first()
        
        if not user:
            print("❌ No active users found in database")
            return False
        
        print(f"✅ Found user: {user.email}")
        
        # Generate HTML
        print("📝 Generating HTML report...")
        html_content = generate_weekly_report_html(user.user_id, db)
        print("✅ HTML report generated")
        
        # Send email
        print(f"📧 Sending email to {user.email}...")
        success = send_weekly_report_email(user.email, html_content)
        
        if success:
            print("✅ Email sent successfully!")
            return True
        else:
            print("❌ Failed to send email")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Testing Weekly Report Email...\n")
    test_weekly_report()
