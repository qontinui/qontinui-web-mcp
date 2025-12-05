# qontinui-web-mcp

MCP (Model Context Protocol) server for the Qontinui web platform. Enables AI assistants to create and manage visual automation configurations through the Qontinui API.

## Features

- **Project Management**: Create, read, update, delete projects
- **Workflow Development**: Build and modify automation workflows
- **State Management**: Define UI states with identifying images
- **Configuration Import/Export**: Full configuration management
- **Capture Sessions**: Record user actions for workflow learning
- **Execution Control**: Trigger and monitor automation runs

## Installation

```bash
cd qontinui-web-mcp
poetry install
```

## Configuration

Set environment variables for the Qontinui API:

```bash
# Development (local)
export QONTINUI_API_URL="http://localhost:8000"

# Production (AWS)
export QONTINUI_API_URL="http://qontinui-prod-py.eba-km2u4s23.eu-central-1.elasticbeanstalk.com"

# Authentication (obtain from Qontinui web app)
export QONTINUI_ACCESS_TOKEN="your-jwt-token"
# OR use credentials
export QONTINUI_EMAIL="your-email@example.com"
export QONTINUI_PASSWORD="your-password"
```

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "qontinui-web": {
      "command": "poetry",
      "args": ["run", "qontinui-web-mcp"],
      "cwd": "/path/to/qontinui-web-mcp",
      "env": {
        "QONTINUI_API_URL": "http://localhost:8000",
        "QONTINUI_EMAIL": "your-email@example.com",
        "QONTINUI_PASSWORD": "your-password"
      }
    }
  }
}
```

### With Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "qontinui-web": {
      "command": "poetry",
      "args": ["run", "qontinui-web-mcp"],
      "cwd": "/path/to/qontinui-web-mcp",
      "env": {
        "QONTINUI_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Available Tools

### Authentication
- `auth_login` - Authenticate with email/password
- `auth_status` - Check current authentication status
- `auth_logout` - Clear stored credentials

### Projects
- `list_projects` - List all accessible projects
- `create_project` - Create a new project
- `get_project` - Get project details
- `update_project` - Update project metadata/configuration
- `delete_project` - Delete a project

### Configuration
- `export_configuration` - Export project configuration as JSON
- `import_configuration` - Import configuration into project
- `validate_configuration` - Validate configuration without importing

### Workflows
- `create_workflow` - Add workflow to project
- `update_workflow` - Modify existing workflow
- `delete_workflow` - Remove workflow from project
- `list_workflows` - List workflows in project

### States
- `create_state` - Define UI state with identifying images
- `update_state` - Modify state definition
- `delete_state` - Remove state from project
- `list_states` - List states in project

### Images
- `add_image` - Add pattern image to project
- `list_images` - List images in project
- `delete_image` - Remove image from project

### Execution
- `execute_workflow` - Run workflow on connected runner
- `get_execution_status` - Check execution progress
- `cancel_execution` - Stop running workflow

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black src/
poetry run isort src/

# Lint
poetry run ruff src/

# Type check
poetry run mypy src/
```

## API Endpoints

This MCP server communicates with the Qontinui backend API:

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:8000` |
| Production | `http://qontinui-prod-py.eba-km2u4s23.eu-central-1.elasticbeanstalk.com` |

## License

MIT
