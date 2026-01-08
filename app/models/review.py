class Review(Base):
    __tablename__ = "reviews"
    id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.id"), unique=True)
    mentor_id = Column(String, ForeignKey("users.id"))
    learner_id = Column(String, ForeignKey("users.id"))
    score = Column(Integer)  # 1-5
    note = Column(String)
