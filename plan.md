# Development Plan: Implementing a Stateful Course System

This document outlines the plan to build a stateful, Mastra-inspired interactive course system on top of the existing MCP server.

The core principle is to separate the **Course Content Structure** (read from the `course_output` directory) from the **User's Progress State** (stored locally in a `.cache` directory).

---

### **Part 1: Foundational Modules (User & State)**

This part focuses on creating the backend components for managing user identity and progress, stored locally on the user's machine.

-   **✅ 1.1: Define Data Models (`mcp_server/models.py`)**
    -   Create Pydantic models: `StepState`, `ModuleState`, and `CourseState`.
    -   These models will represent the user's progress, containing `name` and `status` fields (0=not started, 1=in progress, 2=completed).

-   **✅ 1.2: Create User Management Module (`mcp_server/user_management.py`)**
    -   Implement functions to manage a local user identity in `REPO_DIR/.cache/user_profile.json`.
    -   `save_user_credentials()`: Creates a unique `user_id` and `key`.
    -   `get_user_credentials()`: Retrieves the saved credentials.
    -   Implement functions to manage course progress in `REPO_DIR/.cache/course_state.json`.
    -   `load_course_state()`: Reads the user's progress file.
    -   `save_course_state()`: Writes the user's progress to the file.

### **Part 2: Course Logic Module (Content Management)**

This part refines the existing `CourseContentProcessor` to work with the new stateful system.

-   **✅ 2.1: Refactor `CourseContentProcessor` (`mcp_server/course_management.py`)**
    -   **`scan_course_content(level)`**: This function will be adapted to scan the `course_output/{level}` directory and produce a "fresh" `CourseState` object based on the `course_info.json` and the module/step file structure. This represents the master copy of the course.
    -   **`merge_course_states(current_state, new_state)`**: Implement this critical function to combine a user's saved progress (`current_state`) with the freshly scanned course structure (`new_state`), preserving progress while adding new content.
    -   **`read_course_step(level, module_id, step_type)`**: Adapt this to read the content of a specific step file (e.g., `01_intro.md`).

### **Part 3: Tool Implementation (The User Experience)**

This part creates the user-facing tools that orchestrate the entire experience.

-   **✅ 3.1: Create Prompts Module (`mcp_server/prompts.py`)**
    -   Define `INTRODUCTION_PROMPT` for new user registration.
    -   Define `LESSON_PROMPT_TEMPLATE` to wrap all course step content, providing consistent instructions to the AI model.

-   **⬜ 3.2: Implement Course Tools (`mcp_server/course_tools.py`)**
    -   Create a new file for the stateful course tools.
    -   **`register_user({email: string})`**: Creates the user profile and returns the `INTRODUCTION_PROMPT`.
    -   **`start_course({level: string})`**: The main entry point. It will check registration, load the master course structure, merge it with user progress, and return the current step.
    -   **`get_course_status({level: string})`**: Loads and merges state, then formats a detailed progress report for the user.
    -   **`next_course_step()`**: Handles the core progression logic: marking steps/modules as complete, advancing to the next item, and handling course completion.
    -   **`clear_course_history({confirm: boolean})`**: Deletes the user's progress file.

### **Part 4: System Integration & Logging**

This final part connects all the new modules and implements robust logging.

-   **⬜ 4.1: Setup Structured Logging (`mcp_server/logging_config.py`)**
    -   Create a module to configure file-based JSON logging to `logs/mcp_server.log`.

-   **⬜ 4.2: Integrate New Tools (`mcp_server/main.py` & `mcp_server/tools.py`)**
    -   Update `tools.py` to include the new course tool definitions.
    -   Update `handle_tool_call` to delegate to a new `handle_course_tool_call` function.
    -   Update `main.py` to initialize the logging system at startup.
    -   Add logging throughout the new modules to capture tool calls, state changes, and errors.
    -   Add `logs/` to `.gitignore`.

---
*Legend: ✅ = Done, ⬜ = To Do* 