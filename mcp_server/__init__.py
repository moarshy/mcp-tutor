"""
MCP Server module for educational tutoring system.

This module provides:
- GitHub repository ingestion and processing
- Semantic chunking of documentation
- Content analysis and educational metadata extraction
"""

from .content_processing import (
    GitHubRepositoryIngester,
    DocumentProcessor,
    PreparedDocument,
    RepositoryContent,
    DocumentType,
)

__all__ = [
    "GitHubRepositoryIngester",
    "DocumentProcessor", 
    "PreparedDocument",
    "RepositoryContent",
    "DocumentType",
]

__version__ = "0.1.0" 