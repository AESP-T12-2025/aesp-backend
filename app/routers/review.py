import uuid
from fastapi import APIRouter, Depends, HTTPException

@app.post("/reviews/mentor-submit")
def review_learner(data: MentorReviewCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1. Kiểm tra quyền & tồn tại
    booking = db.query(Booking).filter(Booking.id == data.booking_id, Booking.mentor_id == current_user.id).first()
    if not booking:
        raise HTTPException(404, "Booking không tồn tại hoặc sai Mentor")

    # 2. Lưu đánh giá
    new_review = Review(
        id=str(uuid.uuid4()),
        booking_id=data.booking_id,
        mentor_id=current_user.id,
        learner_id=booking.learner_id,
        score=data.score,
        note=data.note
    )
    db.add(new_review)
    booking.status = "COMPLETED" # Đánh dấu buổi học kết thúc
    
    db.commit()
    return {"status": "success", "review_id": new_review.id}
