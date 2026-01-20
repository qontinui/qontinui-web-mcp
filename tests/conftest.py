"""Pytest fixtures for qontinui-web-mcp tests."""

from datetime import datetime
from uuid import UUID

import pytest

from qontinui_web_mcp.client import QontinuiClient
from qontinui_web_mcp.types import AuthTokens, Project, User
from qontinui_web_mcp.utils.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings."""
    return Settings(
        api_url="http://localhost:8000",
        email="test@example.com",
        password="testpassword",
    )


@pytest.fixture
def mock_user() -> User:
    """Create a mock user."""
    return User(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )


@pytest.fixture
def mock_project() -> Project:
    """Create a mock project."""
    return Project(
        id=UUID("abcdef12-1234-1234-1234-123456789012"),
        name="Test Project",
        description="A test project",
        configuration={
            "workflows": [],
            "states": [],
            "transitions": [],
            "images": [],
        },
        version=1,
        owner_id=UUID("12345678-1234-1234-1234-123456789012"),
        organization_id=None,
        is_public=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_tokens() -> AuthTokens:
    """Create mock auth tokens."""
    return AuthTokens(
        access_token="mock-access-token",
        token_type="bearer",
    )


@pytest.fixture
def mock_client(
    mock_settings: Settings, mock_user: User, mock_tokens: AuthTokens
) -> QontinuiClient:
    """Create a mock Qontinui client."""
    client = QontinuiClient(settings=mock_settings)
    client._access_token = mock_tokens.access_token
    return client


@pytest.fixture
def unauthenticated_client(mock_settings: Settings) -> QontinuiClient:
    """Create an unauthenticated client."""
    return QontinuiClient(settings=mock_settings)
