"""
conftest.py — Test Configuration and Fixtures
=============================================

pytest "fixtures" are reusable setup/teardown helpers.
They're declared with @pytest.fixture and can be injected into any test.

This file sets up:
1. An in-memory SQLite database for tests (so tests don't touch the real DB)
2. A TestClient that lets us send HTTP requests to the app in tests
3. Helper fixtures that pre-create common test data

Why use a separate test database?
    - Tests should be isolated — they shouldn't affect real data.
    - An in-memory database is fast and gets wiped after each test session.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# We need to import from the backend directory, so we add it to the path.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from database import Base, get_db

# ─── In-memory test database ─────────────────────────────────────────────────
# "sqlite:///:memory:" creates a temporary database entirely in RAM.
# It's erased when the test session ends. Perfect for testing!
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables in the test database once per test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """
    Provide a clean database session for each test.

    After each test, all changes are rolled back so tests don't interfere
    with each other.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """
    Provide an HTTP test client with the test database injected.

    FastAPI's dependency injection lets us replace `get_db` with a version
    that uses our test database session instead of the real one.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_plan(client):
    """Create and return a sample learning plan."""
    response = client.post("/api/plans", json={
        "title": "Learn Python",
        "description": "A comprehensive Python learning plan",
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture()
def sample_goal(client, sample_plan):
    """Create and return a sample goal within the sample plan."""
    response = client.post(f"/api/plans/{sample_plan['id']}/goals", json={
        "title": "Python Basics",
        "description": "Learn fundamental Python concepts",
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture()
def sample_subtask(client, sample_goal):
    """Create and return a sample subtask within the sample goal."""
    response = client.post(f"/api/goals/{sample_goal['id']}/subtasks", json={
        "title": "Variables and Data Types",
        "description": "Understand Python's basic data types",
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture()
def sample_task(client, sample_subtask):
    """Create and return a sample daily task within the sample subtask."""
    response = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={
        "title": "Read chapter 1",
        "description": "Read the intro chapter of Learn Python the Hard Way",
        "estimated_minutes": 45,
    })
    assert response.status_code == 201
    return response.json()
