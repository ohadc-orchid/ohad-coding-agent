from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.settings import get_settings

settings = get_settings()
engine = create_engine(settings.sqlalchemy_db_uri)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
