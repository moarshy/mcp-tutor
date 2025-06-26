import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
import subprocess
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class RepositoryContent(BaseModel):
    """Represents a cloned GitHub repository with metadata"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    repo_url: str = Field(..., description="GitHub repository URL")
    local_path: Path = Field(..., description="Local path where repository is cloned")
    branch: str = Field(default="main", description="Git branch that was cloned")
    commit_hash: str = Field(..., description="Git commit hash of cloned state")
    repo_name: str = Field(..., description="Repository name extracted from URL")
    
    @field_validator('repo_url')
    @classmethod
    def validate_repo_url(cls, v):
        if not v.startswith(('http://', 'https://', 'git@')):
            raise ValueError('Repository URL must be a valid git URL')
        return v
    
    @field_validator('commit_hash')
    @classmethod
    def validate_commit_hash(cls, v):
        if len(v) < 7:
            raise ValueError('Commit hash must be at least 7 characters')
        return v

class DocumentType(str, Enum):
    """Types of prepared documents"""
    DOCUMENTATION = "documentation"
    CODE_EXAMPLE = "code_example"
    CHANGELOG = "changelog"
    API_REFERENCE = "api_reference"

class PreparedDocument(BaseModel):
    """
    Represents a complete, self-contained document prepared for MCP tools
    This is the "chunk" in our Tool-Augmented Generation approach
    """
    id: str = Field(..., description="Unique identifier for the document")
    doc_type: DocumentType = Field(..., description="Type of document")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Complete document content")
    source_paths: List[str] = Field(default_factory=list, description="Source files that contributed to this document")
    
    # Metadata for tool retrieval
    tool_key: str = Field(..., description="Key used by MCP tools to retrieve this document")
    description: str = Field(default="", description="Brief description for tool help")
    
    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.now)

class DocumentProcessor:
    """
    Document-level processor for Tool-Augmented Generation (TAG)
    
    Philosophy:
    - Each "chunk" is a complete, self-contained document
    - Code examples are aggregated from multiple source files
    - Documents are prepared for specific MCP tool retrieval
    - No semantic search - tools request specific documents by key
    """
    
    def __init__(self, max_doc_lines: int = 1000, max_changelog_lines: int = 300):
        self.max_doc_lines = max_doc_lines
        self.max_changelog_lines = max_changelog_lines
        self.prepared_docs: Dict[str, PreparedDocument] = {}
    
    async def prepare_all_documents(self, repo: RepositoryContent) -> List[PreparedDocument]:
        """
        Main entry point: Prepare all documents from a repository
        Returns complete, self-contained documents ready for MCP tools
        """
        prepared_docs = []
        
        # 1. Prepare raw documentation (copy entire .md files)
        docs = await self._prepare_documentation(repo)
        prepared_docs.extend(docs)
        
        # 2. Prepare aggregated code examples
        examples = await self._prepare_code_examples(repo)
        prepared_docs.extend(examples)
        
        # 3. Prepare changelogs (truncated if needed)
        changelogs = await self._prepare_changelogs(repo)
        prepared_docs.extend(changelogs)
        
        # Store for tool retrieval
        for doc in prepared_docs:
            self.prepared_docs[doc.tool_key] = doc
        
        return prepared_docs
    
    async def _prepare_documentation(self, repo: RepositoryContent) -> List[PreparedDocument]:
        """
        Strategy 1: Copy raw documentation files as complete documents
        Each .md/.mdx file becomes one PreparedDocument
        """
        docs = []
        doc_files = await self._find_documentation_files(repo.local_path)
        
        for doc_file in doc_files:
            try:
                content = doc_file.read_text(encoding='utf-8')
                
                # Skip very small files
                if len(content.strip()) < 100:
                    continue
                
                # Extract title from first heading or filename
                title = self._extract_title_from_content(content) or doc_file.stem
                
                # Create tool key from relative path
                relative_path = doc_file.relative_to(repo.local_path)
                tool_key = str(relative_path).replace('/', '_').replace('.md', '').replace('.mdx', '')
                
                doc = PreparedDocument(
                    id=f"doc_{tool_key}",
                    doc_type=DocumentType.DOCUMENTATION,
                    title=title,
                    content=content,
                    source_paths=[str(relative_path)],
                    tool_key=tool_key,
                    description=f"Documentation: {title}"
                )
                
                docs.append(doc)
                
            except Exception as e:
                print(f"Warning: Could not process documentation file {doc_file}: {e}")
                continue
        
        return docs
    
    async def _prepare_code_examples(self, repo: RepositoryContent) -> List[PreparedDocument]:
        """
        Strategy 2: Aggregate code examples into complete, self-contained documents
        Each example directory becomes one large PreparedDocument with all source files
        """
        examples = []
        examples_dir = repo.local_path / "examples"
        
        if not examples_dir.exists():
            return examples
        
        for example_dir in examples_dir.iterdir():
            if not example_dir.is_dir():
                continue
            
            try:
                # Aggregate all source files in the example
                aggregated_content = await self._aggregate_example_files(example_dir)
                
                if not aggregated_content.strip():
                    continue
                
                # Truncate if too long
                if len(aggregated_content.split('\n')) > self.max_doc_lines:
                    lines = aggregated_content.split('\n')
                    aggregated_content = '\n'.join(lines[:self.max_doc_lines])
                    aggregated_content += f"\n\n... (truncated at {self.max_doc_lines} lines)"
                
                # Get all source files that contributed
                source_paths = [
                    str(f.relative_to(repo.local_path)) 
                    for f in example_dir.rglob('*.py')
                    if f.is_file()
                ] + [
                    str(f.relative_to(repo.local_path)) 
                    for f in example_dir.rglob('*.ts')
                    if f.is_file()
                ] + [
                    str(f.relative_to(repo.local_path)) 
                    for f in example_dir.rglob('*.js')
                    if f.is_file()
                ] + [
                    str(f.relative_to(repo.local_path)) 
                    for f in example_dir.rglob('package.json')
                    if f.is_file()
                ]
                
                doc = PreparedDocument(
                    id=f"example_{example_dir.name}",
                    doc_type=DocumentType.CODE_EXAMPLE,
                    title=f"Code Example: {example_dir.name.replace('-', ' ').title()}",
                    content=aggregated_content,
                    source_paths=source_paths,
                    tool_key=example_dir.name,
                    description=f"Complete code example for {example_dir.name}"
                )
                
                examples.append(doc)
                
            except Exception as e:
                print(f"Warning: Could not process example {example_dir.name}: {e}")
                continue
        
        return examples
    
    async def _aggregate_example_files(self, example_dir: Path) -> str:
        """
        Aggregate multiple source files into one self-contained document
        Each file becomes a fenced code block with filename as header
        """
        content_parts = [f"# {example_dir.name.replace('-', ' ').title()} Example\n"]
        
        # Common files to include in order
        priority_files = ['package.json', 'requirements.txt', 'pyproject.toml', 'README.md']
        code_files = []
        
        # Collect all relevant files
        for file_path in example_dir.rglob('*'):
            if file_path.is_file() and not self._should_exclude_file(file_path):
                if file_path.name in priority_files:
                    # Add priority files first
                    try:
                        file_content = file_path.read_text(encoding='utf-8')
                        relative_path = file_path.relative_to(example_dir)
                        
                        content_parts.append(f"\n## {relative_path}\n")
                        content_parts.append(f"```{self._get_file_language(file_path)}")
                        content_parts.append(file_content)
                        content_parts.append("```\n")
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {e}")
                else:
                    code_files.append(file_path)
        
        # Add code files
        for file_path in sorted(code_files):
            try:
                file_content = file_path.read_text(encoding='utf-8')
                relative_path = file_path.relative_to(example_dir)
                
                content_parts.append(f"\n## {relative_path}\n")
                content_parts.append(f"```{self._get_file_language(file_path)}")
                content_parts.append(file_content)
                content_parts.append("```\n")
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
                continue
        
        return '\n'.join(content_parts)
    
    async def _prepare_changelogs(self, repo: RepositoryContent) -> List[PreparedDocument]:
        """
        Strategy 3: Prepare changelogs (truncate if too long)
        Each CHANGELOG.md becomes one PreparedDocument
        """
        changelogs = []
        
        for changelog_path in repo.local_path.rglob('CHANGELOG.md'):
            try:
                content = changelog_path.read_text(encoding='utf-8')
                
                # Truncate if too long
                lines = content.split('\n')
                if len(lines) > self.max_changelog_lines:
                    content = '\n'.join(lines[:self.max_changelog_lines])
                    content += f"\n\n... (truncated at {self.max_changelog_lines} lines)"
                
                # Create tool key from path
                relative_path = changelog_path.relative_to(repo.local_path)
                package_name = relative_path.parent.name if relative_path.parent.name != '.' else 'main'
                tool_key = f"changelog_{package_name}"
                
                doc = PreparedDocument(
                    id=f"changelog_{package_name}",
                    doc_type=DocumentType.CHANGELOG,
                    title=f"Changelog: {package_name}",
                    content=content,
                    source_paths=[str(relative_path)],
                    tool_key=tool_key,
                    description=f"Changelog for {package_name}"
                )
                
                changelogs.append(doc)
                
            except Exception as e:
                print(f"Warning: Could not process changelog {changelog_path}: {e}")
                continue
        
        return changelogs
    
    def get_document_by_key(self, tool_key: str) -> Optional[PreparedDocument]:
        """Retrieve a prepared document by its tool key (used by MCP tools)"""
        return self.prepared_docs.get(tool_key)
    
    def list_available_documents(self) -> List[str]:
        """List all available document keys for MCP tools"""
        return list(self.prepared_docs.keys())
    
    async def _find_documentation_files(self, repo_path: Path) -> List[Path]:
        """Find all documentation files (.md/.mdx) in the repository"""
        doc_files = []
        
        for pattern in ['**/*.md', '**/*.mdx']:
            for file_path in repo_path.glob(pattern):
                if (file_path.is_file() and 
                    not self._should_exclude_file(file_path) and
                    not self._should_exclude_documentation_file(file_path)):
                    doc_files.append(file_path)
        
        return doc_files
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing"""
        exclude_patterns = {
            'node_modules', '.git', '.github', 'dist', 'build', 
            '.next', '.vscode', '__pycache__', '.pytest_cache',
            'coverage', '.nyc_output', '.coverage', 'htmlcov',
            '.env', '.venv', 'venv', 'env', '.tox',
            'logs', 'log', 'tmp', 'temp', '.tmp'
        }
        
        return any(pattern in file_path.parts for pattern in exclude_patterns)
    
    def _should_exclude_documentation_file(self, file_path: Path) -> bool:
        """Check if documentation file should be excluded from educational content"""
        filename_lower = file_path.name.lower()
        
        # Files that are not educational content
        excluded_filenames = {
            # Legal and licensing
            'license.md', 'license', 'licence.md', 'licence',
            'copyright.md', 'copyright', 'legal.md', 'legal',
            'terms.md', 'terms', 'privacy.md', 'privacy',
            
            # Meta documentation (not educational content)
            # 'readme.md', 'readme', 
            'index.md',
            'changelog.md', 'changelog', 'changes.md', 'changes',
            'history.md', 'history', 'releases.md', 'releases',
            
            # Contributing and development process
            'contributing.md', 'contributing', 'contribute.md', 'contribute',
            'code_of_conduct.md', 'code-of-conduct.md', 'conduct.md',
            'security.md', 'security', 'support.md', 'support',
            'acknowledgments.md', 'acknowledgements.md', 'thanks.md',    
        }
        
        # Check exact filename matches
        if filename_lower in excluded_filenames:
            return True
        
        # Check filename patterns
        exclude_patterns = [
            # Version specific files
            r'^v\d+\.\d+.*\.md$',  # v1.0.md, v2.1.0.md
            r'^\d+\.\d+.*\.md$',   # 1.0.md, 2.1.0.md
            
            # Template files
            r'.*template.*\.md$',
            r'.*example.*\.md$',
            r'.*sample.*\.md$',
            r'.*test.*\.md$',
            r'.*demo.*\.md$',
            
            # Hidden files
            r'^\.',
            
            # Backup/temp files
            r'.*\.bak$',
            r'.*\.tmp$',
            r'.*\.backup$',
            r'.*~$'
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, filename_lower):
                return True
        
        # Check parent directory patterns (for deeply nested excluded content)
        path_parts_lower = [part.lower() for part in file_path.parts]
        excluded_directories = {
            'templates', 'examples', 'samples', 'tests', 'test',
            'demos', 'playground', 'experimental', 'draft', 'drafts',
            'archive', 'archived', 'old', 'legacy', 'deprecated',
            'private', 'internal', 'temp', 'tmp'
        }
        
        return any(excluded_dir in path_parts_lower for excluded_dir in excluded_directories)
    
    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """Extract title from the first heading in markdown content"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None
    
    def _get_file_language(self, file_path: Path) -> str:
        """Get language identifier for code fencing"""
        suffix = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.js': 'javascript',
            '.json': 'json',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.txt': 'text'
        }
        return language_map.get(suffix, 'text')
    


class GitHubRepositoryIngester:
    """
    Purpose: Convert GitHub documentation into complete, self-contained documents
    Focus: Tool-Augmented Generation (TAG) with document-level preparation
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.processor = DocumentProcessor()
    
    async def clone_repository(self, repo_url: str, branch: str = "main") -> RepositoryContent:
        """Clone and validate repository structure"""
        try:
            # Extract repository name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            
            # Create temporary directory for cloning
            temp_path = Path(self.temp_dir) / f"repo_{repo_name}_{os.getpid()}"
            
            if temp_path.exists():
                shutil.rmtree(temp_path)
            
            # Clone repository
            clone_cmd = [
                'git', 'clone', 
                '--depth', '1',  # Shallow clone for efficiency
                '--branch', branch,
                repo_url, 
                str(temp_path)
            ]
            
            result = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to clone repository: {stderr.decode()}")
            
            # Get commit hash
            commit_cmd = ['git', 'rev-parse', 'HEAD']
            commit_result = await asyncio.create_subprocess_exec(
                *commit_cmd,
                cwd=temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            commit_stdout, _ = await commit_result.communicate()
            commit_hash = commit_stdout.decode().strip()
            
            return RepositoryContent(
                repo_url=repo_url,
                local_path=temp_path,
                branch=branch,
                commit_hash=commit_hash,
                repo_name=repo_name
            )
            
        except Exception as e:
            # Cleanup on error
            if 'temp_path' in locals() and temp_path.exists():
                shutil.rmtree(temp_path)
            raise RuntimeError(f"Failed to clone repository {repo_url}: {str(e)}")
    
    async def prepare_documents(self, repo: RepositoryContent) -> List[PreparedDocument]:
        """
        Main method: Prepare complete, self-contained documents for MCP tools
        This replaces the complex chunking with document-level preparation
        """
        return await self.processor.prepare_all_documents(repo)
    
    def get_document_by_key(self, tool_key: str) -> Optional[PreparedDocument]:
        """Get a prepared document by its tool key (for MCP tool implementation)"""
        return self.processor.get_document_by_key(tool_key)
    
    def list_available_documents(self) -> List[str]:
        """List all available document keys (for MCP tool help)"""
        return self.processor.list_available_documents()
    
    async def ingest_repository(self, repo_url: str, branch: str = "main") -> None:
        """Complete ingestion workflow: clone repository and prepare all documents"""
        try:
            # Clone repository
            repo_content = await self.clone_repository(repo_url, branch)
            
            # Prepare documents
            prepared_docs = await self.prepare_documents(repo_content)
            
            # Clean up the cloned repository (we have the processed documents)
            self.cleanup(repo_content)
            
            logger.info(f"Ingested {len(prepared_docs)} documents from {repo_url}")
            
        except Exception as e:
            logger.error(f"Failed to ingest repository {repo_url}: {e}")
            raise

    def cleanup(self, repo: RepositoryContent) -> None:
        """Clean up temporary repository files"""
        if repo.local_path.exists():
            shutil.rmtree(repo.local_path) 