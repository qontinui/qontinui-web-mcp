"""Tests for the Qontinui API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qontinui_web_mcp.client import (
    AuthenticationError,
    NotFoundError,
    QontinuiClient,
    ValidationError,
)
from qontinui_web_mcp.types import (
    AuthTokens,
    Project,
    ProjectCreate,
    ProjectUpdate,
    User,
)
from qontinui_web_mcp.utils.config import Settings


class TestQontinuiClient:
    """Tests for QontinuiClient."""

    def test_init_with_settings(self, mock_settings: Settings) -> None:
        """Test client initialization with settings."""
        client = QontinuiClient(settings=mock_settings)
        assert client.base_url == "http://localhost:8000"
        assert not client.is_authenticated

    def test_init_with_token(self, mock_settings: Settings) -> None:
        """Test client initialization with pre-configured token."""
        mock_settings.access_token = "test-token"
        client = QontinuiClient(settings=mock_settings)
        assert client.is_authenticated

    def test_is_authenticated(
        self, mock_client: QontinuiClient, unauthenticated_client: QontinuiClient
    ) -> None:
        """Test is_authenticated property."""
        assert mock_client.is_authenticated
        assert not unauthenticated_client.is_authenticated

    def test_logout(self, mock_client: QontinuiClient) -> None:
        """Test logout clears token."""
        assert mock_client.is_authenticated
        mock_client.logout()
        assert not mock_client.is_authenticated


class TestClientAuth:
    """Tests for authentication methods."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        unauthenticated_client: QontinuiClient,
        mock_tokens: AuthTokens,
        mock_user: User,
    ) -> None:
        """Test successful login."""
        with patch.object(unauthenticated_client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client

            # Mock login response
            mock_login_response = MagicMock()
            mock_login_response.status_code = 200
            mock_login_response.json.return_value = {
                "access_token": "new-token",
                "token_type": "bearer",
            }
            mock_http_client.post.return_value = mock_login_response

            # Mock get current user
            with patch.object(
                unauthenticated_client, "get_current_user", return_value=mock_user
            ):
                tokens = await unauthenticated_client.login(
                    "test@example.com", "password"
                )

            assert tokens.access_token == "new-token"
            assert unauthenticated_client.is_authenticated

    @pytest.mark.asyncio
    async def test_login_failure(self, unauthenticated_client: QontinuiClient) -> None:
        """Test login failure raises AuthenticationError."""
        with patch.object(unauthenticated_client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"detail": "Invalid credentials"}
            mock_http_client.post.return_value = mock_response

            with pytest.raises(AuthenticationError):
                await unauthenticated_client.login("bad@example.com", "wrong")


class TestClientProjects:
    """Tests for project methods."""

    @pytest.mark.asyncio
    async def test_list_projects(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test listing projects."""
        with patch.object(mock_client, "_request") as mock_request:
            mock_request.return_value = [mock_project.model_dump()]

            projects = await mock_client.list_projects()

            assert len(projects) == 1
            assert projects[0].name == "Test Project"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating a project."""
        with patch.object(mock_client, "_request") as mock_request:
            mock_request.return_value = mock_project.model_dump()

            project = await mock_client.create_project(
                ProjectCreate(name="Test Project", description="A test project")
            )

            assert project.name == "Test Project"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test getting a project by ID."""
        with patch.object(mock_client, "_request") as mock_request:
            mock_request.return_value = mock_project.model_dump()

            project = await mock_client.get_project(mock_project.id)

            assert project.id == mock_project.id
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test updating a project."""
        with patch.object(mock_client, "_request") as mock_request:
            updated_project = mock_project.model_copy()
            updated_project.name = "Updated Project"
            mock_request.return_value = updated_project.model_dump()

            project = await mock_client.update_project(
                mock_project.id, ProjectUpdate(name="Updated Project")
            )

            assert project.name == "Updated Project"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test deleting a project."""
        with patch.object(mock_client, "_request") as mock_request:
            mock_request.return_value = {}

            await mock_client.delete_project(mock_project.id)

            mock_request.assert_called_once()


class TestClientWorkflows:
    """Tests for workflow methods."""

    @pytest.mark.asyncio
    async def test_get_workflows(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test getting workflows from a project."""
        project_with_workflows = mock_project.model_copy()
        project_with_workflows.configuration = {
            "workflows": [
                {"id": "wf-1", "name": "Workflow 1", "actions": []},
                {"id": "wf-2", "name": "Workflow 2", "actions": []},
            ]
        }

        with patch.object(
            mock_client, "get_project", return_value=project_with_workflows
        ):
            workflows = await mock_client.get_workflows(mock_project.id)

            assert len(workflows) == 2
            assert workflows[0]["name"] == "Workflow 1"

    @pytest.mark.asyncio
    async def test_add_workflow(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test adding a workflow to a project."""
        with patch.object(mock_client, "get_project", return_value=mock_project):
            with patch.object(mock_client, "update_project") as mock_update:
                mock_update.return_value = mock_project

                await mock_client.add_workflow(
                    mock_project.id,
                    {"id": "wf-new", "name": "New Workflow", "actions": []},
                )

                mock_update.assert_called_once()
                call_args = mock_update.call_args
                config = call_args[0][1].configuration
                assert len(config["workflows"]) == 1


class TestClientStates:
    """Tests for state methods."""

    @pytest.mark.asyncio
    async def test_get_states(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test getting states from a project."""
        project_with_states = mock_project.model_copy()
        project_with_states.configuration = {
            "states": [
                {"id": "state-1", "name": "Login Screen"},
                {"id": "state-2", "name": "Dashboard"},
            ]
        }

        with patch.object(mock_client, "get_project", return_value=project_with_states):
            states = await mock_client.get_states(mock_project.id)

            assert len(states) == 2
            assert states[0]["name"] == "Login Screen"

    @pytest.mark.asyncio
    async def test_add_state(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test adding a state to a project."""
        with patch.object(mock_client, "get_project", return_value=mock_project):
            with patch.object(mock_client, "update_project") as mock_update:
                mock_update.return_value = mock_project

                await mock_client.add_state(
                    mock_project.id,
                    {"id": "state-new", "name": "New State"},
                )

                mock_update.assert_called_once()


class TestClientErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_404_raises_not_found(self, mock_client: QontinuiClient) -> None:
        """Test 404 response raises NotFoundError."""
        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_http_client.request.return_value = mock_response

            with pytest.raises(NotFoundError):
                await mock_client._request("GET", "/api/v1/projects/nonexistent")

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self, mock_client: QontinuiClient) -> None:
        """Test 401 response raises AuthenticationError."""
        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_http_client.request.return_value = mock_response

            with pytest.raises(AuthenticationError):
                await mock_client._request("GET", "/api/v1/projects")

    @pytest.mark.asyncio
    async def test_422_raises_validation_error(
        self, mock_client: QontinuiClient
    ) -> None:
        """Test 422 response raises ValidationError."""
        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client

            mock_response = MagicMock()
            mock_response.status_code = 422
            mock_response.json.return_value = {"detail": "Validation failed"}
            mock_http_client.request.return_value = mock_response

            with pytest.raises(ValidationError):
                await mock_client._request("POST", "/api/v1/projects", json={})
