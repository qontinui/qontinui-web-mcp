"""Project management tools for qontinui-web-mcp."""

import logging
from typing import Any
from uuid import UUID

from mcp.types import Tool

from qontinui_web_mcp.client import QontinuiClient
from qontinui_web_mcp.types import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


PROJECTS_TOOLS = [
    Tool(
        name="list_projects",
        description=(
            "List all projects accessible to the authenticated user. "
            "Returns project metadata including ID, name, description, and timestamps."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "organization_id": {
                    "type": "string",
                    "description": "Optional organization UUID to filter by",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of projects to return (default: 100)",
                    "default": 100,
                },
            },
        },
    ),
    Tool(
        name="create_project",
        description=(
            "Create a new Qontinui project. "
            "Projects contain workflows, states, images, and automation configuration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name (required)",
                },
                "description": {
                    "type": "string",
                    "description": "Optional project description",
                },
                "organization_id": {
                    "type": "string",
                    "description": "Optional organization UUID to create project in",
                },
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="get_project",
        description=(
            "Get detailed information about a project including its full configuration. "
            "Use this to inspect workflows, states, images, and settings."
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
        name="update_project",
        description=(
            "Update a project's metadata or configuration. "
            "Can update name, description, or the full configuration object."
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
                    "description": "New project name",
                },
                "description": {
                    "type": "string",
                    "description": "New project description",
                },
                "configuration": {
                    "type": "object",
                    "description": "Full configuration object to replace existing",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="delete_project",
        description=(
            "Delete a project and all its contents. " "This action is irreversible."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project UUID to delete",
                },
            },
            "required": ["project_id"],
        },
    ),
]


async def handle_projects_tool(
    name: str,
    arguments: dict[str, Any],
    client: QontinuiClient,
) -> dict[str, Any]:
    """Handle project management tool calls.

    Args:
        name: Tool name
        arguments: Tool arguments
        client: Qontinui API client

    Returns:
        Tool result as dict
    """
    try:
        if name == "list_projects":
            org_id = arguments.get("organization_id")
            limit = arguments.get("limit", 100)

            projects = await client.list_projects(
                organization_id=UUID(org_id) if org_id else None,
                limit=limit,
            )

            return {
                "success": True,
                "count": len(projects),
                "projects": [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "description": p.description,
                        "version": p.version,
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat(),
                        "workflow_count": len(p.configuration.get("workflows", [])),
                        "state_count": len(p.configuration.get("states", [])),
                    }
                    for p in projects
                ],
            }

        elif name == "create_project":
            project_name = arguments.get("name")
            if not project_name:
                return {"success": False, "error": "Project name is required"}

            org_id = arguments.get("organization_id")
            project = await client.create_project(
                ProjectCreate(
                    name=project_name,
                    description=arguments.get("description"),
                    organization_id=UUID(org_id) if org_id else None,
                )
            )

            return {
                "success": True,
                "message": f"Created project '{project.name}'",
                "project": {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "created_at": project.created_at.isoformat(),
                },
            }

        elif name == "get_project":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            project = await client.get_project(UUID(project_id))

            return {
                "success": True,
                "project": {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "version": project.version,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                    "configuration": project.configuration,
                },
            }

        elif name == "update_project":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            update = ProjectUpdate(
                name=arguments.get("name"),
                description=arguments.get("description"),
                configuration=arguments.get("configuration"),
            )

            project = await client.update_project(UUID(project_id), update)

            return {
                "success": True,
                "message": f"Updated project '{project.name}'",
                "project": {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "version": project.version,
                    "updated_at": project.updated_at.isoformat(),
                },
            }

        elif name == "delete_project":
            project_id = arguments.get("project_id")
            if not project_id:
                return {"success": False, "error": "Project ID is required"}

            await client.delete_project(UUID(project_id))

            return {
                "success": True,
                "message": f"Deleted project {project_id}",
            }

        return {"error": f"Unknown projects tool: {name}"}

    except Exception as e:
        logger.error(f"Projects tool error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
