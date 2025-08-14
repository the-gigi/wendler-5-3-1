"""
Test configuration and fixtures for the Wendler 5-3-1 backend.
"""
import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from database import get_session
from models import User, UserCreate


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session with in-memory SQLite."""
    # Use in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with dependency override."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user."""
    user = User(
        oauth_id="test_oauth_id",
        email="test@example.com",
        name="Test User",
        provider="google",
        is_onboarded=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="onboarded_user")
def onboarded_user_fixture(session: Session):
    """Create an onboarded test user."""
    user = User(
        oauth_id="onboarded_oauth_id", 
        email="onboarded@example.com",
        name="Onboarded User",
        provider="google",
        is_onboarded=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for authentication."""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Create authorization headers with mock token."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def mock_auth_user(test_user):
    """Mock the authentication dependency to return a test user."""
    def mock_get_current_user():
        return test_user
    
    with patch("main.get_current_user", return_value=test_user):
        yield test_user