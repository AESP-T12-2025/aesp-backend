from app.core.database import engine, Base
from app.models.mentor_resource import MentorVocabSuggestion
from app.models.content import Topic # Trigger loading of Topic model
from app.models.mentor import Mentor # Trigger loading of Mentor model
from sqlalchemy import text

def migrate():
    print("Migrating MentorVocabSuggestion table...")
    # Create table if not exists
    Base.metadata.create_all(bind=engine)
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
