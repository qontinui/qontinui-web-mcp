"""Capture session tools for qontinui-web-mcp.

Capture sessions enable learning workflows from recorded user actions.
"""

import logging
from typing import Any

from mcp.types import Tool

from qontinui_web_mcp.client import QontinuiClient

logger = logging.getLogger(__name__)


CAPTURE_TOOLS = [
    Tool(
        name="create_capture_session",
        description=(
            "Create a new capture session to record user actions. "
            "Capture sessions are used to learn workflows from demonstrations. "
            "After creating a session, upload screenshots and actions, "
            "then complete the session to generate a workflow."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID to create session in",
                },
                "name": {
                    "type": "string",
                    "description": "Session name",
                },
                "description": {
                    "type": "string",
                    "description": "Optional session description",
                },
            },
            "required": ["project_id", "name"],
        },
    ),
    Tool(
        name="list_capture_sessions",
        description="List capture sessions for a project.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (capturing, uploading, analyzing, completed, failed)",
                    "enum": [
                        "capturing",
                        "uploading",
                        "analyzing",
                        "completed",
                        "failed",
                    ],
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of sessions to return",
                    "default": 50,
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="get_capture_session",
        description="Get details of a capture session including screenshots and actions.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Capture session UUID",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="upload_capture_screenshot",
        description=(
            "Upload a screenshot to a capture session. "
            "Screenshots document the UI state during the recording."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Capture session UUID",
                },
                "image_data": {
                    "type": "string",
                    "description": "Base64-encoded screenshot image",
                },
                "width": {
                    "type": "integer",
                    "description": "Image width in pixels",
                },
                "height": {
                    "type": "integer",
                    "description": "Image height in pixels",
                },
                "timestamp": {
                    "type": "string",
                    "description": "ISO timestamp when screenshot was taken",
                },
            },
            "required": ["session_id", "image_data", "width", "height"],
        },
    ),
    Tool(
        name="add_capture_action",
        description=(
            "Add a user action to a capture session. "
            "Actions include clicks, typing, key presses, and scrolls."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Capture session UUID",
                },
                "screenshot_id": {
                    "type": "string",
                    "description": "Screenshot UUID this action was performed on",
                },
                "action_type": {
                    "type": "string",
                    "description": "Type of action",
                    "enum": [
                        "click",
                        "double_click",
                        "right_click",
                        "type",
                        "key_press",
                        "scroll",
                    ],
                },
                "x": {
                    "type": "integer",
                    "description": "X coordinate (for click actions)",
                },
                "y": {
                    "type": "integer",
                    "description": "Y coordinate (for click actions)",
                },
                "text": {
                    "type": "string",
                    "description": "Text typed (for type actions)",
                },
                "key": {
                    "type": "string",
                    "description": "Key pressed (for key_press actions)",
                },
                "scroll_delta": {
                    "type": "integer",
                    "description": "Scroll amount (for scroll actions)",
                },
            },
            "required": ["session_id", "screenshot_id", "action_type"],
        },
    ),
    Tool(
        name="complete_capture_session",
        description=(
            "Mark a capture session as complete and ready for analysis. "
            "This triggers workflow generation from the recorded actions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Capture session UUID to complete",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="generate_workflow_from_capture",
        description=(
            "Generate a workflow from a completed capture session. "
            "Uses AI to analyze the recorded actions and create an automation workflow."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Capture session UUID",
                },
                "workflow_name": {
                    "type": "string",
                    "description": "Name for the generated workflow",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="list_learned_workflows",
        description="List workflows learned from capture sessions.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status",
                    "enum": ["draft", "reviewing", "approved", "rejected", "published"],
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="approve_learned_workflow",
        description=(
            "Approve a learned workflow and optionally publish it to the project. "
            "Publishing adds the workflow to the project configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "Learned workflow UUID",
                },
                "publish": {
                    "type": "boolean",
                    "description": "Whether to publish to project configuration",
                    "default": False,
                },
            },
            "required": ["workflow_id"],
        },
    ),
]


