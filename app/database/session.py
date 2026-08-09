from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase): pass

def make_engine(url: str):
    return create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})

def make_session_factory(url: str):
    return sessionmaker(make_engine(url), expire_on_commit=False)
