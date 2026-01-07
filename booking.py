@router.post("/bookings/create")
def create_booking(slot_id: int, learner_id: int, db: Session = Depends(get_db)):
    # 1. Kiểm tra slot có tồn tại và còn trống không
    slot = db.query(Slot).filter(Slot.id == slot_id, Slot.status == BookingStatus.AVAILABLE).first()
    
    if not slot:
        raise HTTPException(status_code=400, detail="Slot này không còn trống hoặc không tồn tại")

    # 2. Cập nhật trạng thái slot thành BOOKED
    slot.status = BookingStatus.BOOKED
    
    # 3. Tạo record Booking mới
    new_booking = Booking(
        slot_id=slot_id,
        learner_id=learner_id,
        created_at=datetime.now()
    )
    
    db.add(new_booking)
    try:
        db.commit()
        db.refresh(new_booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi đặt lịch")

    return {"message": "Đặt lịch thành công", "booking_id": new_booking.id}
