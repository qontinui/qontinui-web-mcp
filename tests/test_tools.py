"""Tests for MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

from qontinui_web_mcp.client import QontinuiClient
from qontinui_web_mcp.tools.auth import AUTH_TOOLS, handle_auth_tool
from qontinui_web_mcp.tools.capture import CAPTURE_TOOLS, handle_capture_tool
from qontinui_web_mcp.tools.configuration import (
    CONFIGURATION_TOOLS,
    handle_configuration_tool,
)
from qontinui_web_mcp.tools.execution import EXECUTION_TOOLS, handle_execution_tool
from qontinui_web_mcp.tools.projects import PROJECTS_TOOLS, handle_projects_tool
from qontinui_web_mcp.tools.transitions import (
    TRANSITIONS_TOOLS,
    handle_transitions_tool,
)
from qontinui_web_mcp.tools.variables import VARIABLES_TOOLS, handle_variables_tool
from qontinui_web_mcp.types import Project, User


class TestToolDefinitions:
    """Tests for tool definitions."""

    def test_auth_tools_defined(self) -> None:
        """Test auth tools are properly defined."""
        assert len(AUTH_TOOLS) == 3
        tool_names = {t.name for t in AUTH_TOOLS}
        assert "auth_login" in tool_names
        assert "auth_status" in tool_names
        assert "auth_logout" in tool_names

    def test_projects_tools_defined(self) -> None:
        """Test projects tools are properly defined."""
        assert len(PROJECTS_TOOLS) == 5
        tool_names = {t.name for t in PROJECTS_TOOLS}
        assert "list_projects" in tool_names
        assert "create_project" in tool_names
        assert "get_project" in tool_names
        assert "update_project" in tool_names
        assert "delete_project" in tool_names

    def test_configuration_tools_defined(self) -> None:
        """Test configuration tools are properly defined."""
        tool_names = {t.name for t in CONFIGURATION_TOOLS}
        assert "export_configuration" in tool_names
        assert "import_configuration" in tool_names
        assert "list_workflows" in tool_names
        assert "create_workflow" in tool_names
        assert "list_states" in tool_names
        assert "create_state" in tool_names
        assert "list_images" in tool_names
        assert "add_image" in tool_names

    def test_execution_tools_defined(self) -> None:
        """Test execution tools are properly defined."""
        assert len(EXECUTION_TOOLS) == 3
        tool_names = {t.name for t in EXECUTION_TOOLS}
        assert "execute_workflow" in tool_names
        assert "get_execution_status" in tool_names
        assert "cancel_execution" in tool_names

    def test_capture_tools_defined(self) -> None:
        """Test capture tools are properly defined."""
        tool_names = {t.name for t in CAPTURE_TOOLS}
        assert "create_capture_session" in tool_names
        assert "list_capture_sessions" in tool_names
        assert "upload_capture_screenshot" in tool_names
        assert "add_capture_action" in tool_names
        assert "complete_capture_session" in tool_names

    def test_variables_tools_defined(self) -> None:
        """Test variables tools are properly defined."""
        tool_names = {t.name for t in VARIABLES_TOOLS}
        assert "list_variables" in tool_names
        assert "create_variable" in tool_names
        assert "update_variable" in tool_names
        assert "delete_variable" in tool_names

    def test_transitions_tools_defined(self) -> None:
        """Test transitions tools are properly defined."""
        tool_names = {t.name for t in TRANSITIONS_TOOLS}
        assert "list_transitions" in tool_names
        assert "create_transition" in tool_names
        assert "update_transition" in tool_names
        assert "delete_transition" in tool_names

    def test_all_tools_have_schemas(self) -> None:
        """Test all tools have input schemas."""
        all_tools = (
            AUTH_TOOLS
            + PROJECTS_TOOLS
            + CONFIGURATION_TOOLS
            + EXECUTION_TOOLS
            + CAPTURE_TOOLS
            + VARIABLES_TOOLS
            + TRANSITIONS_TOOLS
        )
        for tool in all_tools:
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"


class TestAuthTools:
    """Tests for authentication tools."""

    @pytest.mark.asyncio
    async def test_auth_login_success(
        self, mock_client: QontinuiClient, mock_user: User
    ) -> None:
        """Test successful login."""
        mock_client._access_token = None  # Start unauthenticated

        with patch.object(mock_client, "login") as mock_login:
            mock_login.return_value = MagicMock(access_token="new-token")
            with patch.object(mock_client, "get_current_user", return_value=mock_user):
                result = await handle_auth_tool(
                    "auth_login",
                    {"email": "test@example.com", "password": "password"},
                    mock_client,
                )

        assert result["success"] is True
        assert "user" in result

    @pytest.mark.asyncio
    async def test_auth_login_missing_credentials(
        self, mock_client: QontinuiClient
    ) -> None:
        """Test login with missing credentials."""
        result = await handle_auth_tool(
            "auth_login",
            {"email": "", "password": ""},
            mock_client,
        )
        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_auth_status_authenticated(
        self, mock_client: QontinuiClient, mock_user: User
    ) -> None:
        """Test auth status when authenticated."""
        with patch.object(mock_client, "get_current_user", return_value=mock_user):
            result = await handle_auth_tool("auth_status", {}, mock_client)

        assert result["authenticated"] is True
        assert result["user"]["email"] == mock_user.email

    @pytest.mark.asyncio
    async def test_auth_status_unauthenticated(
        self, unauthenticated_client: QontinuiClient
    ) -> None:
        """Test auth status when not authenticated."""
        result = await handle_auth_tool("auth_status", {}, unauthenticated_client)
        assert result["authenticated"] is False

    @pytest.mark.asyncio
    async def test_auth_logout(self, mock_client: QontinuiClient) -> None:
        """Test logout."""
        result = await handle_auth_tool("auth_logout", {}, mock_client)
        assert result["success"] is True
        assert not mock_client.is_authenticated


class TestProjectsTools:
    """Tests for project tools."""

    @pytest.mark.asyncio
    async def test_list_projects(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test listing projects."""
        with patch.object(mock_client, "list_projects", return_value=[mock_project]):
            result = await handle_projects_tool("list_projects", {}, mock_client)

        assert result["success"] is True
        assert result["count"] == 1
        assert result["projects"][0]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_create_project(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating a project."""
        with patch.object(mock_client, "create_project", return_value=mock_project):
            result = await handle_projects_tool(
                "create_project",
                {"name": "Test Project", "description": "A test project"},
                mock_client,
            )

        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_create_project_missing_name(
        self, mock_client: QontinuiClient
    ) -> None:
        """Test creating a project without name."""
        result = await handle_projects_tool("create_project", {}, mock_client)
        assert result["success"] is False
        assert "name" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_project(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test getting a project."""
        with patch.object(mock_client, "get_project", return_value=mock_project):
            result = await handle_projects_tool(
                "get_project",
                {"project_id": str(mock_project.id)},
                mock_client,
            )

        assert result["success"] is True
        assert result["project"]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_delete_project(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test deleting a project."""
        with patch.object(mock_client, "delete_project") as mock_delete:
            result = await handle_projects_tool(
                "delete_project",
                {"project_id": str(mock_project.id)},
                mock_client,
            )

        assert result["success"] is True
        mock_delete.assert_called_once()


class TestConfigurationTools:
    """Tests for configuration tools."""

    @pytest.mark.asyncio
    async def test_list_workflows(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test listing workflows."""
        project_with_workflows = mock_project.model_copy()
        project_with_workflows.configuration = {
            "workflows": [
                {"id": "wf-1", "name": "Workflow 1", "actions": []},
            ]
        }

        with patch.object(
            mock_client,
            "get_workflows",
            return_value=[{"id": "wf-1", "name": "Workflow 1", "actions": []}],
        ):
            result = await handle_configuration_tool(
                "list_workflows",
                {"project_id": str(mock_project.id)},
                mock_client,
            )

        assert result["success"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_create_workflow(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating a workflow."""
        with patch.object(mock_client, "add_workflow", return_value=mock_project):
            result = await handle_configuration_tool(
                "create_workflow",
                {
                    "project_id": str(mock_project.id),
                    "name": "New Workflow",
                },
                mock_client,
            )

        assert result["success"] is True
        assert result["workflow"]["name"] == "New Workflow"

    @pytest.mark.asyncio
    async def test_list_states(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test listing states."""
        with patch.object(
            mock_client,
            "get_states",
            return_value=[{"id": "state-1", "name": "Login"}],
        ):
            result = await handle_configuration_tool(
                "list_states",
                {"project_id": str(mock_project.id)},
                mock_client,
            )

        assert result["success"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_create_state(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating a state."""
        with patch.object(mock_client, "add_state", return_value=mock_project):
            result = await handle_configuration_tool(
                "create_state",
                {
                    "project_id": str(mock_project.id),
                    "name": "New State",
                },
                mock_client,
            )

        assert result["success"] is True
        assert result["state"]["name"] == "New State"


class TestTransitionsTools:
    """Tests for transition tools."""

    @pytest.mark.asyncio
    async def test_list_transitions(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test listing transitions."""
        project_with_transitions = mock_project.model_copy()
        project_with_transitions.configuration = {
            "transitions": [
                {
                    "id": "t-1",
                    "name": "Login",
                    "type": "action",
                    "fromState": "state-1",
                    "toState": "state-2",
                    "processes": [],
                }
            ]
        }

        with patch.object(
            mock_client, "get_project", return_value=project_with_transitions
        ):
            result = await handle_transitions_tool(
                "list_transitions",
                {"project_id": str(mock_project.id)},
                mock_client,
            )

        assert result["success"] is True
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_create_transition(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating a transition."""
        with patch.object(mock_client, "get_project", return_value=mock_project):
            with patch.object(mock_client, "update_project", return_value=mock_project):
                result = await handle_transitions_tool(
                    "create_transition",
                    {
                        "project_id": str(mock_project.id),
                        "name": "New Transition",
                        "from_state": "state-1",
                        "to_state": "state-2",
                    },
                    mock_client,
                )

        assert result["success"] is True
        assert result["transition"]["name"] == "New Transition"


class TestVariablesTools:
    """Tests for variable tools."""

    @pytest.mark.asyncio
    async def test_create_variable(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating a variable."""
        with patch.object(
            mock_client,
            "_request",
            return_value={
                "id": "var-1",
                "name": "test_var",
                "value": "test_value",
                "scope": "global",
            },
        ):
            result = await handle_variables_tool(
                "create_variable",
                {
                    "project_id": str(mock_project.id),
                    "name": "test_var",
                    "value": "test_value",
                },
                mock_client,
            )

        assert result["success"] is True
        assert result["variable"]["name"] == "test_var"

    @pytest.mark.asyncio
    async def test_create_workflow_scoped_variable_missing_workflow_id(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating workflow-scoped variable without workflow_id."""
        result = await handle_variables_tool(
            "create_variable",
            {
                "project_id": str(mock_project.id),
                "name": "test_var",
                "value": "test_value",
                "scope": "workflow",
            },
            mock_client,
        )

        assert result["success"] is False
        assert "workflow" in result["error"].lower()


class TestCaptureTools:
    """Tests for capture tools."""

    @pytest.mark.asyncio
    async def test_create_capture_session(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test creating a capture session."""
        with patch.object(
            mock_client,
            "_request",
            return_value={
                "id": "session-1",
                "name": "Test Session",
                "status": "capturing",
            },
        ):
            result = await handle_capture_tool(
                "create_capture_session",
                {
                    "project_id": str(mock_project.id),
                    "name": "Test Session",
                },
                mock_client,
            )

        assert result["success"] is True
        assert result["session"]["name"] == "Test Session"


class TestExecutionTools:
    """Tests for execution tools."""

    @pytest.mark.asyncio
    async def test_execute_workflow(
        self, mock_client: QontinuiClient, mock_project: Project
    ) -> None:
        """Test executing a workflow."""
        with patch.object(
            mock_client,
            "execute_workflow",
            return_value={"session_id": "exec-1", "status": "running"},
        ):
            result = await handle_execution_tool(
                "execute_workflow",
                {
                    "project_id": str(mock_project.id),
                    "workflow_id": "wf-1",
                },
                mock_client,
            )

        assert result["success"] is True
        assert "session" in result

    @pytest.mark.asyncio
    async def test_execute_workflow_missing_params(
        self, mock_client: QontinuiClient
    ) -> None:
        """Test executing workflow with missing parameters."""
        result = await handle_execution_tool(
            "execute_workflow",
            {},
            mock_client,
        )
        assert result["success"] is False
