# MCP Educational Tutor

An experimental Model Context Protocol (MCP) server that transforms documentation repositories into interactive educational content for AI tutoring systems.

> **⚠️ Development Status**: This project is actively being developed. Currently uses [MCP documentation](https://github.com/modelcontextprotocol/docs) as course material. Future versions will/should support diverse content sources including GitHub repositories, websites, and YouTube videos.

## 🌟 Overview

Inspired by Mastra's ["course as a MCP"](https://github.com/mastra-ai/mastra/tree/main/packages/mcp-docs-server), this project creates a specialized MCP server designed for educational applications. The server processes documentation repositories and exposes them through MCP tools and prompts for AI tutoring agents.

### What has been done?

1. **MCP server**
   - **Content Processing**
     - clones the repo
     - document level processing
   - **MCP tools**
     - exposes the following tools
       - `search_mcp_concepts`: Search through prepared documents
       - `get_document_by_key`: Retrieve specific documents by key
       - `list_available_documents`: Browse all available content
       - `get_code_example`: Find code examples for concepts (not properly thought through)
     - uses a simple search logic (text matching with document title, description, content)
   - **MCP Prompts**
     - exposes the following prompts but note the current tutor_agent doesnt use them
     - they have been explored but could become pivotal when Claude Desktop becomes the tutor agent
     - available prompts
       - `search_mcp_concepts`: Search through prepared documents
       - `get_document_by_key`: Retrieve specific documents by key
       - `list_available_documents`: Browse all available content
       - `get_code_example`: Find code examples for concepts

2. **Tutor Agent**
   - the current tutor agent is implemented using DSPY's ReAct module
   - simple loop that takes student query and student_profile (knowledge_level, interests, learning_goals)
   - gererates teaching material (??)
   - known issues with current implementation
     - retrieval can be wild

## ✅ Current Implementation

### MCP Server Components

#### 📚 Content Processing
- **Repository Ingestion**: Automatically clones and processes Git repositories
- **Document-Level Processing**: Creates complete, self-contained documents
- **Smart Filtering**: Focuses on educational content (documentation, examples, changelogs)

#### 🔧 MCP Tools (4 Available)
- **`search_mcp_concepts`**: Search through prepared documents with text matching
- **`get_document_by_key`**: Retrieve specific documents by unique identifier  
- **`list_available_documents`**: Browse all available content by type
- **`get_code_example`**: Find code examples for specific concepts

#### 📝 MCP Prompts (6 Available)
Educational prompts designed for structured learning:
- **`explain_mcp_concept`**: Conceptual explanations with analogies
- **`mcp_socratic_dialogue`**: Guided discovery through questioning
- **`mcp_code_review`**: Educational code feedback
- **`mcp_troubleshooting_guide`**: Systematic debugging assistance
- **`mcp_project_architect`**: Design guidance from requirements
- **`mcp_learning_path`**: Personalized learning plans

## 🏗️ Architecture

### Content Processing Pipeline
```
GitHub Repository → Clone → Process → Prepare Documents → MCP Tools/Prompts
```

1. **GitHubRepositoryIngester**: Handles repository cloning and file discovery
2. **DocumentProcessor**: Creates three document types:
   - **Documentation**: `.md`/`.mdx` files as complete educational units
   - **Code Examples**: Aggregated source files from example directories
   - **Changelogs**: Version history and updates

## 🚀 Quick Start

### Installation
```bash
git clone <repository-url>
cd tutor
pip install -e .
```

### Run MCP Server
```bash
python -m mcp_server.main
```

### Run Tutor Agent
```bash
python tutor_agent.main.py
```

## 📂 Project Structure

```
tutor/
├── mcp_server/              # Core MCP server implementation
│   ├── __init__.py
│   ├── main.py             # Server orchestration & startup
│   ├── tools.py            # 4 MCP tools implementation
│   ├── prompts.py          # 6 educational prompts
│   └── content_processing.py # Repository ingestion pipeline
├── mcp_client/             # Client implementation (future)
├── tutor_agent/           # DSPy agent integration
│   ├── __init__.py
│   ├── main.py            # DSPy ReAct tutor agent
│   └── deprecated/        # Previous implementations
├── tests/                 # Test implementations
│   ├── test_tutor_agent.py
│   └── test_server.py
├── docs/                  # Architecture documentation
├── cache/                 # Cached processed documents
├── pyproject.toml         # Project configuration
└── README.md             # Project documentation
```

### Key Components

**`mcp_server/`** - The core MCP server that processes content and exposes tools/prompts
- `main.py`: Server startup, content initialization, MCP handler registration
- `tools.py`: 4 MCP tools for document search and retrieval
- `prompts.py`: 6 educational prompts for structured learning
- `content_processing.py`: GitHub repo cloning and document preparation

**`tutor_agent/`** - DSPy-based educational agent that consumes MCP tools
- `main.py`: ReAct agent implementation with MCP integration
- Uses DSPy ReAct pattern to intelligently call MCP tools based on student queries

**`tests/`** - Test suite for validation
- Agent functionality and MCP integration tests
- Server tool and prompt testing

## Musings

### 1. MCP Server Design Questions
- Tool/Prompt Strategy: What tools and prompts should the server actually expose?
- Knowledge Discovery: Since retrieval seems to be the most important thing this provides, how/what should we implement for better discovery?
- Domain Flexibility: We're starting with technical docs - how much does the server need to change for teaching, say, high school maths?
- Resource Types: Should we also expose resources - for example, images that the agent can use for teaching? Can this be used in teachings?

### 2. Tutor Agent Architecture
- Multi-Domain Agents: Will we have a single agent for different types of "courses" (technical docs vs maths vs other subjects)?
- Agent Pattern Choice: ReAct vs other agent patterns - what works best for educational use cases?