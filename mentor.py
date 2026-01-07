from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/mentors/profile")
def create_or_update_profile(data: MentorSchema, db: Session = Depends(get_db)):
    mentor = db.query(Mentor).filter(Mentor.id == data.id).first()
    if not mentor:
        mentor = Mentor(id=data.id, full_name=data.full_name, bio=data.bio, skills=data.skills)
        db.add(mentor)
    else:
        mentor.full_name = data.full_name
        mentor.bio = data.bio
        mentor.skills = data.skills
    
    db.commit()
    return {"message": "Mentor profile updated successfully"}
