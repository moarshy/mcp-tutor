"""
MCP Server main entry point.
Implements the educational tutoring MCP server with tools that use prepared documents.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from .content_processing import GitHubRepositoryIngester
from .tools import MCPTools
from .prompts import MCPPrompts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPTutorServer:
    """MCP Server for educational tutoring using prepared documents"""
    
    def __init__(self):
        self.server = Server("mcp-educational-tutor")
        self.ingester = GitHubRepositoryIngester()
        
        # Initialize modular components
        self.tools_handler = MCPTools(self.ingester)
        self.prompts_handler = MCPPrompts(self.tools_handler)
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register MCP handlers for tools, prompts, and resources"""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools for document access and tutoring"""
            return self.tools_handler.get_tools_list()

        @self.server.list_prompts()
        async def list_prompts() -> List[types.Prompt]:
            """List available educational prompts for MCP tutoring"""
            return self.prompts_handler.get_prompts_list()

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, Any]) -> types.GetPromptResult:
            """Handle prompt requests using the prompts handler"""
            try:
                return await self.prompts_handler.handle_prompt_request(name, arguments)
            except Exception as e:
                logger.error(f"Error generating prompt '{name}': {e}")
                # Return error as a prompt result
                return types.GetPromptResult(
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=f"Error generating prompt: {str(e)}"
                            )
                        )
                    ]
                )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls using the tools handler"""
            try:
                return await self.tools_handler.handle_tool_call(name, arguments)
            except Exception as e:
                logger.error(f"Error calling tool '{name}': {e}")
                return [types.TextContent(
                    type="text", 
                    text=f"Error: {str(e)}"
                )]

    async def initialize_content(self):
        """Initialize content by processing MCP documentation repository"""
        try:
            logger.info("Initializing MCP documentation content...")
            
            # Process the MCP documentation repository
            repo_url = "https://github.com/modelcontextprotocol/docs"
            branch = "main"
            
            # Use the ingester to process the repository
            await self.ingester.ingest_repository(repo_url, branch)
            
            # Get count of processed documents
            doc_count = len(self.ingester.processor.prepared_docs)
            logger.info(f"Successfully initialized content: {doc_count} documents prepared")
            
            # Log summary by type
            type_counts = {}
            for doc in self.ingester.processor.prepared_docs.values():
                doc_type = doc.doc_type.value
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            logger.info(f"Document types: {type_counts}")
            
        except Exception as e:
            logger.error(f"Failed to initialize content: {e}")
            raise

    async def run(self):
        """Run the MCP server with stdio transport"""
        # Initialize content first
        await self.initialize_content()
        
        logger.info("Starting MCP Educational Tutor Server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point"""
    server = MCPTutorServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
