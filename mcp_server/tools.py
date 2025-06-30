"""
MCP Tools for Educational Tutor Server

Tool definitions and handlers for course interaction and content retrieval.
"""

import logging
from typing import Any, Dict, List
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def get_tool_definitions() -> List[Tool]:
    """Get all available tool definitions"""
    return [
        Tool(
            name="list_courses",
            description="List all available courses with their titles and levels",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_course_outline",
            description="Get the complete outline/structure of a specific course",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Course level (beginner, intermediate, advanced)"
                    }
                },
                "required": ["level"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_module_content",
            description="Get all content from a specific module in a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Course level (beginner, intermediate, advanced)"
                    },
                    "module_id": {
                        "type": "string",
                        "description": "Module identifier (e.g., module_01, module_02)"
                    }
                },
                "required": ["level", "module_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_step_content",
            description="Get content from a specific step within a module",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Course level (beginner, intermediate, advanced)"
                    },
                    "module_id": {
                        "type": "string",
                        "description": "Module identifier (e.g., module_01, module_02)"
                    },
                    "step_type": {
                        "type": "string",
                        "description": "Step type (intro, main, conclusion, assessments, summary)",
                        "enum": ["intro", "main", "conclusion", "assessments", "summary"]
                    }
                },
                "required": ["level", "module_id", "step_type"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="search_course_content",
            description="Search for specific content across all courses",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant content"
                    },
                    "level": {
                        "type": "string",
                        "description": "Optional: limit search to specific course level",
                        "enum": ["beginner", "intermediate", "advanced"]
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        )
    ]


async def handle_tool_call(name: str, arguments: Dict[str, Any], course_processor) -> List[TextContent]:
    """Handle tool calls for course interaction"""
    
    if not course_processor:
        return [TextContent(type="text", text="Course processor not initialized")]
    
    try:
        if name == "list_courses":
            return await _handle_list_courses(course_processor)
        elif name == "get_course_outline":
            return await _handle_get_course_outline(arguments, course_processor)
        elif name == "get_module_content":
            return await _handle_get_module_content(arguments, course_processor)
        elif name == "get_step_content":
            return await _handle_get_step_content(arguments, course_processor)
        elif name == "search_course_content":
            return await _handle_search_course_content(arguments, course_processor)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_list_courses(course_processor) -> List[TextContent]:
    """Handle list_courses tool"""
    courses = course_processor.list_courses()
    if not courses:
        return [TextContent(type="text", text="No courses found")]
    
    result = "Available Courses:\n\n"
    for level, title in courses.items():
        result += f"• **{level.title()}**: {title}\n"
    
    return [TextContent(type="text", text=result)]


async def _handle_get_course_outline(arguments: Dict[str, Any], course_processor) -> List[TextContent]:
    """Handle get_course_outline tool"""
    level = arguments.get("level")
    course = course_processor.get_course(level)
    
    if not course:
        return [TextContent(type="text", text=f"Course not found: {level}")]
    
    result = f"# {course.title}\n\n"
    result += f"**Level**: {course.level.title()}\n"
    result += f"**Description**: {course.description}\n\n"
    
    
    result += "## Modules\n\n"
    for module in course.modules:
        result += f"### {module.order + 1}. {module.title}\n"
        result += f"**Module ID**: {module.module_id}\n"
        result += f"**Available Steps**: {', '.join(module.steps.keys())}\n\n"
    
    return [TextContent(type="text", text=result)]


async def _handle_get_module_content(arguments: Dict[str, Any], course_processor) -> List[TextContent]:
    """Handle get_module_content tool"""
    level = arguments.get("level")
    module_id = arguments.get("module_id")
    
    course = course_processor.get_course(level)
    if not course:
        return [TextContent(type="text", text=f"Course not found: {level}")]
    
    module = next((m for m in course.modules if m.module_id == module_id), None)
    if not module:
        return [TextContent(type="text", text=f"Module not found: {module_id}")]
    
    result = f"# {module.title}\n\n"
    result += f"**Module ID**: {module.module_id}\n"
    result += f"**Course**: {course.title} ({level.title()})\n\n"
    
    # Include all steps
    step_order = ["intro", "main", "conclusion", "assessments", "summary"]
    for step_type in step_order:
        if step_type in module.steps:
            step = module.steps[step_type]
            result += f"## {step.title}\n\n"
            result += step.content + "\n\n"
            result += "---\n\n"
    
    return [TextContent(type="text", text=result)]


async def _handle_get_step_content(arguments: Dict[str, Any], course_processor) -> List[TextContent]:
    """Handle get_step_content tool"""
    level = arguments.get("level")
    module_id = arguments.get("module_id")
    step_type = arguments.get("step_type")
    
    course = course_processor.get_course(level)
    if not course:
        return [TextContent(type="text", text=f"Course not found: {level}")]
    
    module = next((m for m in course.modules if m.module_id == module_id), None)
    if not module:
        return [TextContent(type="text", text=f"Module not found: {module_id}")]
    
    if step_type not in module.steps:
        return [TextContent(type="text", text=f"Step not found: {step_type}")]
    
    step = module.steps[step_type]
    result = f"# {step.title}\n\n"
    result += f"**Module**: {module.title}\n"
    result += f"**Course**: {course.title} ({level.title()})\n"
    result += f"**Step Type**: {step_type.title()}\n\n"
    result += "---\n\n"
    result += step.content
    
    return [TextContent(type="text", text=result)]


async def _handle_search_course_content(arguments: Dict[str, Any], course_processor) -> List[TextContent]:
    """Handle search_course_content tool"""
    query = arguments.get("query", "").lower()
    level_filter = arguments.get("level")
    
    if not query:
        return [TextContent(type="text", text="Please provide a search query")]
    
    results = []
    courses_to_search = [course_processor.get_course(level_filter)] if level_filter else course_processor.get_all_courses()
    
    for course in courses_to_search:
        if not course:
            continue
            
        # Search in course title and description
        if query in course.title.lower() or query in course.description.lower():
            results.append(f"**Course**: {course.title} ({course.level})\n{course.description}")
        
        # Search in modules and steps
        for module in course.modules:
            if query in module.title.lower():
                results.append(f"**Module**: {module.title} (Course: {course.title})")
            
            for step in module.steps.values():
                if query in step.title.lower() or query in step.content.lower():
                    # Show a snippet of the content
                    content_snippet = step.content[:200] + "..." if len(step.content) > 200 else step.content
                    results.append(f"**Step**: {step.title}\n**Module**: {module.title}\n**Course**: {course.title}\n\n{content_snippet}")
    
    if not results:
        return [TextContent(type="text", text=f"No content found matching '{query}'")]
    
    result_text = f"Search Results for '{query}':\n\n" + "\n\n---\n\n".join(results[:10])  # Limit to 10 results
    if len(results) > 10:
        result_text += f"\n\n... and {len(results) - 10} more results"
    
    return [TextContent(type="text", text=result_text)] 