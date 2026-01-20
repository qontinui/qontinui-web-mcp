"""Tests for the MCP server."""

from unittest.mock import MagicMock, patch

import pytest

from qontinui_web_mcp.client import QontinuiClient
from qontinui_web_mcp.server import (
    AUTH_TOOL_NAMES,
    AUTHENTICATED_TOOL_NAMES,
    call_tool,
    ensure_authenticated,
    list_tools,
)


class TestServerTools:
    """Tests for server tool listing."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self) -> None:
        """Test that list_tools returns all registered tools."""
        tools = await list_tools()
        assert len(tools) > 0

        # Check some expected tools exist
        tool_names = {t.name for t in tools}
        assert "auth_login" in tool_names
        assert "list_projects" in tool_names
        assert "create_workflow" in tool_names
        assert "list_transitions" in tool_names
        assert "create_variable" in tool_names
        assert "create_capture_session" in tool_names

    @pytest.mark.asyncio
    async def test_all_tools_have_descriptions(self) -> None:
        """Test that all tools have descriptions."""
        tools = await list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestServerToolRouting:
    """Tests for tool call routing."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self) -> None:
        """Test that unknown tool returns error."""
        result = await call_tool("unknown_tool", {})
        assert len(result) == 1
        import json

        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_auth_tool_does_not_require_authentication(self) -> None:
        """Test that auth tools don't require authentication."""
        with patch("qontinui_web_mcp.server.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.is_authenticated = False
            mock_get_client.return_value = mock_client

            with patch("qontinui_web_mcp.server.handle_auth_tool") as mock_handle:
                mock_handle.return_value = {"authenticated": False}
                await call_tool("auth_status", {})

            mock_handle.assert_called_once()


class TestAuthentication:
    """Tests for authentication handling."""

    @pytest.mark.asyncio
    async def test_ensure_authenticated_with_token(
        self, mock_client: QontinuiClient
    ) -> None:
        """Test ensure_authenticated with valid token."""
        result = await ensure_authenticated(mock_client)
        assert result is None

    @pytest.mark.asyncio
    async def test_ensure_authenticated_without_credentials(
        self, unauthenticated_client: QontinuiClient
    ) -> None:
        """Test ensure_authenticated without credentials."""
        # Clear any credentials
        unauthenticated_client.settings.email = None
        unauthenticated_client.settings.password = None

        with patch("qontinui_web_mcp.server.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.has_credentials = False
            mock_get_settings.return_value = mock_settings

            result = await ensure_authenticated(unauthenticated_client)

        assert result is not None
        assert result["success"] is False
        assert "auth_login" in result["error"]

    @pytest.mark.asyncio
    async def test_ensure_authenticated_auto_login_success(
        self, unauthenticated_client: QontinuiClient
    ) -> None:
        """Test ensure_authenticated with auto-login."""
        with patch("qontinui_web_mcp.server.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.has_credentials = True
            mock_get_settings.return_value = mock_settings

            with patch.object(
                unauthenticated_client, "login_with_settings"
            ) as mock_login:
                mock_login.return_value = MagicMock(access_token="token")
                unauthenticated_client._access_token = "token"

                result = await ensure_authenticated(unauthenticated_client)

        assert result is None


class TestToolCategories:
    """Tests for tool categorization."""

    def test_auth_tools_not_in_authenticated(self) -> None:
        """Test auth tools are not in authenticated set."""
        for tool_name in AUTH_TOOL_NAMES:
            assert tool_name not in AUTHENTICATED_TOOL_NAMES

    def test_authenticated_tools_comprehensive(self) -> None:
        """Test all non-auth tools require authentication."""
        # This ensures we don't accidentally add tools without auth
        expected_auth_requiring = {
            "list_projects",
            "create_project",
            "get_project",
            "update_project",
            "delete_project",
            "export_configuration",
            "import_configuration",
            "validate_configuration",
            "list_workflows",
            "create_workflow",
            "update_workflow",
            "delete_workflow",
            "list_states",
            "create_state",
            "update_state",
            "delete_state",
            "list_images",
            "add_image",
            "delete_image",
            "execute_workflow",
            "get_execution_status",
            "cancel_execution",
            "list_transitions",
            "create_transition",
            "update_transition",
            "delete_transition",
            "list_variables",
            "create_variable",
            "get_variable",
            "update_variable",
            "delete_variable",
            "get_variable_history",
            "create_capture_session",
            "list_capture_sessions",
            "get_capture_session",
            "upload_capture_screenshot",
            "add_capture_action",
            "complete_capture_session",
            "generate_workflow_from_capture",
            "list_learned_workflows",
            "approve_learned_workflow",
        }

        for tool_name in expected_auth_requiring:
            assert (
                tool_name in AUTHENTICATED_TOOL_NAMES
            ), f"{tool_name} should require auth"
