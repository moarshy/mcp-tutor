# Mastra MCP Server Overview

A Model Context Protocol (MCP) server that provides AI assistants with direct access to Mastra.ai's complete knowledge base.

## Features

- **Complete Documentation Access** - All Mastra.ai docs with MDX support (sourced from `.docs/raw/`)
- **Production-Ready Code Examples** - Real implementation patterns and templates (flattened from `examples/` repo directory)
- **Technical Blog Posts** - Latest announcements and technical articles (live scraped from mastra.ai/blog)
- **Package Changelogs** - Detailed version history for all packages (extracted from multiple repo directories)
- **Interactive Course System** - Guided learning with progress tracking (scanned from `.docs/raw/course/`)
- **Multi-Environment Support** - Works with Cursor, Windsurf, and Mastra agents

## Tools

### Documentation & Content Tools

| Tool | Purpose | Discovery Method |
|------|---------|------------------|
| `mastraDocs` | Get documentation by path | File system scanning |
| `mastraExamples` | Access code examples | Pre-processed markdown files |
| `mastraBlog` | Fetch blog posts | Live web scraping |
| `mastraChanges` | Package changelogs | Pre-processed changelog files |

### Course Tools

| Tool | Purpose |
|------|---------|
| `startMastraCourse` | Register/start course |
| `getMastraCourseStatus` | Check progress |
| `startMastraCourseLesson` | Jump to specific lesson |
| `nextMastraCourseStep` | Advance to next step |
| `clearMastraCourseHistory` | Reset progress |

## How Each Tool Works

### `mastraDocs`
- **Input**: `paths: string[]`, `queryKeywords?: string[]`
- **How LLM Discovers**: Gets complete directory tree in tool schema description (built at startup from `.docs/raw/`; code here https://github.com/mastra-ai/mastra/blob/main/packages/mcp-docs-server/src/tools/docs.ts#L163)
- **How LLM Calls**: 
  - **List all**: `{ paths: [""] }` - Returns root directory + all file contents
  - **Specific docs**: `{ paths: ["reference/agents"] }` - Returns directory listing + all .mdx contents
  - **Multi-path**: `{ paths: ["agents", "reference/agents"] }` - Gets both guides and API docs
  - **Smart Features**: 
    - Typo Recovery: `Only when path not found` - walks up directory tree to find nearest match (e.g., "reference/agen" → suggests "reference/agents/")
    - Full-text Search: `Only when keywords provided` - scans all .mdx content for matches, scores by keyword frequency + title matches + path relevance
    - Auto-content Inclusion: `Always for directory requests` - automatically returns listing + full content of ALL .mdx files in that directory
    - Keyword Suggestions: `Only when path fails + keywords exist` - triggers content-based suggestions using extracted keywords + user query terms 
    - none of these use vector db or others like it for content retrieval

### `mastraExamples`
- **Input**: `example?: string`, `queryKeywords?: string[]`
- **How LLM Discovers**: Tool schema includes alphabetically sorted list of all examples (built from `.docs/organized/code-examples/` https://github.com/mastra-ai/mastra/blob/main/packages/mcp-docs-server/src/tools/examples.ts#L54 here is where all examples get embedded in to the tool description)
- **How LLM Calls**:
  - **List all**: `{}` - Returns sorted list of example names
  - **Specific example**: `{ example: "quick-start" }` - Returns flattened code (package.json + all .ts files)
  - **With keywords**: `{ example: "agent", queryKeywords: ["network"] }` - Gets example + keyword suggestions
- **Content**: Pre-processed examples (max 1000 lines each) with package.json and TypeScript files

### `mastraBlog`
- **Input**: `url: string`
- **How LLM Discovers**: No pre-built list - discovers dynamically by scraping live blog page
- **How LLM Calls**:
  - **List all posts**: `{ url: "/blog" }` - Scrapes mastra.ai/blog, extracts all post links/titles
  - **Specific post**: `{ url: "/blog/post-name" }` - Fetches and converts HTML to clean text
- **Dynamic**: Always up-to-date with latest blog posts from live site

### `mastraChanges`
- **Input**: `package?: string`
- **How LLM Discovers**: Tool schema includes sorted list of all package names (built from `.docs/organized/changelogs/`)
- **How LLM Calls**:
  - **List all packages**: `{}` - Returns sorted list: @mastra/core, @mastra/deployer, etc.
  - **Specific changelog**: `{ package: "@mastra/core" }` - Returns truncated changelog (max 300 lines)
- **Content**: Pre-extracted from multiple repo directories, URL-encoded filenames for special characters

## Course Tools

### `startMastraCourse`

- **Input**: `email?: string`
- **How LLM Discovers**: Dynamically scans `.docs/raw/course/` directory on every call - builds lesson/step hierarchy from numbered directories and .md files
- **How LLM Calls**:
  - **Unregistered user**: `{}` - Checks `~/.cache/mastra/.device_id`, returns registration prompt if not found
  - **Registration**: `{ email: "user@example.com" }` - HTTP POST to `mastra.ai/api/course/register`, saves deviceId+key locally, returns introduction prompt
  - **Registered user**: `{}` - Loads existing progress, merges with fresh course scan, returns current lesson/step content

#### State Management:

- **Credentials**: `~/.cache/mastra/.device_id` stores `{deviceId, key}` for server authentication
- **Progress**: `~/.cache/mastra/course/state.json` tracks lesson/step completion status (0=not started, 1=in progress, 2=completed)
- **Sync**: Local state saved first, then synced to server via POST to `/api/course/update` (fails silently if offline)
- **Merging**: Fresh course structure merged with existing progress on every call to handle new content

#### Smart Features:

- **Content Detection**: Automatically detects new lessons/steps added to course directory
- **Progress Preservation**: Maintains completion status when course content updates
- **Auto-progression**: Handles lesson completion and moves to next lesson automatically
- **Registration Flow**: Guides unregistered users through email registration with clear prompts

#### `getMastraCourseStatus`
- **Input**: `{}` (no parameters)
- **How LLM Calls**: `{}` - Returns formatted progress report with completion percentages, current lesson, course URL
- **Process**: Loads state, merges with latest course content, calculates statistics

#### `startMastraCourseLesson`
- **Input**: `lessonName: string`
- **How LLM Discovers**: Available lesson names from course state (scanned from directory structure)
- **How LLM Calls**: `{ lessonName: "first-agent" }` - Jumps to specific lesson, returns first incomplete step
- **Validation**: Shows available lessons if invalid name provided

#### `nextMastraCourseStep`
- **Input**: `{}` (no parameters)
- **How LLM Calls**: `{}` - Marks current step complete, advances to next step/lesson, returns new content
- **Auto-progression**: Handles lesson completion and course completion automatically

#### `clearMastraCourseHistory`
- **Input**: `confirm: boolean`
- **How LLM Calls**: `{ confirm: true }` - Requires explicit confirmation, deletes all progress
- **Safety**: Prevents accidental deletion with confirmation requirement

## Content Discovery Architecture

### 1. Preparation Phase (Build Time)
```bash
# Pre-processes content into organized structure
prepareCodeExamples()    # Flattens example projects
preparePackageChanges()  # Extracts changelogs  
copyRaw()               # Copies documentation
```