from sqlalchemy.ext.declarative import declarative_base
from sqlmodel import SQLModel

Base = declarative_base()
SQLModel.metadata = Base.metadata