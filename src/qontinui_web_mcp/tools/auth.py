"""Authentication tools for qontinui-web-mcp."""

import logging
from typing import Any

from mcp.types import Tool

from qontinui_web_mcp.client import QontinuiClient

logger = logging.getLogger(__name__)


AUTH_TOOLS = [
    Tool(
        name="auth_login",
        description=(
            "Authenticate with the Qontinui API using email and password. "
            "Returns access token on success. Required before using other tools "
            "unless QONTINUI_ACCESS_TOKEN is configured."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "User email address",
                },
                "password": {
                    "type": "string",
                    "description": "User password",
                },
            },
            "required": ["email", "password"],
        },
    ),
    Tool(
        name="auth_status",
        description=(
            "Check current authentication status. "
            "Returns whether authenticated and current user info if available."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="auth_logout",
        description="Clear stored authentication. Requires re-authentication to use API.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]


async def handle_auth_tool(
    name: str,
    arguments: dict[str, Any],
    client: QontinuiClient,
) -> dict[str, Any]:
    """Handle authentication tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Qontinui API client

    Returns:
        Tool result as dict
    """
    if name == "auth_login":
        email = arguments.get("email", "")
        password = arguments.get("password", "")

        if not email or not password:
            return {
                "success": False,
                "error": "Email and password are required",
            }

        try:
            await client.login(email, password)
            user = await client.get_current_user()
            return {
                "success": True,
                "message": f"Logged in as {user.email}",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "is_verified": user.is_verified,
                },
            }
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    elif name == "auth_status":
        if not client.is_authenticated:
            return {
                "authenticated": False,
                "message": "Not authenticated. Use auth_login to authenticate.",
            }

        try:
            user = await client.get_current_user()
            return {
                "authenticated": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "is_verified": user.is_verified,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return {
                "authenticated": False,
                "error": str(e),
            }

    elif name == "auth_logout":
        client.logout()
        return {
            "success": True,
            "message": "Logged out successfully",
        }

    return {"error": f"Unknown auth tool: {name}"}
