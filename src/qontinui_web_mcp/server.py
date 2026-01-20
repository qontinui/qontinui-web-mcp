"""MCP server for Qontinui web platform.

Enables AI assistants to create and manage visual automation configurations
through the Qontinui API.
"""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from qontinui_web_mcp.client import QontinuiClient
from qontinui_web_mcp.tools import (
    AUTH_TOOLS,
    CAPTURE_TOOLS,
    CONFIGURATION_TOOLS,
    EXECUTION_TOOLS,
    PROJECTS_TOOLS,
    TRANSITIONS_TOOLS,
    VARIABLES_TOOLS,
    handle_auth_tool,
    handle_capture_tool,
    handle_configuration_tool,
    handle_execution_tool,
    handle_projects_tool,
    handle_transitions_tool,
    handle_variables_tool,
)
from qontinui_web_mcp.utils.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("qontinui-web-mcp")

# Shared client instance
_client: QontinuiClient | None = None


def get_client() -> QontinuiClient:
    """Get or create the shared API client."""
    global _client
    if _client is None:
        _client = QontinuiClient()
    return _client


# Tool name to category mapping
AUTH_TOOL_NAMES = {t.name for t in AUTH_TOOLS}
PROJECTS_TOOL_NAMES = {t.name for t in PROJECTS_TOOLS}
CONFIGURATION_TOOL_NAMES = {t.name for t in CONFIGURATION_TOOLS}
EXECUTION_TOOL_NAMES = {t.name for t in EXECUTION_TOOLS}
CAPTURE_TOOL_NAMES = {t.name for t in CAPTURE_TOOLS}
VARIABLES_TOOL_NAMES = {t.name for t in VARIABLES_TOOLS}
TRANSITIONS_TOOL_NAMES = {t.name for t in TRANSITIONS_TOOLS}

# All tools that require authentication
AUTHENTICATED_TOOL_NAMES = (
    PROJECTS_TOOL_NAMES
    | CONFIGURATION_TOOL_NAMES
    | EXECUTION_TOOL_NAMES
    | CAPTURE_TOOL_NAMES
    | VARIABLES_TOOL_NAMES
    | TRANSITIONS_TOOL_NAMES
)


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return (
        AUTH_TOOLS
        + PROJECTS_TOOLS
        + CONFIGURATION_TOOLS
        + EXECUTION_TOOLS
        + CAPTURE_TOOLS
        + VARIABLES_TOOLS
        + TRANSITIONS_TOOLS
    )


async def ensure_authenticated(client: QontinuiClient) -> dict[str, Any] | None:
    """Ensure the client is authenticated.

    Attempts auto-login if credentials are configured.

    Args:
        client: Qontinui API client

    Returns:
        Error dict if authentication fails, None if successful
    """
    if client.is_authenticated:
        return None

    settings = get_settings()
    if settings.has_credentials:
        try:
            await client.login_with_settings()
            logger.info("Auto-logged in with configured credentials")
            return None
        except Exception as e:
            return {
                "success": False,
                "error": f"Not authenticated. Auto-login failed: {e}",
            }
    else:
        return {
            "success": False,
            "error": "Not authenticated. Use auth_login first.",
        }


@server.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls.

    Routes to the appropriate handler based on tool name.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List containing TextContent with JSON result
    """
    client = get_client()
    logger.info(f"Tool call: {name}")

    try:
        # Auth tools don't require authentication
        if name in AUTH_TOOL_NAMES:
            result = await handle_auth_tool(name, arguments, client)

        # All other tools require authentication
        elif name in AUTHENTICATED_TOOL_NAMES:
            auth_error = await ensure_authenticated(client)
            if auth_error:
                return [TextContent(type="text", text=json.dumps(auth_error))]

            # Route to appropriate handler
            if name in PROJECTS_TOOL_NAMES:
                result = await handle_projects_tool(name, arguments, client)
            elif name in CONFIGURATION_TOOL_NAMES:
                result = await handle_configuration_tool(name, arguments, client)
            elif name in EXECUTION_TOOL_NAMES:
                result = await handle_execution_tool(name, arguments, client)
            elif name in CAPTURE_TOOL_NAMES:
                result = await handle_capture_tool(name, arguments, client)
            elif name in VARIABLES_TOOL_NAMES:
                result = await handle_variables_tool(name, arguments, client)
            elif name in TRANSITIONS_TOOL_NAMES:
                result = await handle_transitions_tool(name, arguments, client)
            else:
                result = {"error": f"Unknown tool: {name}"}
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, default=str))]

    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e),
        }
        return [TextContent(type="text", text=json.dumps(result))]


async def run_server() -> None:
    """Run the MCP server."""
    settings = get_settings()
    logger.info("Starting qontinui-web-mcp server")
    logger.info(f"API URL: {settings.api_url}")
    logger.info(f"Credentials configured: {settings.has_credentials}")
    logger.info(f"Token configured: {settings.has_token}")

    # Count tools
    total_tools = (
        len(AUTH_TOOLS)
        + len(PROJECTS_TOOLS)
        + len(CONFIGURATION_TOOLS)
        + len(EXECUTION_TOOLS)
        + len(CAPTURE_TOOLS)
        + len(VARIABLES_TOOLS)
        + len(TRANSITIONS_TOOLS)
    )
    logger.info(f"Registered {total_tools} tools")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Entry point for the MCP server."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
