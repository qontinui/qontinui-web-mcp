"""HTTP client for Qontinui web backend API."""

import logging
from typing import Any, cast
from uuid import UUID

import httpx

from qontinui_web_mcp.types import (
    AuthTokens,
    ExportConfiguration,
    Project,
    ProjectCreate,
    ProjectUpdate,
    User,
)
from qontinui_web_mcp.utils.config import Settings, get_settings

logger = logging.getLogger(__name__)


class QontinuiClientError(Exception):
    """Base exception for API client errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(QontinuiClientError):
    """Authentication failed."""

    pass


class NotFoundError(QontinuiClientError):
    """Resource not found."""

    pass


class ValidationError(QontinuiClientError):
    """Validation error from API."""

    pass


class QontinuiClient:
    """HTTP client for Qontinui web backend.

    Handles authentication and provides methods for all API endpoints.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._access_token: str | None = self.settings.access_token
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        """Get the API base URL."""
        return self.settings.api_url.rstrip("/")

    @property
    def is_authenticated(self) -> bool:
        """Check if client has valid authentication."""
        return bool(self._access_token)

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.settings.api_timeout,
                headers=self._get_headers(),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /api/v1/projects)
            json: JSON body
            params: Query parameters
            data: Form data

        Returns:
            Response JSON as dict

        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If resource not found
            ValidationError: If validation fails
            QontinuiClientError: For other API errors
        """
        client = await self._get_client()

        # Update headers in case token changed
        client.headers.update(self._get_headers())

        try:
            response = await client.request(
                method,
                path,
                json=json,
                params=params,
                data=data,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please login again.",
                    status_code=401,
                )

            if response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found: {path}",
                    status_code=404,
                )

            if response.status_code == 422:
                detail = response.json().get("detail", "Validation error")
                raise ValidationError(
                    f"Validation error: {detail}",
                    status_code=422,
                )

            if response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                raise QontinuiClientError(
                    f"API error ({response.status_code}): {detail}",
                    status_code=response.status_code,
                )

            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}

            result: dict[str, Any] = response.json()
            return result

        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            raise QontinuiClientError(f"Request failed: {e}") from e

    # ========================================================================
    # Authentication
    # ========================================================================

    async def login(self, email: str, password: str) -> AuthTokens:
        """Authenticate with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            AuthTokens with access_token
        """
        # fastapi-users expects form data for login
        client = await self._get_client()
        response = await client.post(
            "/api/v1/auth/jwt/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            try:
                detail = response.json().get("detail", "Login failed")
            except Exception:
                detail = response.text
            raise AuthenticationError(f"Login failed: {detail}", status_code=401)

        tokens = AuthTokens(**response.json())
        self._access_token = tokens.access_token
        return tokens

    async def login_with_settings(self) -> AuthTokens:
        """Login using credentials from settings."""
        if not self.settings.has_credentials:
            raise AuthenticationError(
                "No credentials configured. Set QONTINUI_EMAIL and QONTINUI_PASSWORD."
            )
        return await self.login(
            self.settings.email,  # type: ignore
            self.settings.password,  # type: ignore
        )

    async def get_current_user(self) -> User:
        """Get the currently authenticated user."""
        data = await self._request("GET", "/api/v1/auth/users/me")
        return User(**data)

    def logout(self) -> None:
        """Clear stored authentication."""
        self._access_token = None

    # ========================================================================
    # Projects
    # ========================================================================

    async def list_projects(
        self,
        *,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """List all accessible projects.

        Args:
            organization_id: Filter by organization
            skip: Pagination offset
            limit: Maximum number of results

        Returns:
            List of projects
        """
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if organization_id:
            params["organization_id"] = str(organization_id)

        response = await self._request("GET", "/api/v1/projects", params=params)
        # The API returns a list of projects, cast for type safety
        data = cast(list[dict[str, Any]], response)
        return [Project(**p) for p in data]

    async def create_project(self, project: ProjectCreate) -> Project:
        """Create a new project.

        Args:
            project: Project creation data

        Returns:
            Created project
        """
        data = await self._request(
            "POST",
            "/api/v1/projects",
            json=project.model_dump(exclude_none=True),
        )
        return Project(**data)

    async def get_project(self, project_id: UUID) -> Project:
        """Get a project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project details
        """
        data = await self._request("GET", f"/api/v1/projects/{project_id}")
        return Project(**data)

    async def update_project(self, project_id: UUID, update: ProjectUpdate) -> Project:
        """Update a project.

        Args:
            project_id: Project UUID
            update: Fields to update

        Returns:
            Updated project
        """
        data = await self._request(
            "PUT",
            f"/api/v1/projects/{project_id}",
            json=update.model_dump(exclude_none=True),
        )
        return Project(**data)

    async def delete_project(self, project_id: UUID) -> None:
        """Delete a project.

        Args:
            project_id: Project UUID
        """
        await self._request("DELETE", f"/api/v1/projects/{project_id}")

    # ========================================================================
    # Configuration Export/Import
    # ========================================================================

    async def export_configuration(self, project_id: UUID) -> ExportConfiguration:
        """Export project configuration.

        Args:
            project_id: Project UUID

        Returns:
            Complete configuration including workflows, states, images
        """
        data = await self._request("GET", f"/api/v1/projects/{project_id}/export")
        return ExportConfiguration(**data)

    async def import_configuration(
        self,
        project_id: UUID,
        configuration: ExportConfiguration,
        *,
        merge: bool = False,
    ) -> dict[str, Any]:
        """Import configuration into a project.

        Args:
            project_id: Project UUID
            configuration: Configuration to import
            merge: If True, merge with existing; if False, replace

        Returns:
            Import result with success status
        """
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/import",
            json={
                "configuration": configuration.model_dump(),
                "merge": merge,
            },
        )

    async def validate_configuration(
        self, configuration: ExportConfiguration
    ) -> dict[str, Any]:
        """Validate configuration without importing.

        Args:
            configuration: Configuration to validate

        Returns:
            Validation result with valid flag, errors, warnings
        """
        return await self._request(
            "POST",
            "/api/v1/projects/validate",
            json=configuration.model_dump(),
        )

    # ========================================================================
    # Workflows (via configuration)
    # ========================================================================

    async def get_workflows(self, project_id: UUID) -> list[dict[str, Any]]:
        """Get all workflows in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of workflow definitions
        """
        project = await self.get_project(project_id)
        workflows: list[dict[str, Any]] = project.configuration.get("workflows", [])
        return workflows

    async def add_workflow(self, project_id: UUID, workflow: dict[str, Any]) -> Project:
        """Add a workflow to a project.

        Args:
            project_id: Project UUID
            workflow: Workflow definition

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        workflows = config.get("workflows", [])
        workflows.append(workflow)
        config["workflows"] = workflows

        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    async def update_workflow(
        self, project_id: UUID, workflow_id: str, workflow: dict[str, Any]
    ) -> Project:
        """Update a workflow in a project.

        Args:
            project_id: Project UUID
            workflow_id: Workflow ID
            workflow: Updated workflow definition

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        workflows = config.get("workflows", [])

        for i, w in enumerate(workflows):
            if w.get("id") == workflow_id:
                workflows[i] = workflow
                break
        else:
            raise NotFoundError(f"Workflow not found: {workflow_id}")

        config["workflows"] = workflows
        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    async def delete_workflow(self, project_id: UUID, workflow_id: str) -> Project:
        """Delete a workflow from a project.

        Args:
            project_id: Project UUID
            workflow_id: Workflow ID

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        workflows = config.get("workflows", [])

        config["workflows"] = [w for w in workflows if w.get("id") != workflow_id]
        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    # ========================================================================
    # States (via configuration)
    # ========================================================================

    async def get_states(self, project_id: UUID) -> list[dict[str, Any]]:
        """Get all states in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of state definitions
        """
        project = await self.get_project(project_id)
        states: list[dict[str, Any]] = project.configuration.get("states", [])
        return states

    async def add_state(self, project_id: UUID, state: dict[str, Any]) -> Project:
        """Add a state to a project.

        Args:
            project_id: Project UUID
            state: State definition

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        states = config.get("states", [])
        states.append(state)
        config["states"] = states

        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    async def update_state(
        self, project_id: UUID, state_id: str, state: dict[str, Any]
    ) -> Project:
        """Update a state in a project.

        Args:
            project_id: Project UUID
            state_id: State ID
            state: Updated state definition

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        states = config.get("states", [])

        for i, s in enumerate(states):
            if s.get("id") == state_id:
                states[i] = state
                break
        else:
            raise NotFoundError(f"State not found: {state_id}")

        config["states"] = states
        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    async def delete_state(self, project_id: UUID, state_id: str) -> Project:
        """Delete a state from a project.

        Args:
            project_id: Project UUID
            state_id: State ID

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        states = config.get("states", [])

        config["states"] = [s for s in states if s.get("id") != state_id]
        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    # ========================================================================
    # Images (via configuration)
    # ========================================================================

    async def get_images(self, project_id: UUID) -> list[dict[str, Any]]:
        """Get all images in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of image definitions
        """
        project = await self.get_project(project_id)
        images: list[dict[str, Any]] = project.configuration.get("images", [])
        return images

    async def add_image(self, project_id: UUID, image: dict[str, Any]) -> Project:
        """Add an image to a project.

        Args:
            project_id: Project UUID
            image: Image definition with base64 data

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        images = config.get("images", [])
        images.append(image)
        config["images"] = images

        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    async def delete_image(self, project_id: UUID, image_id: str) -> Project:
        """Delete an image from a project.

        Args:
            project_id: Project UUID
            image_id: Image ID

        Returns:
            Updated project
        """
        project = await self.get_project(project_id)
        config = project.configuration.copy()
        images = config.get("images", [])

        config["images"] = [i for i in images if i.get("id") != image_id]
        return await self.update_project(
            project_id, ProjectUpdate(configuration=config)
        )

    # ========================================================================
    # Execution
    # ========================================================================

    async def execute_workflow(
        self,
        project_id: UUID,
        workflow_id: str,
        *,
        runner_id: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a workflow.

        Args:
            project_id: Project UUID
            workflow_id: Workflow ID to execute
            runner_id: Optional runner device ID
            variables: Optional runtime variables

        Returns:
            Automation session info
        """
        return await self._request(
            "POST",
            f"/api/v1/automation/projects/{project_id}/execute",
            json={
                "workflow_id": workflow_id,
                "runner_id": runner_id,
                "variables": variables or {},
            },
        )

    async def get_execution_status(self, session_id: UUID) -> dict[str, Any]:
        """Get execution status.

        Args:
            session_id: Automation session UUID

        Returns:
            Session status with logs and screenshots
        """
        return await self._request("GET", f"/api/v1/automation/sessions/{session_id}")

    async def cancel_execution(self, session_id: UUID) -> dict[str, Any]:
        """Cancel a running execution.

        Args:
            session_id: Automation session UUID

        Returns:
            Cancellation result
        """
        return await self._request(
            "POST", f"/api/v1/automation/sessions/{session_id}/cancel"
        )
