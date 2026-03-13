"""
database.py — Database connection setup
=======================================

This module sets up the connection to the SQLite database using SQLAlchemy.

Key concepts:
- SQLite: A lightweight file-based database. No separate server needed!
  The whole database lives in a single file (learningguide.db).
- SQLAlchemy: A Python library that lets us work with databases using
  Python classes and objects instead of writing raw SQL queries.
- Session: A "unit of work" with the database. You open a session,
  do some work, then close it. Like opening and closing a file.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# Load environment variables from a .env file (if it exists).
# This lets us configure settings without hardcoding them in the code.
load_dotenv()

# The database URL tells SQLAlchemy where to find the database.
# Format: "sqlite:///./filename.db"  — three slashes = relative path
# You can override this with a DATABASE_URL environment variable.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./learningguide.db")

# The "engine" is the core connection to the database.
# connect_args={"check_same_thread": False} is needed for SQLite when used
# with FastAPI because FastAPI uses multiple threads.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# SessionLocal is a factory that creates new database sessions.
# autocommit=False means changes aren't saved until you explicitly call commit().
# autoflush=False means SQLAlchemy won't automatically sync changes to the DB
# before each query (we control this manually for better performance).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Every database table (model) will inherit from this class.
    SQLAlchemy uses it to track all the tables in our app.
    """
    pass


def get_db():
    """
    FastAPI dependency that provides a database session.

    This function is used as a "dependency" in FastAPI route handlers.
    It opens a database session, yields it to the route, then always
    closes it — even if an error occurs (thanks to try/finally).

    Usage in a route:
        @app.get("/something")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
