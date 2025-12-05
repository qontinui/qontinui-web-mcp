"""Configuration management tools for qontinui-web-mcp.

Handles workflows, states, images, and import/export.
"""

import logging
import uuid
from typing import Any
from uuid import UUID

from mcp.types import Tool

from qontinui_web_mcp.client import QontinuiClient
from qontinui_web_mcp.types import ExportConfiguration

logger = logging.getLogger(__name__)


CONFIGURATION_TOOLS = [
    # Export/Import
    Tool(
        name="export_configuration",
        description=(
            "Export a project's complete configuration as JSON. "
            "Includes all workflows, states, transitions, images, and settings. "
            "Use this for backup or to copy configuration to another project."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID to export",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="import_configuration",
        description=(
            "Import configuration into a project. "
            "Can either replace existing configuration or merge with it."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID to import into",
                },
                "configuration": {
                    "type": "object",
                    "description": "Configuration object to import",
                },
                "merge": {
                    "type": "boolean",
                    "description": "If true, merge with existing; if false, replace",
                    "default": False,
                },
            },
            "required": ["project_id", "configuration"],
        },
    ),
    Tool(
        name="validate_configuration",
        description=(
            "Validate a configuration without importing. "
            "Returns validation errors and warnings."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "configuration": {
                    "type": "object",
                    "description": "Configuration object to validate",
                },
            },
            "required": ["configuration"],
        },
    ),
    # Workflows
    Tool(
        name="list_workflows",
        description="List all workflows in a project.",
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
        name="create_workflow",
        description=(
            "Create a new workflow in a project. "
            "A workflow is a sequence of actions (click, type, find, etc.) "
            "connected in a graph structure."
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
                    "description": "Workflow name",
                },
                "actions": {
                    "type": "array",
                    "description": "List of action definitions",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"type": "string"},
                            "name": {"type": "string"},
                            "config": {"type": "object"},
                        },
                    },
                },
                "connections": {
                    "type": "object",
                    "description": "Connection map between actions",
                },
            },
            "required": ["project_id", "name"],
        },
    ),
    Tool(
        name="update_workflow",
        description="Update an existing workflow.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID to update",
                },
                "name": {
                    "type": "string",
                    "description": "New workflow name",
                },
                "actions": {
                    "type": "array",
                    "description": "Updated action definitions",
                },
                "connections": {
                    "type": "object",
                    "description": "Updated connection map",
                },
            },
            "required": ["project_id", "workflow_id"],
        },
    ),
    Tool(
        name="delete_workflow",
        description="Delete a workflow from a project.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID to delete",
                },
            },
            "required": ["project_id", "workflow_id"],
        },
    ),
    # States
    Tool(
        name="list_states",
        description="List all UI states defined in a project.",
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
        name="create_state",
        description=(
            "Create a UI state definition. "
            "States represent recognizable UI screens identified by pattern images."
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
                    "description": "State name",
                },
                "description": {
                    "type": "string",
                    "description": "State description",
                },
                "identifying_images": {
                    "type": "array",
                    "description": "Image IDs used to identify this state",
                    "items": {
                        "type": "object",
                        "properties": {
                            "imageId": {"type": "string"},
                            "threshold": {"type": "number"},
                            "required": {"type": "boolean"},
                        },
                    },
                },
                "is_initial": {
                    "type": "boolean",
                    "description": "Whether this is an initial/start state",
                    "default": False,
                },
                "is_final": {
                    "type": "boolean",
                    "description": "Whether this is a final/end state",
                    "default": False,
                },
            },
            "required": ["project_id", "name"],
        },
    ),
    Tool(
        name="update_state",
        description="Update a UI state definition.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "state_id": {
                    "type": "string",
                    "description": "State ID to update",
                },
                "name": {
                    "type": "string",
                    "description": "New state name",
                },
                "description": {
                    "type": "string",
                    "description": "New description",
                },
                "identifying_images": {
                    "type": "array",
                    "description": "Updated identifying images",
                },
                "is_initial": {
                    "type": "boolean",
                },
                "is_final": {
                    "type": "boolean",
                },
            },
            "required": ["project_id", "state_id"],
        },
    ),
    Tool(
        name="delete_state",
        description="Delete a UI state from a project.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "state_id": {
                    "type": "string",
                    "description": "State ID to delete",
                },
            },
            "required": ["project_id", "state_id"],
        },
    ),
    # Images
    Tool(
        name="list_images",
        description="List all pattern images in a project.",
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
        name="add_image",
        description=(
            "Add a pattern image to a project. "
            "Images are used for visual pattern matching in states and actions."
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
                    "description": "Image name",
                },
                "data": {
                    "type": "string",
                    "description": "Base64-encoded image data",
                },
                "format": {
                    "type": "string",
                    "description": "Image format (png, jpg)",
                    "default": "png",
                },
            },
            "required": ["project_id", "name", "data"],
        },
    ),
    Tool(
        name="delete_image",
        description="Delete a pattern image from a project.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID",
                },
                "image_id": {
                    "type": "string",
                    "description": "Image ID to delete",
                },
            },
            "required": ["project_id", "image_id"],
        },
    ),
]


