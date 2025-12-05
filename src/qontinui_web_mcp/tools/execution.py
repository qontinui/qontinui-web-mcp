"""Execution management tools for qontinui-web-mcp."""

import logging
from typing import Any
from uuid import UUID

from mcp.types import Tool

from qontinui_web_mcp.client import QontinuiClient

logger = logging.getLogger(__name__)


EXECUTION_TOOLS = [
    Tool(
        name="execute_workflow",
        description=(
            "Execute a workflow on a connected desktop runner. "
            "Requires an active runner connection. "
            "Returns an automation session ID to track progress."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID to execute",
                },
                "runner_id": {
                    "type": "string",
                    "description": "Optional runner device ID (uses first available if not specified)",
                },
                "variables": {
                    "type": "object",
                    "description": "Optional runtime variables to pass to the workflow",
                },
            },
            "required": ["project_id", "workflow_id"],
        },
    ),
    Tool(
        name="get_execution_status",
        description=(
            "Get the status of an automation execution. "
            "Returns progress, logs, and screenshots."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Automation session UUID",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="cancel_execution",
        description="Cancel a running automation execution.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Automation session UUID to cancel",
                },
            },
            "required": ["session_id"],
        },
    ),
]


async def handle_execution_tool(
    name: str,
    arguments: dict[str, Any],
    client: QontinuiClient,
) -> dict[str, Any]:
    """Handle execution management tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Qontinui API client

    Returns:
        Tool result as dict
    """
    try:
        if name == "execute_workflow":
            project_id = arguments.get("project_id")
            workflow_id = arguments.get("workflow_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not workflow_id:
                return {"success": False, "error": "Workflow ID is required"}

            result = await client.execute_workflow(
                UUID(project_id),
                workflow_id,
                runner_id=arguments.get("runner_id"),
                variables=arguments.get("variables"),
            )

            return {
                "success": True,
                "message": "Workflow execution started",
                "session": result,
            }

        elif name == "get_execution_status":
            session_id = arguments.get("session_id")
            if not session_id:
                return {"success": False, "error": "Session ID is required"}

            result = await client.get_execution_status(UUID(session_id))
            return {
                "success": True,
                "status": result,
            }

        elif name == "cancel_execution":
            session_id = arguments.get("session_id")
            if not session_id:
                return {"success": False, "error": "Session ID is required"}

            result = await client.cancel_execution(UUID(session_id))
            return {
                "success": True,
                "message": "Execution cancelled",
                "result": result,
            }

        return {"error": f"Unknown execution tool: {name}"}

    except Exception as e:
        logger.error(f"Execution tool error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
