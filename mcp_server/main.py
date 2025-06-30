"""
MCP Educational Tutor Server

Simple MCP server for educational course content.
Supports stdio (default) or SSE via MCP_USE_SSE=true environment variable.
"""

import logging
import os
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent, Prompt, PromptMessage
import mcp.server.stdio

# Optional SSE support
try:
    import mcp.server.sse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

from .course_management import CourseContentProcessor
from .tools import get_tool_definitions, handle_tool_call
from .prompts import get_prompt_definitions, handle_prompt_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("educational-tutor")

# Global course processor
course_processor = None


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return get_tool_definitions()


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    return await handle_tool_call(name, arguments, course_processor)


# @server.list_prompts()
# async def handle_list_prompts() -> List[Prompt]:
#     """List available prompts"""
#     return get_prompt_definitions()


# @server.get_prompt()
# async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> List[PromptMessage]:
#     """Handle prompt requests"""
#     return await handle_prompt_request(name, arguments, course_processor)


async def main():
    """Initialize and run the MCP server"""
    global course_processor
    
    # Initialize course processor
    try:
        COURSE_DIR = os.getenv("COURSE_DIR", "./course_output")
        course_processor = CourseContentProcessor(COURSE_DIR)
        course_processor.scan_courses()
        courses = course_processor.list_courses()
        logger.info(f"Loaded {len(courses)} courses")
    except Exception as e:
        logger.error(f"Failed to initialize course processor: {e}")
        course_processor = None
    
    # Check if SSE is requested
    use_sse = os.getenv("MCP_USE_SSE", "false").lower() == "true"
    
    if use_sse:
        if not SSE_AVAILABLE:
            logger.error("SSE requested but not available. Install with: pip install mcp[sse]")
            return
        
        # Run SSE server
        host = os.getenv("MCP_HOST", "localhost")
        port = int(os.getenv("MCP_PORT", "8000"))
        logger.info(f"Starting SSE server on {host}:{port}")
        
        async with mcp.server.sse.sse_server(host=host, port=port) as server_context:
            await server.run(
                server_context.read_stream,
                server_context.write_stream,
                server.create_initialization_options()
            )
    else:
        # Run stdio server (default)
        logger.info("Starting stdio server")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 