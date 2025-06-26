"""
MCP Server main entry point.
Implements the educational tutoring MCP server with tools that use prepared documents.
"""

import asyncio
import logging
import pickle
import hashlib
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from mcp_server.content_processing import GitHubRepositoryIngester
from mcp_server.tools import MCPTools
from mcp_server.prompts import MCPPrompts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPTutorServer:
    """MCP Server for educational tutoring using prepared documents"""
    
    def __init__(self, output_dir: str = ".cache", use_cache: bool = True):
        self.server = Server("mcp-educational-tutor")
        self.ingester = GitHubRepositoryIngester()
        self.output_dir = Path(output_dir)
        self.use_cache = use_cache
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize modular components
        self.tools_handler = MCPTools(self.ingester)
        self.prompts_handler = MCPPrompts(self.tools_handler)
        
        # Flag to track if content is initialized
        self.content_initialized = False
        
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
        """Initialize content by processing MCP documentation repository with caching support"""
        if self.content_initialized:
            return
            
        try:
            logger.info("Initializing MCP documentation content...")
            
            # Repository configuration
            repo_url = "https://github.com/modelcontextprotocol/docs"
            branch = "main"
            
            # Generate cache filename based on repo URL and branch
            repo_hash = hashlib.md5(f"{repo_url}#{branch}".encode()).hexdigest()
            cache_file = self.output_dir / f"mcp_docs_{repo_hash}.pickle"
            
            # Check if we should use cache
            if self.use_cache and cache_file.exists():
                logger.info(f"Loading cached content from {cache_file}")
                try:
                    with open(cache_file, 'rb') as f:
                        cached_data = pickle.load(f)
                    
                    # Restore the cached documents to the ingester
                    self.ingester.processor.prepared_docs = cached_data['prepared_docs']
                    
                    doc_count = len(self.ingester.processor.prepared_docs)
                    logger.info(f"Successfully loaded {doc_count} documents from cache")
                    
                    # Log summary by type
                    if doc_count > 0:
                        type_counts = {}
                        for doc in self.ingester.processor.prepared_docs.values():
                            doc_type = doc.doc_type.value
                            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                        
                        logger.info(f"Document types: {type_counts}")
                    
                    self.content_initialized = True
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to load cache file {cache_file}: {e}")
                    logger.info("Proceeding with fresh repository processing...")
            
            # If not using cache or cache doesn't exist, remove any existing cache file
            if not self.use_cache and cache_file.exists():
                logger.info(f"Removing existing cache file: {cache_file}")
                cache_file.unlink()
            
            # Process repository fresh
            logger.info(f"Attempting to clone and process {repo_url}")
            
            # Use the ingester to process the repository
            await self.ingester.ingest_repository(repo_url, branch)
            
            # Get count of processed documents
            doc_count = len(self.ingester.processor.prepared_docs)
            logger.info(f"Successfully processed content: {doc_count} documents prepared")
            
            # Log summary by type
            if doc_count > 0:
                type_counts = {}
                for doc in self.ingester.processor.prepared_docs.values():
                    doc_type = doc.doc_type.value
                    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                
                logger.info(f"Document types: {type_counts}")
                
                # Save to cache for future use
                cache_data = {
                    'prepared_docs': self.ingester.processor.prepared_docs,
                    'repo_url': repo_url,
                    'branch': branch,
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                try:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(cache_data, f)
                    logger.info(f"Cached content saved to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to save cache: {e}")
            else:
                logger.warning("No documents were processed from the repository")
                
            self.content_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize content: {e}")
            logger.warning("Continuing with empty content - MCP tools will provide fallback responses")
            # Don't raise, just log the error and continue with empty content
            self.content_initialized = True

    async def run(self):
        """Run the MCP server with stdio transport"""
        # Initialize content first, only once
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
