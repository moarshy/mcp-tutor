"""
MCP Tools for Educational Tutor Server

Tool definitions and handlers for the interactive course system.
"""

import logging
from typing import Any, Dict, List

from mcp.types import Tool, TextContent
from mcp_server.course_management import CourseContentProcessor
from mcp_server.course_tools import CourseTools

logger = logging.getLogger(__name__)


def get_tool_definitions() -> List[Tool]:
    """Get all available tool definitions"""
    return [
        Tool(
            name="register_user",
            description="Register to start the interactive course.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
        Tool(
            name="start_course",
            description="Start or resume a course at a specific level.",
            inputSchema={
                "type": "object",
                "properties": {"level": {"type": "string", "description": "The course level to start (e.g., 'beginner')."}},
                "required": ["level"],
            },
        ),
        Tool(
            name="get_course_status",
            description="Get your current progress in the course.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
        Tool(
            name="next_course_step",
            description="Advance to the next step in the course.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
        Tool(
            name="clear_course_history",
            description="Clear all your course progress and start over.",
            inputSchema={
                "type": "object",
                "properties": {"confirm": {"type": "boolean", "description": "Must be true to confirm."}},
                "required": ["confirm"],
            },
        ),
         Tool(
            name="list_courses",
            description="List all available course levels.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
    ]


async def handle_tool_call(
    name: str, arguments: Dict[str, Any], course_processor: CourseContentProcessor, course_tools: CourseTools
) -> List[TextContent]:
    """Handle all tool calls by delegating to the appropriate handler."""
    logger.info(f"Received tool call: {name}", extra={"tool_name": name, "arguments": arguments})

    # Delegate to stateful course tools
    if hasattr(course_tools, name):
        handler = getattr(course_tools, name)
        result_text = await handler(arguments)
        return [TextContent(type="text", text=result_text)]

    # Handle simple, stateless tools directly
    if name == "list_courses":
        return await _handle_list_courses(course_processor)

    logger.warning(f"Unknown tool called: {name}")
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _handle_list_courses(course_processor: CourseContentProcessor) -> List[TextContent]:
    """Handles the list_courses tool by scanning the course directory."""
    course_levels = []
    for item in course_processor.course_directory.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it's a valid course by looking for course_info.json
            if (item / 'course_info.json').exists():
                 course_levels.append(item.name)

    if not course_levels:
        return [TextContent(type="text", text="No courses found.")]

    result = "Available Courses:\n\n"
    for level in sorted(course_levels):
        result += f"• {level.title()}\n"
    
    return [TextContent(type="text", text=result)] 