async def handle_configuration_tool(
    name: str,
    arguments: dict[str, Any],
    client: QontinuiClient,
) -> dict[str, Any]:
    """Handle configuration management tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Qontinui API client

    Returns:
        Tool result as dict
    """
    try:
        # Export/Import
        if name == "export_configuration":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            config = await client.export_configuration(UUID(project_id))
            return {
                "success": True,
                "configuration": config.model_dump(),
            }

        elif name == "import_configuration":
            project_id = arguments.get("project_id")
            config_data = arguments.get("configuration")
            merge = arguments.get("merge", False)

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not config_data:
                return {"success": False, "error": "Configuration is required"}

            config = ExportConfiguration(**config_data)
            result = await client.import_configuration(
                UUID(project_id), config, merge=merge
            )
            return {
                "success": True,
                "result": result,
            }

        elif name == "validate_configuration":
            config_data = arguments.get("configuration")
            if not config_data:
                return {"success": False, "error": "Configuration is required"}

            config = ExportConfiguration(**config_data)
            result = await client.validate_configuration(config)
            return result

        # Workflows
        elif name == "list_workflows":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            workflows = await client.get_workflows(UUID(project_id))
            return {
                "success": True,
                "count": len(workflows),
                "workflows": [
                    {
                        "id": w.get("id"),
                        "name": w.get("name"),
                        "action_count": len(w.get("actions", [])),
                    }
                    for w in workflows
                ],
            }

        elif name == "create_workflow":
            project_id = arguments.get("project_id")
            workflow_name = arguments.get("name")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not workflow_name:
                return {"success": False, "error": "Workflow name is required"}

            workflow = {
                "id": f"workflow-{uuid.uuid4().hex[:8]}",
                "name": workflow_name,
                "version": "1.0.0",
                "format": "graph",
                "actions": arguments.get("actions", []),
                "connections": arguments.get("connections", {}),
                "visibility": "public",
                "variables": {},
                "settings": {},
                "metadata": {},
            }

            await client.add_workflow(UUID(project_id), workflow)
            return {
                "success": True,
                "message": f"Created workflow '{workflow_name}'",
                "workflow": {
                    "id": workflow["id"],
                    "name": workflow["name"],
                },
            }

        elif name == "update_workflow":
            project_id = arguments.get("project_id")
            workflow_id = arguments.get("workflow_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not workflow_id:
                return {"success": False, "error": "Workflow ID is required"}

            # Get existing workflow
            workflows = await client.get_workflows(UUID(project_id))
            existing = next((w for w in workflows if w.get("id") == workflow_id), None)
            if not existing:
                return {"success": False, "error": f"Workflow not found: {workflow_id}"}

            # Update fields
            if "name" in arguments:
                existing["name"] = arguments["name"]
            if "actions" in arguments:
                existing["actions"] = arguments["actions"]
            if "connections" in arguments:
                existing["connections"] = arguments["connections"]

            await client.update_workflow(UUID(project_id), workflow_id, existing)
            return {
                "success": True,
                "message": f"Updated workflow '{existing['name']}'",
            }

        elif name == "delete_workflow":
            project_id = arguments.get("project_id")
            workflow_id = arguments.get("workflow_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not workflow_id:
                return {"success": False, "error": "Workflow ID is required"}

            await client.delete_workflow(UUID(project_id), workflow_id)
            return {
                "success": True,
                "message": f"Deleted workflow {workflow_id}",
            }

        # States
        elif name == "list_states":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            states = await client.get_states(UUID(project_id))
            return {
                "success": True,
                "count": len(states),
                "states": [
                    {
                        "id": s.get("id"),
                        "name": s.get("name"),
                        "description": s.get("description"),
                        "is_initial": s.get("isInitial", False),
                        "is_final": s.get("isFinal", False),
                        "image_count": len(s.get("identifyingImages", [])),
                    }
                    for s in states
                ],
            }

        elif name == "create_state":
            project_id = arguments.get("project_id")
            state_name = arguments.get("name")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not state_name:
                return {"success": False, "error": "State name is required"}

            state = {
                "id": f"state-{uuid.uuid4().hex[:8]}",
                "name": state_name,
                "description": arguments.get("description"),
                "identifyingImages": arguments.get("identifying_images", []),
                "position": {"x": 0.0, "y": 0.0},
                "isInitial": arguments.get("is_initial", False),
                "isFinal": arguments.get("is_final", False),
            }

            await client.add_state(UUID(project_id), state)
            return {
                "success": True,
                "message": f"Created state '{state_name}'",
                "state": {
                    "id": state["id"],
                    "name": state["name"],
                },
            }

        elif name == "update_state":
            project_id = arguments.get("project_id")
            state_id = arguments.get("state_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not state_id:
                return {"success": False, "error": "State ID is required"}

            # Get existing state
            states = await client.get_states(UUID(project_id))
            existing = next((s for s in states if s.get("id") == state_id), None)
            if not existing:
                return {"success": False, "error": f"State not found: {state_id}"}

            # Update fields
            if "name" in arguments:
                existing["name"] = arguments["name"]
            if "description" in arguments:
                existing["description"] = arguments["description"]
            if "identifying_images" in arguments:
                existing["identifyingImages"] = arguments["identifying_images"]
            if "is_initial" in arguments:
                existing["isInitial"] = arguments["is_initial"]
            if "is_final" in arguments:
                existing["isFinal"] = arguments["is_final"]

            await client.update_state(UUID(project_id), state_id, existing)
            return {
                "success": True,
                "message": f"Updated state '{existing['name']}'",
            }

        elif name == "delete_state":
            project_id = arguments.get("project_id")
            state_id = arguments.get("state_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not state_id:
                return {"success": False, "error": "State ID is required"}

            await client.delete_state(UUID(project_id), state_id)
            return {
                "success": True,
                "message": f"Deleted state {state_id}",
            }

        # Images
        elif name == "list_images":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            images = await client.get_images(UUID(project_id))
            return {
                "success": True,
                "count": len(images),
                "images": [
                    {
                        "id": i.get("id"),
                        "name": i.get("name"),
                        "format": i.get("format"),
                        "width": i.get("width"),
                        "height": i.get("height"),
                    }
                    for i in images
                ],
            }

        elif name == "add_image":
            project_id = arguments.get("project_id")
            image_name = arguments.get("name")
            image_data = arguments.get("data")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not image_name:
                return {"success": False, "error": "Image name is required"}
            if not image_data:
                return {"success": False, "error": "Image data is required"}

            image = {
                "id": f"img-{uuid.uuid4().hex[:8]}",
                "name": image_name,
                "data": image_data,
                "format": arguments.get("format", "png"),
            }

            await client.add_image(UUID(project_id), image)
            return {
                "success": True,
                "message": f"Added image '{image_name}'",
                "image": {
                    "id": image["id"],
                    "name": image["name"],
                },
            }

        elif name == "delete_image":
            project_id = arguments.get("project_id")
            image_id = arguments.get("image_id")

            if not project_id:
                return {"success": False, "error": "Project ID is required"}
            if not image_id:
                return {"success": False, "error": "Image ID is required"}

            await client.delete_image(UUID(project_id), image_id)
            return {
                "success": True,
                "message": f"Deleted image {image_id}",
            }

        return {"error": f"Unknown configuration tool: {name}"}

    except Exception as e:
        logger.error(f"Configuration tool error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
