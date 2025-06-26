"""
MCP Tools implementation for educational tutoring.
Contains all model-controlled tools for document access and search.
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

import mcp.types as types
from mcp_server.content_processing import GitHubRepositoryIngester, PreparedDocument, DocumentType

logger = logging.getLogger(__name__)


class MCPTools:
    """MCP Tools handler for educational content access"""
    
    def __init__(self, ingester: GitHubRepositoryIngester):
        self.ingester = ingester
    
    def get_tools_list(self) -> List[types.Tool]:
        """Return list of available MCP tools"""
        return [
            types.Tool(
                name="search_mcp_concepts",
                description="Search MCP documentation for specific concepts, patterns, or examples",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "Concept to search for (e.g., 'tools', 'prompts', 'server implementation')"
                        },
                        "doc_type": {
                            "type": "string", 
                            "enum": ["documentation", "code_example", "changelog", "any"],
                            "description": "Type of document to search in",
                            "default": "any"
                        }
                    },
                    "required": ["query"]
                },
                annotations={
                    "title": "MCP Concept Search",
                    "readOnlyHint": True,
                }
            ),
            
            types.Tool(
                name="get_document_by_key",
                description="Retrieve a specific prepared document by its key",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_key": {
                            "type": "string",
                            "description": "The tool_key of the document to retrieve"
                        }
                    },
                    "required": ["document_key"]
                },
                annotations={
                    "title": "Get Document",
                    "readOnlyHint": True,
                    "idempotentHint": True
                }
            ),
            
            types.Tool(
                name="list_available_documents", 
                description="List all available document keys and their descriptions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_type_filter": {
                            "type": "string",
                            "enum": ["documentation", "code_example", "changelog", "all"],
                            "description": "Filter by document type",
                            "default": "all"
                        }
                    }
                },
                annotations={
                    "title": "List Documents",
                    "readOnlyHint": True,
                    "idempotentHint": True
                }
            ),
            
            types.Tool(
                name="get_code_example",
                description="Retrieve working code examples for MCP concepts",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "concept": {
                            "type": "string",
                            "description": "MCP concept needing example (e.g., 'server', 'tools', 'prompts')"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["typescript", "python", "javascript", "any"],
                            "description": "Programming language preference",
                            "default": "any"
                        }
                    },
                    "required": ["concept"]
                },
                annotations={
                    "title": "Get Code Example",
                    "readOnlyHint": True,
                    "idempotentHint": True
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle tool calls and route to appropriate methods"""
        
        if name == "search_mcp_concepts":
            return await self._search_concepts(
                query=arguments.get("query", ""),
                doc_type=arguments.get("doc_type", "any")
            )
            
        elif name == "get_document_by_key":
            return await self._get_document_by_key(
                document_key=arguments.get("document_key", "")
            )
            
        elif name == "list_available_documents":
            return await self._list_available_documents(
                doc_type_filter=arguments.get("doc_type_filter", "all")
            )
            
        elif name == "get_code_example":
            return await self._get_code_example(
                concept=arguments.get("concept", ""),
                language=arguments.get("language", "any")
            )
            
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _search_concepts(self, query: str, doc_type: str) -> List[types.TextContent]:
        """Search through prepared documents for concepts"""
        if not query.strip():
            return [types.TextContent(type="text", text="Error: Query cannot be empty")]
        
        if not self.ingester.processor.prepared_docs:
            return [types.TextContent(
                type="text", 
                text="No documents loaded. Server may still be initializing - please try again in a moment."
            )]
        
        query_lower = query.lower()
        matching_docs = []
        
        for doc_key, doc in self.ingester.processor.prepared_docs.items():
            # Filter by document type if specified
            if doc_type != "any" and doc.doc_type.value != doc_type:
                continue
                
            # Search in title, description, and content
            if (query_lower in doc.title.lower() or 
                query_lower in doc.description.lower() or 
                query_lower in doc.content.lower()):
                
                # Create a snippet from the content
                content_lines = doc.content.split('\n')
                snippet_lines = []
                for i, line in enumerate(content_lines):
                    if query_lower in line.lower():
                        # Include context around the match
                        start = max(0, i - 2)
                        end = min(len(content_lines), i + 3)
                        snippet_lines.extend(content_lines[start:end])
                        break
                
                snippet = '\n'.join(snippet_lines[:10])  # Limit snippet length
                if len(snippet_lines) > 10:
                    snippet += "\n... (truncated)"
                
                matching_docs.append({
                    'key': doc_key,
                    'title': doc.title,
                    'type': doc.doc_type.value,
                    'description': doc.description,
                    'snippet': snippet
                })
        
        if not matching_docs:
            return [types.TextContent(
                type="text", 
                text=f"No documents found matching query: '{query}'"
            )]
        
        # Format results
        result_text = f"Found {len(matching_docs)} documents matching '{query}':\n\n"
        for i, doc in enumerate(matching_docs[:5], 1):  # Limit to top 5 results
            result_text += f"## {i}. {doc['title']} ({doc['type']})\n"
            result_text += f"**Key:** `{doc['key']}`\n"
            result_text += f"**Description:** {doc['description']}\n"
            if doc['snippet']:
                result_text += f"**Relevant snippet:**\n```\n{doc['snippet']}\n```\n"
            result_text += "\n---\n\n"
        
        if len(matching_docs) > 5:
            result_text += f"... and {len(matching_docs) - 5} more results.\n"
        
        return [types.TextContent(type="text", text=result_text)]

    async def _get_document_by_key(self, document_key: str) -> List[types.TextContent]:
        """Retrieve a specific document by its key"""
        if not document_key.strip():
            return [types.TextContent(type="text", text="Error: Document key cannot be empty")]
        
        doc = self.ingester.get_document_by_key(document_key)
        if not doc:
            available_keys = self.ingester.list_available_documents()
            return [types.TextContent(
                type="text", 
                text=f"Document '{document_key}' not found. Available keys: {', '.join(available_keys[:10])}"
            )]
        
        result_text = f"# {doc.title}\n\n"
        result_text += f"**Type:** {doc.doc_type.value}\n"
        result_text += f"**Description:** {doc.description}\n"
        result_text += f"**Source files:** {', '.join(doc.source_paths)}\n"
        result_text += f"**Created:** {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        result_text += "---\n\n"
        result_text += doc.content
        
        return [types.TextContent(type="text", text=result_text)]

    async def _list_available_documents(self, doc_type_filter: str) -> List[types.TextContent]:
        """List all available documents with their metadata"""
        if not self.ingester.processor.prepared_docs:
            return [types.TextContent(
                type="text",
                text="No documents available. Server may still be initializing - please try again in a moment."
            )]
        
        docs_by_type = {
            "documentation": [],
            "code_example": [],
            "changelog": []
        }
        
        for doc_key, doc in self.ingester.processor.prepared_docs.items():
            if doc_type_filter == "all" or doc.doc_type.value == doc_type_filter:
                docs_by_type[doc.doc_type.value].append({
                    'key': doc_key,
                    'title': doc.title,
                    'description': doc.description
                })
        
        result_text = "# Available Documents\n\n"
        
        for doc_type, docs in docs_by_type.items():
            if docs and (doc_type_filter == "all" or doc_type_filter == doc_type):
                result_text += f"## {doc_type.replace('_', ' ').title()} ({len(docs)} documents)\n\n"
                for doc in docs:
                    result_text += f"- **{doc['key']}**: {doc['title']}\n"
                    result_text += f"  _{doc['description']}_\n\n"
                result_text += "\n"
        
        return [types.TextContent(type="text", text=result_text)]

    async def _get_code_example(self, concept: str, language: str) -> List[types.TextContent]:
        """Get code examples for a specific concept"""
        if not concept.strip():
            return [types.TextContent(type="text", text="Error: Concept cannot be empty")]
        
        concept_lower = concept.lower()
        matching_examples = []
        
        for doc_key, doc in self.ingester.processor.prepared_docs.items():
            if doc.doc_type == DocumentType.CODE_EXAMPLE:
                if concept_lower in doc.title.lower() or concept_lower in doc.content.lower():
                    # Check language preference if specified
                    if language != "any":
                        if language.lower() in doc.content.lower():
                            matching_examples.append(doc)
                    else:
                        matching_examples.append(doc)
        
        if not matching_examples:
            return [types.TextContent(
                type="text",
                text=f"No code examples found for concept '{concept}' with language preference '{language}'"
            )]
        
        # Return the best matching example
        best_example = matching_examples[0]
        result_text = f"# Code Example: {best_example.title}\n\n"
        result_text += f"**Description:** {best_example.description}\n"
        result_text += f"**Source files:** {', '.join(best_example.source_paths)}\n\n"
        result_text += "---\n\n"
        result_text += best_example.content
        
        if len(matching_examples) > 1:
            result_text += f"\n\n*Note: Found {len(matching_examples)} examples. Use 'search_mcp_concepts' to see all matches.*"
        
        return [types.TextContent(type="text", text=result_text)] 