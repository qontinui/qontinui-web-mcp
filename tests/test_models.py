"""Tests for Pydantic models."""

from datetime import datetime
from uuid import UUID

from qontinui_web_mcp.types import (
    ActionConfig,
    ActionType,
    AuthCredentials,
    AuthTokens,
    ConnectionTarget,
    ExportConfiguration,
    ImageDefinition,
    Project,
    ProjectCreate,
    ProjectUpdate,
    StateDefinition,
    TransitionDefinition,
    User,
    WorkflowDefinition,
    WorkflowStep,
)


class TestAuthModels:
    """Tests for authentication models."""

    def test_auth_credentials(self) -> None:
        """Test AuthCredentials model."""
        creds = AuthCredentials(email="test@example.com", password="password")
        assert creds.email == "test@example.com"
        assert creds.password == "password"

    def test_auth_tokens(self) -> None:
        """Test AuthTokens model."""
        tokens = AuthTokens(access_token="abc123")
        assert tokens.access_token == "abc123"
        assert tokens.token_type == "bearer"

    def test_user_model(self) -> None:
        """Test User model."""
        user = User(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            email="test@example.com",
        )
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False


class TestProjectModels:
    """Tests for project models."""

    def test_project_create(self) -> None:
        """Test ProjectCreate model."""
        project = ProjectCreate(name="Test Project", description="A test")
        assert project.name == "Test Project"
        assert project.description == "A test"

    def test_project_create_minimal(self) -> None:
        """Test ProjectCreate with minimal fields."""
        project = ProjectCreate(name="Test")
        assert project.name == "Test"
        assert project.description is None

    def test_project_update(self) -> None:
        """Test ProjectUpdate model."""
        update = ProjectUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.configuration is None

    def test_project_model(self) -> None:
        """Test Project model."""
        project = Project(
            id=UUID("12345678-1234-1234-1234-123456789012"),
            name="Test Project",
            version=1,
            owner_id=UUID("12345678-1234-1234-1234-123456789012"),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert project.name == "Test Project"
        assert project.configuration == {}


class TestActionModels:
    """Tests for action and workflow models."""

    def test_action_type_enum(self) -> None:
        """Test ActionType enum values."""
        assert ActionType.CLICK.value == "click"
        assert ActionType.TYPE.value == "type"
        assert ActionType.FIND.value == "find"
        assert ActionType.WAIT_FOR.value == "wait_for"

    def test_action_config(self) -> None:
        """Test ActionConfig model."""
        config = ActionConfig(
            type=ActionType.CLICK,
            description="Click the button",
            options={"threshold": 0.9},
        )
        assert config.type == ActionType.CLICK
        assert config.options["threshold"] == 0.9

    def test_workflow_step(self) -> None:
        """Test WorkflowStep model."""
        step = WorkflowStep(
            id="step-1",
            type=ActionType.CLICK,
            name="Click Login",
            config={"imageId": "img-1"},
        )
        assert step.id == "step-1"
        assert step.type == ActionType.CLICK

    def test_connection_target(self) -> None:
        """Test ConnectionTarget model."""
        target = ConnectionTarget(action="step-2", type="main", index=0)
        assert target.action == "step-2"
        assert target.type == "main"

    def test_workflow_definition(self) -> None:
        """Test WorkflowDefinition model."""
        workflow = WorkflowDefinition(
            id="wf-1",
            name="Login Workflow",
            actions=[
                WorkflowStep(
                    id="step-1",
                    type=ActionType.CLICK,
                    name="Click Login",
                )
            ],
        )
        assert workflow.id == "wf-1"
        assert len(workflow.actions) == 1


class TestStateModels:
    """Tests for state and transition models."""

    def test_image_definition(self) -> None:
        """Test ImageDefinition model."""
        image = ImageDefinition(
            id="img-1",
            name="Login Button",
            data="base64data",
            format="png",
        )
        assert image.id == "img-1"
        assert image.format == "png"

    def test_state_definition(self) -> None:
        """Test StateDefinition model."""
        state = StateDefinition(
            id="state-1",
            name="Login Screen",
            isInitial=True,
        )
        assert state.id == "state-1"
        assert state.isInitial is True
        assert state.isFinal is False

    def test_transition_definition(self) -> None:
        """Test TransitionDefinition model."""
        transition = TransitionDefinition(
            id="trans-1",
            name="Login",
            fromState="state-1",
            toState="state-2",
            processes=["wf-1"],
        )
        assert transition.id == "trans-1"
        assert transition.fromState == "state-1"
        assert transition.toState == "state-2"


class TestExportConfiguration:
    """Tests for export configuration model."""

    def test_export_configuration_empty(self) -> None:
        """Test empty ExportConfiguration."""
        config = ExportConfiguration()
        assert config.version == "1.0.0"
        assert config.workflows == []
        assert config.states == []
        assert config.images == []

    def test_export_configuration_full(self) -> None:
        """Test full ExportConfiguration."""
        config = ExportConfiguration(
            version="2.0.0",
            metadata={"name": "Test Project"},
            images=[ImageDefinition(id="img-1", name="Button", data="base64")],
            workflows=[WorkflowDefinition(id="wf-1", name="Login")],
            states=[StateDefinition(id="state-1", name="Login Screen")],
            transitions=[
                TransitionDefinition(
                    id="trans-1",
                    name="Do Login",
                    fromState="state-1",
                    toState="state-2",
                )
            ],
        )
        assert config.version == "2.0.0"
        assert len(config.images) == 1
        assert len(config.workflows) == 1
        assert len(config.states) == 1
        assert len(config.transitions) == 1

    def test_export_configuration_serialization(self) -> None:
        """Test ExportConfiguration can be serialized."""
        config = ExportConfiguration(
            metadata={"name": "Test"},
            workflows=[WorkflowDefinition(id="wf-1", name="Test")],
        )
        data = config.model_dump()
        assert isinstance(data, dict)
        assert data["version"] == "1.0.0"
        assert len(data["workflows"]) == 1
