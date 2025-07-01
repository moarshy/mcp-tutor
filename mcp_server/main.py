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

from mcp_server.course_management import CourseContentProcessor
from mcp_server.course_tools import CourseTools
from mcp_server.logging_config import setup_logging
from mcp_server.tools import get_tool_definitions, handle_tool_call

# Optional SSE support
try:
    import mcp.server.sse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False


# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("educational-tutor")

# Global course processor and tools
course_processor: CourseContentProcessor
course_tools: CourseTools


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return get_tool_definitions()


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    global course_processor, course_tools
    return await handle_tool_call(name, arguments, course_processor, course_tools)


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
    global course_processor, course_tools
    
    # Initialize course processor and tools
    try:
        COURSE_DIR = os.getenv("COURSE_DIR", "course_output")
        course_processor = CourseContentProcessor(COURSE_DIR)
        course_tools = CourseTools(course_processor)
        logger.info(f"Course processor initialized with directory: {COURSE_DIR}")
    except Exception as e:
        logger.error(f"Failed to initialize course processor: {e}", exc_info=True)
        # Exit or handle gracefully if the course processor is essential
        return
    
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