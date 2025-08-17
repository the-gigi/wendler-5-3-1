from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "sqlite:///./data/wendler.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session