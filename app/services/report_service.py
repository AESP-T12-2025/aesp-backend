"""
Report Service
==============
Handles generation of weekly reports.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.gamification import UserDailyStats
from app.models.content import SpeakingSession, AIFeedback

logger = logging.getLogger(__name__)


def generate_weekly_report_html(user_id: int, db: Session) -> str:
    """
    Generate weekly HTML report for a user.
    Returns HTML content string.
    """
    # Get user
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # Calculate dates (last week: Monday to Sunday)
    today = datetime.now().date()
    # Find last Monday
    last_monday = today - timedelta(days=today.weekday() + 7)  # Previous Monday
    last_sunday = last_monday + timedelta(days=6)

    # Query data for last week
    stats = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == user_id,
        UserDailyStats.date >= last_monday,
        UserDailyStats.date <= last_sunday
    ).all()

    # Engagement metrics
    lessons_completed = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == user_id,
        SpeakingSession.start_time >= last_monday,
        SpeakingSession.start_time <= last_sunday + timedelta(days=1)
    ).count()

    minutes_studied = sum(s.speaking_duration_seconds for s in stats) // 60

    # Quality metrics
    errors_corrected = db.query(AIFeedback).filter(
        AIFeedback.session_id.in_(
            db.query(SpeakingSession.session_id).filter(
                SpeakingSession.user_id == user_id,
                SpeakingSession.start_time >= last_monday,
                SpeakingSession.start_time <= last_sunday + timedelta(days=1)
            )
        )
    ).count()

    # Gamification metrics
    xp_earned = sum(s.words_learned * 10 for s in stats)  # Assuming 10 XP per word

    # Get current streak (from latest stat)
    latest_stat = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == user_id
    ).order_by(UserDailyStats.date.desc()).first()
    current_streak = latest_stat.login_streak_current if latest_stat else 0

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Báo cáo hàng tuần AESP</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
            .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
            .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .metric h3 {{ margin: 0 0 5px 0; color: #007bff; }}
            .metric p {{ margin: 0; font-size: 18px; font-weight: bold; }}
            .footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Báo cáo hàng tuần AESP</h1>
                <p>Xin chào {user.full_name or user.email}!</p>
                <p>Tuần: {last_monday} - {last_sunday}</p>
            </div>

            <div class="metric">
                <h3>🎯 Hoạt động học tập (Engagement)</h3>
                <p>Bài học hoàn thành: {lessons_completed}</p>
                <p>Phút đã học: {minutes_studied}</p>
            </div>

            <div class="metric">
                <h3>✨ Chất lượng học tập (Quality)</h3>
                <p>Lỗi đã sửa: {errors_corrected}</p>
            </div>

            <div class="metric">
                <h3>🏆 Thành tích (Gamification)</h3>
                <p>XP kiếm được: {xp_earned}</p>
                <p>Chuỗi ngày học: {current_streak} ngày</p>
            </div>

            <div class="footer">
                <p>Tiếp tục học tập để đạt mục tiêu của bạn!</p>
                <p>AESP - AI English Speaking Practice</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


async def generate_weekly_reports_for_all():
    """
    Scheduled task to generate and send weekly reports to all users.
    """
    from app.core.database import SessionLocal
    from app.services.email_service import send_weekly_report_email

    logger.info("📊 Starting weekly reports email generation for all users...")

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            try:
                html_content = generate_weekly_report_html(user.user_id, db)
                success = send_weekly_report_email(user.email, html_content)
                if success:
                    logger.info(f"✅ Sent weekly report to {user.email}")
                else:
                    logger.warning(f"⚠️ Failed to send to {user.email}")
            except Exception as e:
                logger.error(f"❌ Failed to generate report for user {user.email}: {str(e)}")

        logger.info("📊 Weekly reports email generation completed")
    finally:
        db.close()
    """
    Generate weekly PDF report for a user.
    Returns the file path of the generated PDF.
    """
    # Get user
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # Calculate dates
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    # Query data
    stats = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == user_id,
        UserDailyStats.date >= start_of_week,
        UserDailyStats.date <= end_of_week
    ).all()

    # Aggregate data
    total_seconds = sum(s.speaking_duration_seconds for s in stats)
    total_words = sum(s.words_learned for s in stats)
    total_hours = round(total_seconds / 3600, 1)
    xp_earned = total_words * 10

    # Average score
    avg_score_query = db.query(func.avg(AIFeedback.grammar_score)).join(SpeakingSession).filter(
        SpeakingSession.user_id == user_id,
        SpeakingSession.created_at >= start_of_week,
        SpeakingSession.created_at <= end_of_week + timedelta(days=1)
    ).scalar()
    avg_score = round(avg_score_query / 10, 1) if avg_score_query else 0.0

    # Sessions completed
    sessions_count = db.query(SpeakingSession).filter(
        SpeakingSession.user_id == user_id,
        SpeakingSession.created_at >= start_of_week,
        SpeakingSession.created_at <= end_of_week + timedelta(days=1)
    ).count()

    # Generate PDF
    filename = f"weekly_report_{user_id}_{start_of_week}.pdf"
    filepath = os.path.join("app", "static", "reports", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph(f"Báo cáo hàng tuần - {user.username}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Period
    period = Paragraph(f"Tuần: {start_of_week} đến {end_of_week}", styles['Normal'])
    story.append(period)
    story.append(Spacer(1, 12))

    # Stats table
    data = [
        ['Chỉ số', 'Giá trị'],
        ['Tổng thời gian nói (giờ)', str(total_hours)],
        ['Từ vựng học được', str(total_words)],
        ['Điểm XP kiếm được', str(xp_earned)],
        ['Điểm trung bình ngữ pháp', str(avg_score)],
        ['Số phiên luyện tập', str(sessions_count)]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)

    # Build PDF
    doc.build(story)

    return filepath