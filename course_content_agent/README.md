# Course Content Agent - Modular Architecture

This module has been refactored from a single large file into a modular architecture for better maintainability, testability, and organization.

## File Structure

```
course_content_agent/
├── __init__.py              # Package initialization and main exports
├── content_extraction.py    # Main entry point and unified interface
├── models.py               # All Pydantic models and enums
├── signatures.py           # All DSPy signatures for LLM interactions
├── modules.py              # DSPy modules, utility classes, and helper functions
├── main.py                 # CourseBuilder class and main orchestration logic
└── README.md              # This documentation file
```

## Module Responsibilities

### `models.py`
Contains all Pydantic data models and enums:
- `DocumentType`, `ComplexityLevel` (enums)
- `DocumentMetadata`, `DocumentNode`, `DocumentTree`
- `AssessmentPoint`, `LearningModule`, `GroupedLearningPath`
- `ModuleContent`, `GeneratedCourse`

### `signatures.py`
Contains all DSPy signatures for LLM interactions:
- `DocumentParser`, `DocumentClassifier`
- `CrossReferenceAnalyzer`, `DocumentClusterer`
- Various content generators (intro, summary, assessment, etc.)

### `modules.py`
Contains implementation classes and utilities:
- `RepoManager` - Git repository handling
- `ContentExtractor` - Markdown content processing
- `DocumentParserModule`, `CrossReferenceModule` - DSPy modules
- `LearningPathGenerator`, `CourseGenerator`, `CourseExporter`
- Multiprocessing helper functions

### `main.py`
Contains the main orchestration logic:
- `CourseBuilder` - Main class that coordinates the entire process
- `main()` - Example usage function
- DSPy configuration and logging setup

### `content_extraction.py`
Serves as the unified interface:
- Imports from all other modules
- Re-exports key classes for backward compatibility
- Provides convenience functions like `build_course_from_repo()`

## Usage

### Quick Usage
```python
from course_content_agent import build_course_from_repo

# Generate courses from a repository
tree = build_course_from_repo("https://github.com/example/docs")

# Generate courses from specific folders only
tree = build_course_from_repo(
    "https://github.com/example/docs",
    include_folders=["docs", "guides", "api-reference"]
)
```

### Advanced Usage
```python
from course_content_agent import CourseBuilder

# Initialize with custom settings
builder = CourseBuilder(max_workers=8, cache_dir="./my_cache")

# Build course with options
tree = builder.build_course(
    repo_url="https://github.com/example/docs",
    force_rebuild=True,
    export_dir="./output",
    use_batched_llm=True,
    use_batched_relationships=True
)

# Build course from specific folders only
tree = builder.build_course(
    repo_url="https://github.com/example/docs",
    include_folders=["documentation", "user-guides"],  # Only process these folders
    export_dir="./output"
)
```

### Folder Filtering

You can specify which folders to process using the `include_folders` parameter:

```python
from course_content_agent import build_course_from_repo

# Only process specific folders
success = build_course_from_repo(
    repo_path="/path/to/docs",
    include_folders=["docs", "guides", "api-reference"]
)
```

Folder rules:
- Paths are relative to the repository root
- Use forward slashes (works on all platforms)
- Subfolders are automatically included (e.g., "docs" includes "docs/api", "docs/guides", etc.)
- Use "." to include root-level files

### Overview Context

Provide an overview document filename to help the LLM better understand and classify individual documents:

```python
# Use a specific overview document for context
success = build_course_from_repo(
    repo_path="/path/to/docs",
    overview_doc="architecture.mdx"  # Filename of overview document
)
```

Benefits of providing overview context:
- **Better Classification**: The LLM can classify documents more accurately within the broader project context
- **Improved Extraction**: Key concepts and topics are identified with better understanding of the project scope
- **Enhanced Relationships**: Document relationships are detected more effectively when the overall structure is understood

### Advanced Usage

Combine all features for maximum control:

```python
from course_content_agent import build_course_from_repo

success = build_course_from_repo(
    repo_path="/path/to/mcp-docs",
    output_dir="mcp_course",
    include_folders=["docs", "reference", "examples"],
    overview_doc="architecture.mdx",  # Use this file for overview context
    batch_size=30,
    max_workers=4
)
```

## Benefits of Modular Architecture

1. **Maintainability**: Each file has a clear, focused responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Reusability**: Components can be imported and used independently
4. **Readability**: Smaller files are easier to understand and navigate
5. **Collaboration**: Multiple developers can work on different modules simultaneously
6. **Extensibility**: New features can be added to appropriate modules without affecting others

## Migration from Previous Version

The refactoring maintains backward compatibility. Existing code that imports from `content_extraction.py` should continue to work:

```python
# This still works
from course_content_agent.content_extraction import CourseBuilder

# This also works now
from course_content_agent import CourseBuilder
```

## Configuration

DSPy configuration is now centralized in `main.py`. To use a different LLM:

```python
import dspy
from course_content_agent import CourseBuilder

# Configure DSPy before creating CourseBuilder
dspy.configure(lm=dspy.LM("anthropic/claude-3-5-haiku-latest", cache=False))

builder = CourseBuilder()
```

## Logging

Logging is configured in `main.py` and outputs to both console and `output.log` file. Log levels can be adjusted by modifying the logging configuration.

## Dependencies

The modular structure maintains the same dependencies as the original:
- `dspy` - For LLM interactions
- `pydantic` - For data modeling
- `GitPython` - For repository handling
- `frontmatter` - For markdown processing
- Standard library modules for multiprocessing, file I/O, etc.