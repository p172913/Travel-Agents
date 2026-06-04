import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models import Base

# Database URL default configuration
# Falls back to local SQLite if postgres URL is not provided in env.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travelsouls.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes tables in database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency generator to retrieve DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
