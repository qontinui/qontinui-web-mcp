"""Workflow variable tools for qontinui-web-mcp.

Variables store data that can be used across workflow executions.
"""

import logging
from typing import Any

from mcp.types import Tool

from qontinui_web_mcp.client import QontinuiClient

logger = logging.getLogger(__name__)


VARIABLES_TOOLS = [
    Tool(
        name="list_variables",
        description=(
            "List workflow variables in a project. "
            "Variables can be global (project-level) or workflow-specific."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "scope": {
                    "type": "string",
                    "description": "Filter by scope",
                    "enum": ["global", "workflow"],
                },
                "workflow_id": {
                    "type": "string",
                    "description": "Filter by workflow ID (for workflow-scoped variables)",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="create_variable",
        description=(
            "Create a workflow variable. "
            "Global variables are accessible across all workflows. "
            "Workflow-scoped variables are only accessible within a specific workflow."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "name": {
                    "type": "string",
                    "description": "Variable name",
                },
                "value": {
                    "description": "Variable value (any JSON-serializable type)",
                },
                "scope": {
                    "type": "string",
                    "description": "Variable scope",
                    "enum": ["global", "workflow"],
                    "default": "global",
                },
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID (required if scope is 'workflow')",
                },
                "description": {
                    "type": "string",
                    "description": "Optional variable description",
                },
            },
            "required": ["project_id", "name", "value"],
        },
    ),
    Tool(
        name="get_variable",
        description="Get a workflow variable by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "variable_id": {
                    "type": "string",
                    "description": "Variable ID",
                },
            },
            "required": ["project_id", "variable_id"],
        },
    ),
    Tool(
        name="update_variable",
        description="Update a workflow variable's value.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "variable_id": {
                    "type": "string",
                    "description": "Variable ID",
                },
                "value": {
                    "description": "New variable value",
                },
                "description": {
                    "type": "string",
                    "description": "New description",
                },
            },
            "required": ["project_id", "variable_id", "value"],
        },
    ),
    Tool(
        name="delete_variable",
        description="Delete a workflow variable.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "variable_id": {
                    "type": "string",
                    "description": "Variable ID to delete",
                },
            },
            "required": ["project_id", "variable_id"],
        },
    ),
    Tool(
        name="get_variable_history",
        description=(
            "Get the change history for a variable. "
            "Shows previous values and when they were changed."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "variable_id": {
                    "type": "string",
                    "description": "Variable ID",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of history entries to return",
                    "default": 20,
                },
            },
            "required": ["project_id", "variable_id"],
        },
    ),
]


async def handle_variables_tool(
    name: str,
    arguments: dict[str, Any],
    client: QontinuiClient,
) -> dict[str, Any]:
    """Handle workflow variable tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Qontinui API client

    Returns:
        Tool result as dict
    """
    try:
        if name == "list_variables":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            params: dict[str, Any] = {}
            if arguments.get("scope"):
                params["scope"] = arguments["scope"]
            if arguments.get("workflow_id"):
                params["workflow_id"] = arguments["workflow_id"]

            result = await client._request(
                "GET",
                f"/api/v1/variables/projects/{project_id}/variables",
                params=params,
            )

            variables = (
                result if isinstance(result, list) else result.get("variables", [])
            )
            return {
                "success": True,
                "count": len(variables),
                "variables": [
                    {
                        "id": v.get("id"),
                        "name": v.get("name"),
                        "value": v.get("value"),
                        "scope": v.get("scope"),
                        "workflow_id": v.get("workflow_id"),
                        "description": v.get("description"),
                    }
                    for v in variables
                ],
            }

        elif name == "create_variable":
            project_id = arguments.get("project_id")
            var_name = arguments.get("name")
            value = arguments.get("value")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not var_name:
                return {"success": False, "error": "Variable name is required"}
            if value is None:
                return {"success": False, "error": "Variable value is required"}

            scope = arguments.get("scope", "global")
            workflow_id = arguments.get("workflow_id")

            if scope == "workflow" and not workflow_id:
                return {
                    "success": False,
                    "error": "Workflow ID is required for workflow-scoped variables",
                }

            result = await client._request(
                "POST",
                f"/api/v1/variables/projects/{project_id}/variables",
                json={
                    "name": var_name,
                    "value": value,
                    "scope": scope,
                    "workflow_id": workflow_id,
                    "description": arguments.get("description"),
                },
            )

            return {
                "success": True,
                "message": f"Created variable '{var_name}'",
                "variable": result,
            }

        elif name == "get_variable":
            project_id = arguments.get("project_id")
            variable_id = arguments.get("variable_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not variable_id:
                return {"success": False, "error": "Variable ID is required"}

            result = await client._request(
                "GET",
                f"/api/v1/variables/projects/{project_id}/variables/{variable_id}",
            )

            return {
                "success": True,
                "variable": result,
            }

        elif name == "update_variable":
            project_id = arguments.get("project_id")
            variable_id = arguments.get("variable_id")
            value = arguments.get("value")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not variable_id:
                return {"success": False, "error": "Variable ID is required"}
            if value is None:
                return {"success": False, "error": "Value is required"}

            update_data: dict[str, Any] = {"value": value}
            if arguments.get("description") is not None:
                update_data["description"] = arguments["description"]

            result = await client._request(
                "PUT",
                f"/api/v1/variables/projects/{project_id}/variables/{variable_id}",
                json=update_data,
            )

            return {
                "success": True,
                "message": "Variable updated",
                "variable": result,
            }

        elif name == "delete_variable":
            project_id = arguments.get("project_id")
            variable_id = arguments.get("variable_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not variable_id:
                return {"success": False, "error": "Variable ID is required"}

            await client._request(
                "DELETE",
                f"/api/v1/variables/projects/{project_id}/variables/{variable_id}",
            )

            return {
                "success": True,
                "message": f"Deleted variable {variable_id}",
            }

        elif name == "get_variable_history":
            project_id = arguments.get("project_id")
            variable_id = arguments.get("variable_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not variable_id:
                return {"success": False, "error": "Variable ID is required"}

            result = await client._request(
                "GET",
                f"/api/v1/variables/projects/{project_id}/variables/{variable_id}/history",
                params={"limit": arguments.get("limit", 20)},
            )

            return {
                "success": True,
                "history": (
                    result if isinstance(result, list) else result.get("history", [])
                ),
            }

        return {"error": f"Unknown variables tool: {name}"}

    except Exception as e:
        logger.error(f"Variables tool error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
