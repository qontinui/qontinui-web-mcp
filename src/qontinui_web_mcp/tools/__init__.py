"""MCP tool implementations for qontinui-web."""

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

__all__ = [
    "AUTH_TOOLS",
    "CAPTURE_TOOLS",
    "CONFIGURATION_TOOLS",
    "EXECUTION_TOOLS",
    "PROJECTS_TOOLS",
    "TRANSITIONS_TOOLS",
    "VARIABLES_TOOLS",
    "handle_auth_tool",
    "handle_capture_tool",
    "handle_configuration_tool",
    "handle_execution_tool",
    "handle_projects_tool",
    "handle_transitions_tool",
    "handle_variables_tool",
]
