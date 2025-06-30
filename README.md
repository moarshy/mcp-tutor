# Educational Tutor

An experimental system that transforms documentation repositories into interactive educational content using AI and the Model Context Protocol (MCP).

## 🌟 Overview

This project consists of two main components:

1. **📚 Course Content Agent** - Generates structured learning courses from documentation repositories
2. **🔧 MCP Educational Server** - Provides standardized access to course content via MCP protocol

## 🏗️ Architecture

```
Documentation Repository → Course Content Agent → Structured Courses → MCP Server → AI Tutors
```

The system processes documentation, creates educational content, and exposes it through standardized tools for AI tutoring applications.

## 📂 Project Structure

```
tutor/
├── course_content_agent/    # AI-powered course generation from docs
│   ├── main.py             # CourseBuilder orchestration
│   ├── modules.py          # Core processing logic
│   ├── models.py           # Pydantic data models
│   ├── signatures.py       # DSPy LLM signatures
│   └── about.md           # 📖 Detailed documentation
├── mcp_server/             # MCP protocol server for course access
│   ├── main.py            # MCP server startup
│   ├── tools.py           # Course interaction tools
│   ├── course_management.py # Content processing
│   └── about.md           # 📖 Detailed documentation
├── course_output/          # Generated course content
├── nbs/                   # Jupyter notebooks for development
└── pyproject.toml         # Project configuration
```

## 🚀 Quick Start

### 1. Generate Courses from Documentation

```bash
# Install dependencies
pip install -e .

# Generate courses from a repository
python course_content_agent/test.py
```

**Customize for Your Repository**: Edit `course_content_agent/test.py` to change:
- Repository URL (currently uses MCP docs)
- Include/exclude specific folders
- Output directory and caching settings

### 2. Start MCP Server

```bash
# Serve generated courses via MCP protocol
python -m mcp_server.main

# Or customize course directory
COURSE_DIR=your_course_output python -m mcp_server.main
```

### 3. Test MCP Integration

```bash
# Test server capabilities
python mcp_server/stdio_client.py
```

## 📖 Detailed Documentation

For comprehensive information about each component:

- **Course Content Agent**: See [`course_content_agent/about.md`](course_content_agent/about.md)
  - AI-powered course generation
  - DSPy signatures and multiprocessing
  - Document analysis and learning path creation
  
- **MCP Educational Server**: See [`mcp_server/about.md`](mcp_server/about.md)
  - MCP protocol implementation
  - Course interaction tools
  - Integration with AI assistants

## 🔌 MCP Integration with Cursor

To use the educational tutor MCP server with Cursor, create a `.cursor/mcp.json` file in your project root:

```json
{
    "mcpServers": {
        "educational-tutor": {
            "command": "/path/to/your/python",
            "args": ["-m", "mcp_server.main"],
            "cwd": "/path/to/tutor/project",
            "env": {
                "COURSE_DIR": "/path/to/tutor/course_output"
            }
        }
    }
}
```

**Setup Steps**:
1. Update the `command` path to your Python executable (`which python`)
2. Update the `cwd` path to your tutor project directory
3. Update the `COURSE_DIR` to your course output directory
4. Restart Cursor or reload the window
5. Use `@educational-tutor` in Cursor chat to access course tools

## 🔧 Development Status

**Current Status**: ✅ Functional MVP
- Course generation from documentation repositories
- MCP server for standardized content access
- Multi-complexity course creation (beginner/intermediate/advanced)

**Future Enhancements**:
- Support for diverse content sources (websites, videos)
- Advanced search and recommendation systems
- Integration with popular AI platforms

## 🛠️ Technology Stack

- **AI Framework**: DSPy for LLM orchestration
- **Content Processing**: Multiprocessing for performance
- **Protocol**: Model Context Protocol (MCP) for standardization
- **Models**: Gemini 2.5 Flash for content generation
- **Data**: Pydantic models for type safety

## 📄 License

This project is experimental and intended for educational and research purposes.