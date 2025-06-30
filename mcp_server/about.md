# MCP Educational Tutor Server

A Model Context Protocol (MCP) server that provides structured access to educational course content. This server enables AI assistants and clients to interact with course materials through standardized tools and prompts.

## File Structure

```
mcp_server/
├── __init__.py             # Package initialization
├── main.py                 # MCP server entry point and initialization
├── course_management.py    # Course content processing and data models
├── tools.py                # MCP tool definitions and handlers
├── prompts.py              # MCP prompt definitions and handlers (currently disabled)
├── stdio_client.py         # Test client for server capabilities
└── about.md               # This documentation file
```

## Module Responsibilities

### `main.py`
Main MCP server orchestration and initialization:
- Configures stdio or SSE transport protocols
- Initializes course processor and loads course content
- Registers tool and prompt handlers with the MCP server

### `course_management.py`
Course content processing and data management:
- Scans course directories and extracts structured content
- Provides Pydantic models for courses, modules, and steps
- Manages course metadata and content retrieval

### `tools.py`
MCP tool implementations for course interaction:
- Provides 5 tools: list_courses, get_course_outline, get_module_content, get_step_content, search_course_content
- Handles course navigation and content retrieval
- Returns formatted markdown content for educational materials

### `prompts.py`
MCP prompt templates for educational interactions:
- Defines 4 educational prompts: explain_concept, create_assessment, learning_path, review_content
- Provides structured prompt templates for tutoring scenarios
- Currently commented out in main.py (not active)

### `stdio_client.py`
Test client for development and debugging:
- Connects to MCP server via stdio transport
- Lists available tools and demonstrates their usage
- Tests course content retrieval and search functionality

## How It Works (Process Flow)

1. **Server Initialization**: Main.py starts MCP server and initializes course processor
2. **Course Loading**: CourseContentProcessor scans course output directories and builds structured data
3. **Tool Registration**: Server registers tools for course interaction and content access
4. **Client Connection**: External clients connect via stdio or SSE transport
5. **Tool Execution**: Clients call tools to browse courses, get content, and search materials

## Available Tools

### Course Discovery
- **`list_courses`**: Get all available courses with titles and levels
- **`get_course_outline`**: Get complete course structure and module overview

### Content Access
- **`get_module_content`**: Retrieve all content from a specific module
- **`get_step_content`**: Get content from individual module steps (intro, main, conclusion, assessments, summary)

### Search & Navigation
- **`search_course_content`**: Search across all course content with optional level filtering

## Usage Examples

### Starting the Server

```bash
# Stdio transport (default)
python -m mcp_server.main

# SSE transport (requires mcp[sse])
MCP_USE_SSE=true MCP_HOST=localhost MCP_PORT=8000 python -m mcp_server.main
```

### Testing with Client

```bash
# Run test client to see server capabilities
python mcp_server/stdio_client.py
```

### Environment Variables

- **`COURSE_DIR`**: Directory containing course content (default: "nbs/course_output")
- **`MCP_USE_SSE`**: Enable SSE transport ("true"/"false", default: "false")
- **`MCP_HOST`**: SSE server host (default: "localhost")
- **`MCP_PORT`**: SSE server port (default: "8000")

## Course Directory Structure

The server expects courses in this format:

```
course_output/
├── beginner/
│   ├── course_info.json
│   ├── 00_welcome.md
│   ├── 99_conclusion.md
│   └── module_01/
│       ├── 01_intro.md
│       ├── 02_main.md
│       ├── 03_conclusion.md
│       ├── 04_assessments.md
│       └── 05_summary.md
├── intermediate/
└── advanced/
```

## Data Models

### Core Models
- **`StepContent`**: Individual step content (intro, main, conclusion, assessments, summary)
- **`ModuleStructure`**: Module with ordered steps and metadata
- **`CourseStructure`**: Complete course with modules, title, and description

### Content Organization
- **Courses**: Organized by complexity level (beginner, intermediate, advanced)
- **Modules**: Sequential learning units within each course
- **Steps**: 5-part structure for each module (intro → main → conclusion → assessments → summary)

## Integration

This MCP server can be integrated with:
- AI assistants and language models
- Educational platforms and LMS systems
- Custom learning applications
- Course authoring tools

The standardized MCP protocol ensures compatibility with any MCP-capable client or application. 