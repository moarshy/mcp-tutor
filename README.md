# MCP Educational Tutor

A complete MCP (Model Context Protocol) server that provides intelligent tutoring capabilities by ingesting GitHub documentation repositories and making them accessible through structured tools and educational prompts.

**🎯 Ready for production use with 4 tools + 6 prompts + 26 MCP docs**

## 🎯 Features

- **Document-Level Processing**: Complete, self-contained documents rather than fragmented chunks
- **Tool-Augmented Generation (TAG)**: Direct document retrieval by key, not semantic search
- **MCP Tools**: Search concepts, retrieve documents, get code examples
- **Educational Prompts**: Structured teaching prompts for concept explanation, code review, and learning guidance
- **GitHub Integration**: Automatically clone and process documentation repositories
- **Context-Aware Teaching**: Prompts automatically incorporate relevant documentation for enhanced explanations
- **Multiple Learning Styles**: Support for conceptual, practical, and example-driven teaching approaches

## 🏗️ Architecture

### Content Processing Pipeline
1. **GitHubRepositoryIngester**: Clones repositories and prepares documents
2. **DocumentProcessor**: Creates three types of prepared documents:
   - **Documentation**: Complete `.md`/`.mdx` files as self-contained documents
   - **Code Examples**: Aggregated source files from `examples/` directories  
   - **Changelogs**: Truncated changelog files

### MCP Tools Layer (Model-Controlled)
- `search_mcp_concepts`: Search through prepared documents
- `get_document_by_key`: Retrieve specific documents by key
- `list_available_documents`: Browse all available content
- `get_code_example`: Find code examples for concepts

### MCP Prompts Layer (User-Controlled)
- `explain_mcp_concept`: Structured explanations with examples and analogies
- `mcp_socratic_dialogue`: Guided discovery through Socratic questioning
- `mcp_code_review`: Educational code feedback and best practices
- `mcp_troubleshooting_guide`: Systematic debugging assistance
- `mcp_project_architect`: Architectural guidance for MCP solutions
- `mcp_learning_path`: Personalized learning paths for MCP mastery

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd tutor

# Install dependencies
pip install -e .
```

### 2. Run the MCP Server

```bash
# Start the server (automatically loads MCP documentation)
python -m mcp_server.main
```

### 3. Test the System

```bash
# Test complete server functionality
python -c "
import asyncio
from mcp_server.main import MCPTutorServer

async def test():
    server = MCPTutorServer()
    await server.initialize_content()
    print('✅ Server ready with tools and prompts!')

asyncio.run(test())
"
```

## 🔧 Usage

### With Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "mcp-educational-tutor": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "cwd": "/path/to/tutor"
    }
  }
}
```

### Available Tools (Model-Controlled)

#### Search Concepts
```python
# Search for MCP concepts
search_mcp_concepts(
    query="server implementation",
    doc_type="documentation"  # optional: "documentation", "code_example", "changelog", "any"
)
```

#### Get Specific Document
```python
# Retrieve a document by its key
get_document_by_key(document_key="README")
```

#### List Available Content
```python
# Browse all documents
list_available_documents(doc_type_filter="all")  # or specific type
```

#### Get Code Examples
```python
# Find code examples for concepts
get_code_example(
    concept="server",
    language="python"  # optional: "typescript", "python", "javascript", "any"
)
```

### Available Prompts (User-Controlled)

#### Explain Concepts
```python
# Get structured explanation of MCP concepts
explain_mcp_concept(
    concept="tools",
    student_background="intermediate",  # optional
    explanation_style="practical",      # optional: "conceptual", "practical", "example-driven"
    analogy_domain="web APIs"          # optional
)
```

#### Socratic Learning
```python
# Discover concepts through guided questioning
mcp_socratic_dialogue(
    target_concept="prompts",
    student_current_understanding="...",  # optional
    misconceptions="..."                   # optional
)
```

#### Code Review
```python
# Get educational feedback on implementations
mcp_code_review(
    student_code="...",
    implementation_goal="build MCP server",
    focus_areas="best practices"  # optional
)
```

#### Troubleshooting
```python
# Systematic debugging assistance
mcp_troubleshooting_guide(
    error_description="server not responding",
    code_context="...",        # optional
    attempted_solutions="..."  # optional
)
```

#### Architecture Guidance
```python
# Design MCP solutions from requirements
mcp_project_architect(
    project_requirements="document search system",
    constraints="...",                    # optional
    student_experience_level="beginner"  # optional
)
```

#### Learning Paths
```python
# Personalized learning plans
mcp_learning_path(
    learning_goal="build production MCP server",
    current_knowledge="...",           # optional
    time_commitment="5 hours/week",    # optional
    preferred_learning_style="hands-on"  # optional
)
```

## 📂 Project Structure

```
tutor/
├── mcp_server/
│   ├── __init__.py
│   ├── main.py                 # MCP server orchestration & handlers  
│   ├── tools.py                # 4 MCP tools implementation
│   ├── prompts.py              # 6 educational prompts implementation
│   └── content_processing.py   # Repository ingestion & document processing
├── mcp_client/                 # Client implementation (future)
├── tutor_agent/               # DSPy agent integration (future)
├── tests/
│   └── test_refactor.py       # Modular structure verification
├── docs/                      # Architecture documentation  
├── pyproject.toml             # Dependencies and configuration
└── README.md                 # This file
```

### 🏗️ Modular Architecture Benefits

**📄 mcp_server/main.py** - *Server Orchestration*
- Lightweight coordination layer that manages all components
- Clean MCP server setup with proper handler registration  
- Automatic content initialization on server startup
- Centralized error handling and logging

**🔧 mcp_server/tools.py** - *MCP Tools Layer*
- `MCPTools` class containing all 4 tool implementations
- Clean separation of tool logic from server orchestration
- Easy to add new tools or modify existing ones
- Centralized error handling for tool calls

**📝 mcp_server/prompts.py** - *Educational Prompts Layer*
- `MCPPrompts` class with all 6 educational prompt implementations
- Context-aware prompts that automatically pull relevant documentation
- Multiple pedagogical approaches (conceptual, practical, Socratic)
- Structured educational frameworks for each prompt type

**⚙️ mcp_server/content_processing.py** - *Content Pipeline*
- Document-level processing for Tool-Augmented Generation (TAG)
- GitHub repository ingestion with smart file filtering
- Three document preparation strategies (docs, examples, changelogs)
- Complete, self-contained documents for MCP tool retrieval
