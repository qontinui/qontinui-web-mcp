"""Pydantic models for qontinui-web-mcp.

These models mirror the schemas from qontinui-web backend for type safety.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Authentication
# ============================================================================


class AuthCredentials(BaseModel):
    """Credentials for authentication."""

    email: str
    password: str


class AuthTokens(BaseModel):
    """JWT tokens from authentication."""

    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    """Authenticated user info."""

    id: UUID
    email: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


# ============================================================================
# Projects
# ============================================================================


class ProjectCreate(BaseModel):
    """Schema for creating a project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    organization_id: UUID | None = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = None
    description: str | None = None
    configuration: dict[str, Any] | None = None


class Project(BaseModel):
    """Project response model."""

    id: UUID
    name: str
    description: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    owner_id: UUID
    organization_id: UUID | None = None
    is_public: bool = False
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Actions & Workflows
# ============================================================================


class ActionType(str, Enum):
    """Types of automation actions."""

    # Mouse actions
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    SCROLL = "scroll"
    HOVER = "hover"
    MOVE = "move"

    # Keyboard actions
    TYPE = "type"
    KEY_PRESS = "key_press"
    KEY_COMBO = "key_combo"

    # Vision actions
    FIND = "find"
    FIND_ALL = "find_all"
    WAIT_FOR = "wait_for"
    WAIT_VANISH = "wait_vanish"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_NOT_VISIBLE = "assert_not_visible"

    # Control flow
    CONDITION = "condition"
    LOOP = "loop"
    DELAY = "delay"
    RUN_WORKFLOW = "run_workflow"


class ActionConfig(BaseModel):
    """Configuration for an action."""

    type: ActionType
    description: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ConnectionTarget(BaseModel):
    """Target for workflow connections."""

    action: str  # Action ID
    type: str = "main"  # main, error
    index: int = 0


class WorkflowStep(BaseModel):
    """A step in a workflow."""

    id: str
    type: ActionType
    name: str
    config: dict[str, Any] = Field(default_factory=dict)
    base: dict[str, Any] = Field(default_factory=dict)
    execution: dict[str, Any] = Field(default_factory=dict)
    position: list[float] = Field(default_factory=lambda: [0.0, 0.0])


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""

    id: str
    name: str
    version: str = "1.0.0"
    format: str = "graph"
    actions: list[WorkflowStep] = Field(default_factory=list)
    connections: dict[str, dict[str, list[list[ConnectionTarget]]]] = Field(
        default_factory=dict
    )
    visibility: str = "public"
    variables: dict[str, dict[str, Any]] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# States & Transitions
# ============================================================================


class ImageDefinition(BaseModel):
    """Image used for pattern matching."""

    id: str
    name: str
    data: str  # Base64 encoded
    format: str = "png"
    width: int | None = None
    height: int | None = None
    hash: str | None = None


class StateDefinition(BaseModel):
    """UI state definition."""

    id: str
    name: str
    description: str | None = None
    identifyingImages: list[dict[str, Any]] = Field(default_factory=list)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    isInitial: bool = False
    isFinal: bool = False


class TransitionDefinition(BaseModel):
    """State transition definition."""

    id: str
    type: str = "action"
    name: str
    processes: list[str] = Field(default_factory=list)  # Workflow IDs
    fromState: str
    toState: str
    staysVisible: bool = False
    activateStates: list[str] = Field(default_factory=list)
    deactivateStates: list[str] = Field(default_factory=list)
    timeout: int = 10000
    retryCount: int = 3


# ============================================================================
# Export/Import Configuration
# ============================================================================


class ExportConfiguration(BaseModel):
    """Complete project configuration for export/import."""

    version: str = "1.0.0"
    metadata: dict[str, Any] = Field(default_factory=dict)
    images: list[ImageDefinition] = Field(default_factory=list)
    workflows: list[WorkflowDefinition] = Field(default_factory=list)
    states: list[StateDefinition] = Field(default_factory=list)
    transitions: list[TransitionDefinition] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
