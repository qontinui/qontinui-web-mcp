"""State transition tools for qontinui-web-mcp.

Transitions connect states in the state machine and define which workflows
run during state changes.
"""

import logging
import uuid
from typing import Any
from uuid import UUID

from mcp.types import Tool

from qontinui_web_mcp.client import QontinuiClient
from qontinui_web_mcp.types import ProjectUpdate

logger = logging.getLogger(__name__)


TRANSITIONS_TOOLS = [
    Tool(
        name="list_transitions",
        description=(
            "List all state transitions in a project. "
            "Transitions define how the automation moves between UI states."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="create_transition",
        description=(
            "Create a state transition. "
            "Transitions connect a source state to a target state "
            "and specify which workflows execute during the transition."
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
                    "description": "Transition name",
                },
                "from_state": {
                    "type": "string",
                    "description": "Source state ID",
                },
                "to_state": {
                    "type": "string",
                    "description": "Target state ID",
                },
                "workflows": {
                    "type": "array",
                    "description": "Workflow IDs to execute during transition",
                    "items": {"type": "string"},
                },
                "type": {
                    "type": "string",
                    "description": "Transition type",
                    "enum": ["action", "automatic", "conditional"],
                    "default": "action",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds",
                    "default": 10000,
                },
                "retry_count": {
                    "type": "integer",
                    "description": "Number of retries on failure",
                    "default": 3,
                },
            },
            "required": ["project_id", "name", "from_state", "to_state"],
        },
    ),
    Tool(
        name="update_transition",
        description="Update a state transition.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "transition_id": {
                    "type": "string",
                    "description": "Transition ID to update",
                },
                "name": {
                    "type": "string",
                    "description": "New transition name",
                },
                "from_state": {
                    "type": "string",
                    "description": "New source state ID",
                },
                "to_state": {
                    "type": "string",
                    "description": "New target state ID",
                },
                "workflows": {
                    "type": "array",
                    "description": "New workflow IDs",
                    "items": {"type": "string"},
                },
                "timeout": {
                    "type": "integer",
                    "description": "New timeout in milliseconds",
                },
                "retry_count": {
                    "type": "integer",
                    "description": "New retry count",
                },
            },
            "required": ["project_id", "transition_id"],
        },
    ),
    Tool(
        name="delete_transition",
        description="Delete a state transition.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "transition_id": {
                    "type": "string",
                    "description": "Transition ID to delete",
                },
            },
            "required": ["project_id", "transition_id"],
        },
    ),
]


async def handle_transitions_tool(
    name: str,
    arguments: dict[str, Any],
    client: QontinuiClient,
) -> dict[str, Any]:
    """Handle state transition tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Qontinui API client

    Returns:
        Tool result as dict
    """
    try:
        if name == "list_transitions":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            project = await client.get_project(UUID(project_id))
            transitions = project.configuration.get("transitions", [])

            return {
                "success": True,
                "count": len(transitions),
                "transitions": [
                    {
                        "id": t.get("id"),
                        "name": t.get("name"),
                        "type": t.get("type", "action"),
                        "from_state": t.get("fromState"),
                        "to_state": t.get("toState"),
                        "workflows": t.get("processes", []),
                        "timeout": t.get("timeout"),
                        "retry_count": t.get("retryCount"),
                    }
                    for t in transitions
                ],
            }

        elif name == "create_transition":
            project_id = arguments.get("project_id")
            transition_name = arguments.get("name")
            from_state = arguments.get("from_state")
            to_state = arguments.get("to_state")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not transition_name:
                return {"success": False, "error": "Transition name is required"}
            if not from_state:
                return {
                    "success": False,
                    "error": "Source state (from_state) is required",
                }
            if not to_state:
                return {
                    "success": False,
                    "error": "Target state (to_state) is required",
                }

            project = await client.get_project(UUID(project_id))
            config = project.configuration.copy()
            transitions = config.get("transitions", [])

            transition = {
                "id": f"transition-{uuid.uuid4().hex[:8]}",
                "type": arguments.get("type", "action"),
                "name": transition_name,
                "processes": arguments.get("workflows", []),
                "fromState": from_state,
                "toState": to_state,
                "staysVisible": False,
                "activateStates": [],
                "deactivateStates": [],
                "timeout": arguments.get("timeout", 10000),
                "retryCount": arguments.get("retry_count", 3),
            }

            transitions.append(transition)
            config["transitions"] = transitions

            await client.update_project(
                UUID(project_id), ProjectUpdate(configuration=config)
            )

            return {
                "success": True,
                "message": f"Created transition '{transition_name}'",
                "transition": {
                    "id": transition["id"],
                    "name": transition["name"],
                    "from_state": transition["fromState"],
                    "to_state": transition["toState"],
                },
            }

        elif name == "update_transition":
            project_id = arguments.get("project_id")
            transition_id = arguments.get("transition_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not transition_id:
                return {"success": False, "error": "Transition ID is required"}

            project = await client.get_project(UUID(project_id))
            config = project.configuration.copy()
            transitions = config.get("transitions", [])

            # Find and update the transition
            found = False
            for t in transitions:
                if t.get("id") == transition_id:
                    if "name" in arguments:
                        t["name"] = arguments["name"]
                    if "from_state" in arguments:
                        t["fromState"] = arguments["from_state"]
                    if "to_state" in arguments:
                        t["toState"] = arguments["to_state"]
                    if "workflows" in arguments:
                        t["processes"] = arguments["workflows"]
                    if "timeout" in arguments:
                        t["timeout"] = arguments["timeout"]
                    if "retry_count" in arguments:
                        t["retryCount"] = arguments["retry_count"]
                    found = True
                    break

            if not found:
                return {
                    "success": False,
                    "error": f"Transition not found: {transition_id}",
                }

            config["transitions"] = transitions
            await client.update_project(
                UUID(project_id), ProjectUpdate(configuration=config)
            )

            return {
                "success": True,
                "message": f"Updated transition {transition_id}",
            }

        elif name == "delete_transition":
            project_id = arguments.get("project_id")
            transition_id = arguments.get("transition_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not transition_id:
                return {"success": False, "error": "Transition ID is required"}

            project = await client.get_project(UUID(project_id))
            config = project.configuration.copy()
            transitions = config.get("transitions", [])

            original_count = len(transitions)
            config["transitions"] = [
                t for t in transitions if t.get("id") != transition_id
            ]

            if len(config["transitions"]) == original_count:
                return {
                    "success": False,
                    "error": f"Transition not found: {transition_id}",
                }

            await client.update_project(
                UUID(project_id), ProjectUpdate(configuration=config)
            )

            return {
                "success": True,
                "message": f"Deleted transition {transition_id}",
            }

        return {"error": f"Unknown transitions tool: {name}"}

    except Exception as e:
        logger.error(f"Transitions tool error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