async def handle_capture_tool(
    name: str,
    arguments: dict[str, Any],
    client: QontinuiClient,
) -> dict[str, Any]:
    """Handle capture session tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Qontinui API client

    Returns:
        Tool result as dict
    """
    try:
        if name == "create_capture_session":
            project_id = arguments.get("project_id")
            session_name = arguments.get("name")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not session_name:
                return {"success": False, "error": "Session name is required"}

            result = await client._request(
                "POST",
                f"/api/v1/capture/projects/{project_id}/capture-sessions",
                json={
                    "name": session_name,
                    "description": arguments.get("description"),
                },
            )

            return {
                "success": True,
                "message": f"Created capture session '{session_name}'",
                "session": result,
            }

        elif name == "list_capture_sessions":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            params: dict[str, Any] = {"limit": arguments.get("limit", 50)}
            if arguments.get("status"):
                params["status"] = arguments["status"]

            result = await client._request(
                "GET",
                "/api/v1/capture/capture-sessions",
                params={"project_id": project_id, **params},
            )

            return {
                "success": True,
                "sessions": (
                    result if isinstance(result, list) else result.get("sessions", [])
                ),
            }

        elif name == "get_capture_session":
            session_id = arguments.get("session_id")
            if not session_id:
                return {"success": False, "error": "Session ID is required"}

            result = await client._request(
                "GET",
                f"/api/v1/capture/capture-sessions/{session_id}",
            )

            return {
                "success": True,
                "session": result,
            }

        elif name == "upload_capture_screenshot":
            session_id = arguments.get("session_id")
            image_data = arguments.get("image_data")
            width = arguments.get("width")
            height = arguments.get("height")

            if not session_id:
                return {"success": False, "error": "Session ID is required"}
            if not image_data:
                return {"success": False, "error": "Image data is required"}
            if not width or not height:
                return {"success": False, "error": "Width and height are required"}

            result = await client._request(
                "POST",
                f"/api/v1/capture/capture-sessions/{session_id}/screenshots",
                json={
                    "image_data": image_data,
                    "width": width,
                    "height": height,
                    "timestamp": arguments.get("timestamp"),
                },
            )

            return {
                "success": True,
                "message": "Screenshot uploaded",
                "screenshot": result,
            }

        elif name == "add_capture_action":
            session_id = arguments.get("session_id")
            screenshot_id = arguments.get("screenshot_id")
            action_type = arguments.get("action_type")

            if not session_id:
                return {"success": False, "error": "Session ID is required"}
            if not screenshot_id:
                return {"success": False, "error": "Screenshot ID is required"}
            if not action_type:
                return {"success": False, "error": "Action type is required"}

            action_data: dict[str, Any] = {
                "screenshot_id": screenshot_id,
                "action_type": action_type,
            }

            # Add optional fields based on action type
            if arguments.get("x") is not None:
                action_data["x"] = arguments["x"]
            if arguments.get("y") is not None:
                action_data["y"] = arguments["y"]
            if arguments.get("text"):
                action_data["text"] = arguments["text"]
            if arguments.get("key"):
                action_data["key"] = arguments["key"]
            if arguments.get("scroll_delta") is not None:
                action_data["scroll_delta"] = arguments["scroll_delta"]

            result = await client._request(
                "POST",
                f"/api/v1/capture/capture-sessions/{session_id}/actions",
                json=action_data,
            )

            return {
                "success": True,
                "message": f"Added {action_type} action",
                "action": result,
            }

        elif name == "complete_capture_session":
            session_id = arguments.get("session_id")
            if not session_id:
                return {"success": False, "error": "Session ID is required"}

            result = await client._request(
                "POST",
                f"/api/v1/capture/capture-sessions/{session_id}/complete",
            )

            return {
                "success": True,
                "message": "Capture session marked as complete",
                "session": result,
            }

        elif name == "generate_workflow_from_capture":
            session_id = arguments.get("session_id")
            if not session_id:
                return {"success": False, "error": "Session ID is required"}

            result = await client._request(
                "POST",
                f"/api/v1/capture/capture-sessions/{session_id}/learned-workflows",
                json={
                    "name": arguments.get("workflow_name"),
                },
            )

            return {
                "success": True,
                "message": "Workflow generation started",
                "learned_workflow": result,
            }

        elif name == "list_learned_workflows":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            params: dict[str, Any] = {}
            if arguments.get("status"):
                params["status"] = arguments["status"]

            result = await client._request(
                "GET",
                f"/api/v1/capture/projects/{project_id}/learned-workflows",
                params=params,
            )

            return {
                "success": True,
                "workflows": (
                    result if isinstance(result, list) else result.get("workflows", [])
                ),
            }

        elif name == "approve_learned_workflow":
            workflow_id = arguments.get("workflow_id")
            if not workflow_id:
                return {"success": False, "error": "Workflow ID is required"}

            result = await client._request(
                "POST",
                f"/api/v1/capture/learned-workflows/{workflow_id}/approve",
                json={
                    "publish": arguments.get("publish", False),
                },
            )

            return {
                "success": True,
                "message": "Workflow approved",
                "workflow": result,
            }

        return {"error": f"Unknown capture tool: {name}"}

    except Exception as e:
        logger.error(f"Capture tool error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
