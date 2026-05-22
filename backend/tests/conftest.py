"""Test configuration — uses temporary SQLite file to avoid MySQL dependency."""

import os
import tempfile

# Set BEFORE any app imports — database.py/config.py reads this env var
# Using temp file so all engines (test + app) share the same database
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Now import app modules — they'll use the test DATABASE_URL
from app.database import Base, get_db
from app.main import create_app
from app.models.user import User
from app.services.auth import hash_password

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables exist before any test
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db():
    """Clean all data before each test, keep schema."""
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
    yield


@pytest.fixture
def db_session():
    """Provide a fresh session for each test."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI TestClient with test DB override."""
    app = create_app()

    def _get_test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Create and return an admin user."""
    user = User(
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """Return a valid JWT token."""
    resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    return resp.json()["access_token"]


@pytest.fixture
def auth_header(admin_token):
    """Return Authorization header for authenticated requests."""
    return {"Authorization": f"Bearer {admin_token}"}


def pytest_unconfigure():
    """Clean up temp file after all tests."""
    try:
        os.close(_db_fd)
        os.unlink(_db_path)
    except (PermissionError, OSError):
        pass
