# Phase 1: Content Extraction and Parsing Implementation

import os
import pickle
import hashlib
import json
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Set, Union
from pathlib import Path
import git
import dspy
from urllib.parse import urlparse
import re
import frontmatter
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv
import logging

load_dotenv()

# =============================================================================
# Constants
# =============================================================================

CACHE_DIR = ".cache"
MAX_CHARS = 3000

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================
dspy.configure(lm=dspy.LM("openai/gpt-4o"))


# =============================================================================
# Data Models
# =============================================================================

class DocumentType(Enum):
    """Document type"""
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    GUIDE = "guide"
    API = "api"
    EXAMPLE = "example"
    OVERVIEW = "overview"
    CONFIG = "configuration"
    TROUBLESHOOTING = "troubleshooting"
    CHANGELOG = "changelog"
    OTHER = "other"

class ComplexityLevel(Enum):
    """Complexity level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class DocumentMetadata(BaseModel):
    """Enhanced metadata extracted from a document"""
    # Basic extracted metadata
    title: str
    headings: List[str]
    code_blocks: List[Dict[str, str]] 
    links: List[Dict[str, str]] 
    frontmatter: Dict[str, Any]
    word_count: int
    estimated_reading_time: int
    last_modified: Optional[datetime]
    file_size: int
    
    # LLM-enhanced metadata
    doc_type: Optional[DocumentType] = None
    complexity: Optional[ComplexityLevel] = None
    topics: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    
    # Computed metadata
    semantic_summary: Optional[str] = None
    primary_language: Optional[str] = None
    has_examples: bool = False
    has_api_docs: bool = False
    difficulty_score: Optional[float] = None  # 0-1 scale

class DocumentNode(BaseModel):
    """Represents a single documentation file"""
    id: str
    path: str  # relative path from repo root
    filename: str
    content: str
    metadata: DocumentMetadata
    parent_path: Optional[str] = None
    children_paths: List[str] = Field(default_factory=list)
    
    # Enhanced relationships
    related_documents: List[str] = Field(default_factory=list)
    prerequisite_documents: List[str] = Field(default_factory=list)
    follow_up_documents: List[str] = Field(default_factory=list)
    
class DocumentTree(BaseModel):
    """Complete documentation tree structure"""
    repo_url: str
    repo_name: str
    root_path: str
    nodes: Dict[str, DocumentNode] = Field(..., description="Path to node mapping")
    tree_structure: Dict[str, List[str]] = Field(..., description="Folder to list of files/folders mapping")
    cross_references: Dict[str, List[str]] = Field(..., description="File to list of referenced files mapping")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Enhanced tree-level metadata
    document_categories: Dict[DocumentType, List[str]] = Field(default_factory=dict)
    complexity_distribution: Dict[ComplexityLevel, int] = Field(default_factory=dict)
    topic_hierarchy: Dict[str, List[str]] = Field(default_factory=dict)
    learning_paths: List[List[str]] = Field(default_factory=list)

# =============================================================================
# Enhanced DSPy Signatures
# =============================================================================

class DocumentParser(dspy.Signature):
    """Parse a markdown document and extract structured metadata with semantic understanding"""
    content: str = dspy.InputField(desc="Raw markdown content")
    filename: str = dspy.InputField(desc="Document filename")
    
    # Structured outputs
    semantic_summary: str = dspy.OutputField(desc="2-3 sentence summary of the document's purpose and content")
    key_concepts: List[str] = dspy.OutputField(desc="JSON list of 3-5 key concepts or terms covered in this document")
    learning_objectives: List[str] = dspy.OutputField(desc="JSON list of what a reader should learn from this document")
    prerequisites: List[str] = dspy.OutputField(desc="JSON list of concepts/knowledge needed before reading this document")

class DocumentClassifier(dspy.Signature):
    """Classify document type, complexity, and extract topics"""
    title: str = dspy.InputField(desc="Document title")
    content: str = dspy.InputField(desc="Document content sample")
    headings: str = dspy.InputField(desc="Document headings list")
    semantic_summary: str = dspy.InputField(desc="Semantic summary of the document")
    
    doc_type: DocumentType = dspy.OutputField(desc="Document type: tutorial, reference, guide, api, example, overview, configuration, troubleshooting, changelog, other")
    complexity: ComplexityLevel = dspy.OutputField(desc="Complexity level: beginner, intermediate, advanced")
    topics: List[str] = dspy.OutputField(desc="JSON list of 3-7 main topics/technologies covered")
    difficulty_score: float = dspy.OutputField(desc="Difficulty score from 0.0 (very easy) to 1.0 (very hard)")

class CrossReferenceAnalyzer(dspy.Signature):
    """Analyze cross-references and document relationships"""
    document_content: str = dspy.InputField(desc="Document content to analyze")
    document_topics: List[str] = dspy.InputField(desc="Topics covered in this document")
    available_documents: List[str] = dspy.InputField(desc="JSON list of available document paths with their topics")
    
    explicit_references: List[str] = dspy.OutputField(desc="JSON list of document paths explicitly referenced via links")
    related_documents: List[str] = dspy.OutputField(desc="JSON list of document paths that are topically related but not explicitly linked")
    prerequisite_docs: List[str] = dspy.OutputField(desc="JSON list of document paths that should be read before this one")
    follow_up_docs: List[str] = dspy.OutputField(desc="JSON list of document paths that logically follow this one")

class LearningPathGenerator(dspy.Signature):
    """Generate learning paths from document relationships"""
    documents_info: Dict[str, DocumentMetadata] = dspy.InputField(desc="JSON object with document paths, types, complexity, and topics")
    target_complexity: ComplexityLevel = dspy.InputField(desc="Target complexity level: beginner, intermediate, advanced")
    
    learning_path: List[str] = dspy.OutputField(desc="JSON list of document paths in optimal learning order")
    path_rationale: str = dspy.OutputField(desc="Explanation of why this learning path sequence makes sense")

# =============================================================================
# Repository Manager (unchanged)
# =============================================================================

class RepoManager:
    """Handles repository cloning, caching, and file discovery"""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_repo_cache_path(self, repo_url: str) -> Path:
        """Generate cache path for repository"""
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()
        repo_name = urlparse(repo_url).path.strip('/').replace('/', '_')
        return self.cache_dir / f"{repo_name}_{repo_hash}"
    
    def _get_tree_cache_path(self, repo_url: str) -> Path:
        """Generate cache path for processed document tree"""
        cache_path = self._get_repo_cache_path(repo_url)
        return cache_path / "document_tree.pkl"
    
    def clone_or_update_repo(self, repo_url: str, force_update: bool = False) -> Path:
        """Clone repository or update if it exists"""
        repo_path = self._get_repo_cache_path(repo_url)
        
        if repo_path.exists() and not force_update:
            print(f"Repository already cached at {repo_path}")
            try:
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
                print("Updated repository with latest changes")
            except Exception as e:
                print(f"Warning: Could not update repository: {e}")
            return repo_path
        
        if repo_path.exists():
            import shutil
            shutil.rmtree(repo_path)
            
        print(f"Cloning repository to {repo_path}")
        git.Repo.clone_from(repo_url, repo_path)
        return repo_path
    
    def find_documentation_files(self, repo_path: Path) -> List[Path]:
        """Find all markdown files in repository"""
        md_files = []
        for ext in ['*.md', '*.mdx']:
            md_files.extend(repo_path.rglob(ext))
        
        excluded_patterns = {
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'venv', 'env', '.venv', 'build', 'dist', 'tests'
        }
        
        filtered_files = []
        for file_path in md_files:
            if not any(excluded in file_path.parts for excluded in excluded_patterns):
                filtered_files.append(file_path)

        # Remove common non-content files
        filtered_files = [
            file for file in filtered_files 
            if not file.name.lower().startswith(('license', 'contributing', 'code_of_conduct', 'security', 'patents'))
        ]
        
        return sorted(filtered_files)
    
    def save_tree_cache(self, tree: DocumentTree, repo_url: str):
        """Save processed document tree to cache"""
        cache_path = self._get_tree_cache_path(repo_url)
        cache_path.parent.mkdir(exist_ok=True)
        
        with open(cache_path, 'wb') as f:
            pickle.dump(tree, f)
        print(f"Saved document tree cache to {cache_path}")
    
    def load_tree_cache(self, repo_url: str) -> Optional[DocumentTree]:
        """Load processed document tree from cache"""
        cache_path = self._get_tree_cache_path(repo_url)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                tree = pickle.load(f)
            print(f"Loaded document tree cache from {cache_path}")
            return tree
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None

# =============================================================================
# Enhanced Content Processors
# =============================================================================

class ContentExtractor:
    """Extract structured content from markdown files"""
    
    @staticmethod
    def extract_basic_metadata(content: str, filepath: Path) -> Dict[str, Any]:
        """Extract basic metadata from markdown content"""
        try:
            post = frontmatter.loads(content)
            frontmatter_data = post.metadata
            clean_content = post.content
        except:
            frontmatter_data = {}
            clean_content = content
        
        title = ContentExtractor._extract_title(clean_content, frontmatter_data, filepath.name)
        headings = ContentExtractor._extract_headings(clean_content)
        code_blocks = ContentExtractor._extract_code_blocks(clean_content)
        links = ContentExtractor._extract_links(clean_content)
        
        word_count = len(clean_content.split())
        reading_time = max(1, word_count // 200)
        
        file_size = filepath.stat().st_size if filepath.exists() else 0
        last_modified = datetime.fromtimestamp(filepath.stat().st_mtime) if filepath.exists() else None
        
        # Compute additional features
        primary_language = ContentExtractor._get_primary_language(code_blocks)
        has_examples = ContentExtractor._has_code_examples(code_blocks, clean_content)
        has_api_docs = ContentExtractor._has_api_documentation(clean_content, headings)
        
        return {
            'title': title,
            'headings': headings,
            'code_blocks': code_blocks,
            'links': links,
            'frontmatter': frontmatter_data,
            'word_count': word_count,
            'estimated_reading_time': reading_time,
            'last_modified': last_modified,
            'file_size': file_size,
            'primary_language': primary_language,
            'has_examples': has_examples,
            'has_api_docs': has_api_docs
        }
    
    @staticmethod
    def _extract_title(content: str, frontmatter_data: dict, filename: str) -> str:
        """Extract document title"""
        if 'title' in frontmatter_data:
            return frontmatter_data['title']
        
        h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return filename.replace('.md', '').replace('.mdx', '').replace('_', ' ').replace('-', ' ').title()
    
    @staticmethod
    def _extract_headings(content: str) -> List[str]:
        """Extract all headings from content"""
        headings = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append(f"{'  ' * (level-1)}{text}")
        return headings
    
    @staticmethod
    def _extract_code_blocks(content: str) -> List[Dict[str, str]]:
        """Extract code blocks with language information"""
        code_blocks = []
        pattern = r'```(\w+)?\n(.*?)\n```'
        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1) or 'text'
            code_content = match.group(2).strip()
            code_blocks.append({
                'language': language,
                'content': code_content
            })
        return code_blocks
    
    @staticmethod
    def _extract_links(content: str) -> List[Dict[str, str]]:
        """Extract markdown links"""
        links = []
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, content):
            text = match.group(1)
            url = match.group(2)
            link_type = 'internal' if not url.startswith(('http', 'https')) else 'external'
            links.append({
                'text': text,
                'url': url,
                'type': link_type
            })
        return links
    
    @staticmethod
    def _get_primary_language(code_blocks: List[Dict[str, str]]) -> Optional[str]:
        """Determine the primary programming language"""
        if not code_blocks:
            return None
        
        # Count languages by total characters
        lang_chars = {}
        for block in code_blocks:
            lang = block['language'].lower()
            if lang not in ['text', 'txt', '']:
                lang_chars[lang] = lang_chars.get(lang, 0) + len(block['content'])
        
        if not lang_chars:
            return None
        
        return max(lang_chars.items(), key=lambda x: x[1])[0]
    
    @staticmethod
    def _has_code_examples(code_blocks: List[Dict[str, str]], content: str) -> bool:
        """Check if document contains practical code examples"""
        if not code_blocks:
            return False
        
        # Look for example indicators
        example_indicators = ['example', 'demo', 'sample', 'usage', 'how to use']
        content_lower = content.lower()
        
        return any(indicator in content_lower for indicator in example_indicators) and len(code_blocks) > 0
    
    @staticmethod
    def _has_api_documentation(content: str, headings: List[str]) -> bool:
        """Check if document contains API documentation"""
        api_indicators = ['api', 'endpoint', 'method', 'function', 'parameter', 'response', 'request']
        
        content_lower = content.lower()
        headings_lower = ' '.join(headings).lower()
        
        return any(indicator in content_lower or indicator in headings_lower for indicator in api_indicators)

# =============================================================================
# Enhanced DSPy Modules
# =============================================================================

class DocumentParserModule(dspy.Module):
    """Enhanced DSPy module for comprehensive document parsing"""
    
    def __init__(self):
        super().__init__()
        self.parser = dspy.ChainOfThought(DocumentParser)
        self.classifier = dspy.ChainOfThought(DocumentClassifier)
    
    def forward(self, content: str, filename: str, filepath: Path) -> DocumentMetadata:
        """Parse document and extract comprehensive metadata"""
        
        # Extract basic metadata
        basic_data = ContentExtractor.extract_basic_metadata(content, filepath)
        
        try:
            # Get LLM-enhanced semantic understanding
            parse_result = self.parser(
                content=content[:4000],  # Use more content for better understanding
                filename=filename
            )
            
            # Parse LLM outputs
            key_concepts = self._safe_json_parse(parse_result.key_concepts, [])
            learning_objectives = self._safe_json_parse(parse_result.learning_objectives, [])
            prerequisites = self._safe_json_parse(parse_result.prerequisites, [])
            
            # Classify the document
            classification = self.classifier(
                title=basic_data['title'],
                content=content[:3000],
                headings=str(basic_data['headings'][:10]),
                semantic_summary=parse_result.semantic_summary
            )
            
            # Parse classification outputs
            topics = self._safe_json_parse(classification.topics, [])
            doc_type = self._safe_enum_parse(classification.doc_type, DocumentType, DocumentType.OTHER)
            complexity = self._safe_enum_parse(classification.complexity, ComplexityLevel, ComplexityLevel.INTERMEDIATE)
            
        except Exception as e:
            print(f"LLM parsing failed for {filename}: {e}")
            # Fallback to basic classification
            key_concepts = []
            learning_objectives = []
            prerequisites = []
            topics = []
            doc_type = DocumentType.OTHER
            complexity = ComplexityLevel.INTERMEDIATE
            parse_result = type('obj', (object,), {
                'semantic_summary': f"Documentation for {basic_data['title']}"
            })()
            classification = type('obj', (object,), {'difficulty_score': 0.5})()
        
        # Create comprehensive metadata
        return DocumentMetadata(
            # Basic metadata
            title=basic_data['title'],
            headings=basic_data['headings'],
            code_blocks=basic_data['code_blocks'],
            links=basic_data['links'],
            frontmatter=basic_data['frontmatter'],
            word_count=basic_data['word_count'],
            estimated_reading_time=basic_data['estimated_reading_time'],
            last_modified=basic_data['last_modified'],
            file_size=basic_data['file_size'],
            
            # LLM-enhanced metadata
            doc_type=doc_type,
            complexity=complexity,
            topics=topics,
            key_concepts=key_concepts,
            prerequisites=prerequisites,
            learning_objectives=learning_objectives,
            semantic_summary=parse_result.semantic_summary,
            
            # Computed metadata
            primary_language=basic_data['primary_language'],
            has_examples=basic_data['has_examples'],
            has_api_docs=basic_data['has_api_docs'],
            difficulty_score=getattr(classification, 'difficulty_score', 0.5)
        )
    
    def _safe_json_parse(self, json_str: str, default: Any) -> Any:
        """Safely parse JSON string with fallback"""
        try:
            return json.loads(json_str)
        except:
            return default
    
    def _safe_enum_parse(self, value: str, enum_class, default):
        """Safely parse enum value with fallback"""
        try:
            return enum_class(value.lower())
        except:
            return default

class EnhancedCrossReferenceModule(dspy.Module):
    """Enhanced cross-reference analysis with relationship detection"""
    
    def __init__(self):
        super().__init__()
        self.analyzer = dspy.ChainOfThought(CrossReferenceAnalyzer)
    
    def forward(self, document: DocumentNode, all_documents: Dict[str, DocumentNode]) -> Dict[str, List[str]]:
        """Analyze comprehensive document relationships"""
        
        # Prepare document info for LLM
        doc_info = {}
        for path, node in all_documents.items():
            doc_info[path] = {
                'title': node.metadata.title,
                'topics': node.metadata.topics,
                'type': node.metadata.doc_type.value if node.metadata.doc_type else 'other',
                'complexity': node.metadata.complexity.value if node.metadata.complexity else 'intermediate'
            }
        
        try:
            result = self.analyzer(
                document_content=document.content[:4000],
                document_topics=json.dumps(document.metadata.topics),
                available_documents=json.dumps(doc_info)
            )
            
            return {
                'explicit_references': self._safe_json_parse(result.explicit_references, []),
                'related_documents': self._safe_json_parse(result.related_documents, []),
                'prerequisite_docs': self._safe_json_parse(result.prerequisite_docs, []),
                'follow_up_docs': self._safe_json_parse(result.follow_up_docs, [])
            }
        
        except Exception as e:
            print(f"Enhanced cross-reference analysis failed: {e}")
            # Fallback to regex-based analysis
            return self._fallback_analysis(document, list(all_documents.keys()))
    
    def _fallback_analysis(self, document: DocumentNode, available_docs: List[str]) -> Dict[str, List[str]]:
        """Fallback regex-based analysis"""
        references = []
        
        for link_match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', document.content):
            link_url = link_match.group(2)
            
            if link_url.startswith(('http', 'https', 'mailto')):
                continue
                
            clean_link = link_url.split('#')[0].split('?')[0]
            
            for doc_path in available_docs:
                if clean_link in doc_path or doc_path.endswith(clean_link):
                    references.append(doc_path)
                    break
        
        return {
            'explicit_references': list(set(references)),
            'related_documents': [],
            'prerequisite_docs': [],
            'follow_up_docs': []
        }
    
    def _safe_json_parse(self, json_str: str, default: Any) -> Any:
        """Safely parse JSON string with fallback"""
        try:
            return json.loads(json_str)
        except:
            return default

class LearningPathModule(dspy.Module):
    """Generate optimal learning paths for different complexity levels"""
    
    def __init__(self):
        super().__init__()
        self.path_generator = dspy.ChainOfThought(LearningPathGenerator)
    
    def forward(self, documents: Dict[str, DocumentNode], target_complexity: ComplexityLevel) -> List[List[str]]:
        """Generate learning paths for target complexity"""
        
        # Prepare simplified document info
        doc_info = {}
        for path, node in documents.items():
            doc_info[path] = {
                'title': node.metadata.title,
                'type': node.metadata.doc_type.value if node.metadata.doc_type else 'other',
                'complexity': node.metadata.complexity.value if node.metadata.complexity else 'intermediate',
                'topics': node.metadata.topics[:3],  # Top 3 topics
                'prerequisites': node.metadata.prerequisites[:3]  # Top 3 prerequisites
            }
        
        try:
            result = self.path_generator(
                documents_info=json.dumps(doc_info),
                target_complexity=target_complexity.value
            )
            
            learning_path = self._safe_json_parse(result.learning_path, [])
            
            # Validate that all documents in path exist
            valid_path = [doc for doc in learning_path if doc in documents]
            
            return [valid_path] if valid_path else []
        
        except Exception as e:
            print(f"Learning path generation failed: {e}")
            return self._fallback_path_generation(documents, target_complexity)
    
    def _fallback_path_generation(self, documents: Dict[str, DocumentNode], target_complexity: ComplexityLevel) -> List[List[str]]:
        """Fallback path generation based on heuristics"""
        # Simple heuristic: group by complexity and type
        relevant_docs = []
        
        for path, node in documents.items():
            if node.metadata.complexity == target_complexity:
                relevant_docs.append((path, node))
        
        if not relevant_docs:
            return []
        
        # Sort by type priority (overview -> tutorial -> guide -> reference -> examples)
        type_priority = {
            DocumentType.OVERVIEW: 0,
            DocumentType.TUTORIAL: 1,
            DocumentType.GUIDE: 2,
            DocumentType.REFERENCE: 3,
            DocumentType.EXAMPLE: 4,
            DocumentType.OTHER: 5
        }
        
        relevant_docs.sort(key=lambda x: type_priority.get(x[1].metadata.doc_type, 5))
        
        return [[doc[0] for doc in relevant_docs[:10]]]  # Max 10 documents per path
    
    def _safe_json_parse(self, json_str: str, default: Any) -> Any:
        """Safely parse JSON string with fallback"""
        try:
            return json.loads(json_str)
        except:
            return default

# =============================================================================
# Enhanced Document Tree Builder
# =============================================================================

class DocumentTreeBuilder:
    """Enhanced document tree builder with comprehensive analysis"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.repo_manager = RepoManager(cache_dir)
        self.parser_module = DocumentParserModule()
        self.cross_ref_module = EnhancedCrossReferenceModule()
        self.learning_path_module = LearningPathModule()
    
    def build_tree(self, repo_url: str, force_rebuild: bool = False) -> DocumentTree:
        """Build comprehensive document tree with enhanced analysis"""
        
        # Check cache first
        if not force_rebuild:
            cached_tree = self.repo_manager.load_tree_cache(repo_url)
            if cached_tree:
                print("Loaded from cache - use force_rebuild=True for fresh analysis")
                return cached_tree
        
        print(f"Building enhanced document tree for {repo_url}")
        
        # Clone/update repository
        repo_path = self.repo_manager.clone_or_update_repo(repo_url)
        
        # Find documentation files
        md_files = self.repo_manager.find_documentation_files(repo_path)
        print(f"Found {len(md_files)} documentation files")
        
        # Initialize tree structure
        repo_name = Path(repo_url).name.replace('.git', '')
        tree = DocumentTree(
            repo_url=repo_url,
            repo_name=repo_name,
            root_path=str(repo_path),
            nodes={},
            tree_structure={}
        )
        
        # Phase 1: Process each file with enhanced metadata extraction
        print("Phase 1: Processing documents with LLM analysis...")
        for file_path in md_files:
            relative_path = str(file_path.relative_to(repo_path))
            print(f"Processing: {relative_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
            
            doc_id = hashlib.md5(relative_path.encode()).hexdigest()
            
            # Extract comprehensive metadata using enhanced parser
            try:
                metadata = self.parser_module(content=content, filename=file_path.name, filepath=file_path)
            except Exception as e:
                print(f"Error parsing {relative_path}: {e}")
                continue
            
            # Create enhanced document node
            node = DocumentNode(
                id=doc_id,
                path=relative_path,
                filename=file_path.name,
                content=content,
                metadata=metadata,
                parent_path=str(file_path.parent.relative_to(repo_path)) if file_path.parent != repo_path else None
            )
            
            tree.nodes[relative_path] = node
        
        # Phase 2: Build relationships and cross-references
        print("Phase 2: Analyzing document relationships...")
        tree.tree_structure = self._build_tree_structure(tree.nodes)
        tree.cross_references = {}
        
        for path, node in tree.nodes.items():
            print(f"Analyzing relationships for: {path}")
            try:
                relationships = self.cross_ref_module(node, tree.nodes)
                
                # Update node relationships
                node.related_documents = relationships.get('related_documents', [])
                node.prerequisite_documents = relationships.get('prerequisite_docs', [])
                node.follow_up_documents = relationships.get('follow_up_docs', [])
                
                # Update tree cross-references (explicit links)
                tree.cross_references[path] = relationships.get('explicit_references', [])
                
            except Exception as e:
                print(f"Error analyzing relationships for {path}: {e}")
                tree.cross_references[path] = []
        
        # Phase 3: Build enhanced tree metadata
        print("Phase 3: Building tree-level metadata...")
        tree.document_categories = self._categorize_documents(tree.nodes)
        tree.complexity_distribution = self._analyze_complexity_distribution(tree.nodes)
        tree.topic_hierarchy = self._build_topic_hierarchy(tree.nodes)
        
        # Phase 4: Generate learning paths
        print("Phase 4: Generating learning paths...")
        tree.learning_paths = []
        for complexity in ComplexityLevel:
            paths = self.learning_path_module(tree.nodes, complexity)
            tree.learning_paths.extend(paths)
        
        # Cache the enhanced result
        self.repo_manager.save_tree_cache(tree, repo_url)
        
        print(f"Enhanced tree building complete!")
        print(f"- {len(tree.nodes)} documents processed")
        print(f"- {len(tree.document_categories)} document categories")
        print(f"- {len(tree.learning_paths)} learning paths generated")
        
        return tree
    
    def _build_tree_structure(self, nodes: Dict[str, DocumentNode]) -> Dict[str, List[str]]:
        """Build hierarchical tree structure"""
        structure = {}
        
        for path, node in nodes.items():
            dir_path = str(Path(path).parent)
            if dir_path == '.':
                dir_path = 'root'
            
            if dir_path not in structure:
                structure[dir_path] = []
            
            structure[dir_path].append(path)
        
        return structure
    
    def _categorize_documents(self, nodes: Dict[str, DocumentNode]) -> Dict[DocumentType, List[str]]:
        """Categorize documents by type"""
        categories = {}
        
        for path, node in nodes.items():
            doc_type = node.metadata.doc_type or DocumentType.OTHER
            
            if doc_type not in categories:
                categories[doc_type] = []
            
            categories[doc_type].append(path)
        
        return categories
    
    def _analyze_complexity_distribution(self, nodes: Dict[str, DocumentNode]) -> Dict[ComplexityLevel, int]:
        """Analyze complexity distribution across documents"""
        distribution = {level: 0 for level in ComplexityLevel}
        
        for node in nodes.values():
            complexity = node.metadata.complexity or ComplexityLevel.INTERMEDIATE
            distribution[complexity] += 1
        
        return distribution
    
    def _build_topic_hierarchy(self, nodes: Dict[str, DocumentNode]) -> Dict[str, List[str]]:
        """Build topic hierarchy from document topics"""
        topic_docs = {}
        
        for path, node in nodes.items():
            for topic in node.metadata.topics:
                if topic not in topic_docs:
                    topic_docs[topic] = []
                topic_docs[topic].append(path)
        
        return topic_docs

# =============================================================================
# Enhanced Usage Example and Testing
# =============================================================================

def print_enhanced_summary(tree: DocumentTree):
    """Print comprehensive summary of the enhanced document tree"""
    
    print(f"\n{'='*60}")
    print(f"ENHANCED DOCUMENT TREE ANALYSIS")
    print(f"{'='*60}")
    
    print(f"Repository: {tree.repo_name}")
    print(f"URL: {tree.repo_url}")
    print(f"Total documents: {len(tree.nodes)}")
    print(f"Last updated: {tree.last_updated}")
    
    # Document type distribution
    print(f"\n--- Document Type Distribution ---")
    for doc_type, docs in tree.document_categories.items():
        print(f"{doc_type.value.title()}: {len(docs)} documents")
        # Show a few examples
        for doc in docs[:2]:
            title = tree.nodes[doc].metadata.title
            print(f"  • {title}")
        if len(docs) > 2:
            print(f"  ... and {len(docs) - 2} more")
    
    # Complexity distribution
    print(f"\n--- Complexity Distribution ---")
    for complexity, count in tree.complexity_distribution.items():
        print(f"{complexity.value.title()}: {count} documents")
    
    # Topic analysis
    print(f"\n--- Top Topics ---")
    sorted_topics = sorted(tree.topic_hierarchy.items(), key=lambda x: len(x[1]), reverse=True)
    for topic, docs in sorted_topics[:10]:
        print(f"{topic}: {len(docs)} documents")
    
    # Enhanced metadata insights
    print(f"\n--- Content Insights ---")
    total_concepts = sum(len(node.metadata.key_concepts) for node in tree.nodes.values())
    total_objectives = sum(len(node.metadata.learning_objectives) for node in tree.nodes.values())
    docs_with_examples = sum(1 for node in tree.nodes.values() if node.metadata.has_examples)
    docs_with_api = sum(1 for node in tree.nodes.values() if node.metadata.has_api_docs)
    
    print(f"Total key concepts extracted: {total_concepts}")
    print(f"Total learning objectives: {total_objectives}")
    print(f"Documents with examples: {docs_with_examples}")
    print(f"Documents with API docs: {docs_with_api}")
    
    # Language analysis
    languages = {}
    for node in tree.nodes.values():
        if node.metadata.primary_language:
            lang = node.metadata.primary_language
            languages[lang] = languages.get(lang, 0) + 1
    
    print(f"\n--- Primary Languages ---")
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{lang}: {count} documents")
    
    # Learning paths
    print(f"\n--- Generated Learning Paths ---")
    print(f"Total learning paths: {len(tree.learning_paths)}")
    for i, path in enumerate(tree.learning_paths[:3]):
        print(f"\nPath {i+1} ({len(path)} documents):")
        for j, doc_path in enumerate(path[:5]):
            node = tree.nodes[doc_path]
            complexity = node.metadata.complexity.value if node.metadata.complexity else 'unknown'
            print(f"  {j+1}. {node.metadata.title} ({complexity})")
        if len(path) > 5:
            print(f"  ... and {len(path) - 5} more documents")
    
    # Document relationships
    print(f"\n--- Document Relationships ---")
    total_related = sum(len(node.related_documents) for node in tree.nodes.values())
    total_prereqs = sum(len(node.prerequisite_documents) for node in tree.nodes.values())
    total_followups = sum(len(node.follow_up_documents) for node in tree.nodes.values())
    
    print(f"Total related document connections: {total_related}")
    print(f"Total prerequisite relationships: {total_prereqs}")
    print(f"Total follow-up relationships: {total_followups}")
    
    # Most connected documents
    connected_docs = [
        (path, len(node.related_documents) + len(node.prerequisite_documents) + len(node.follow_up_documents))
        for path, node in tree.nodes.items()
    ]
    connected_docs.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n--- Most Connected Documents ---")
    for path, connection_count in connected_docs[:5]:
        if connection_count > 0:
            node = tree.nodes[path]
            print(f"{node.metadata.title}: {connection_count} connections")
            print(f"  Type: {node.metadata.doc_type.value if node.metadata.doc_type else 'unknown'}")
            print(f"  Topics: {', '.join(node.metadata.topics[:3])}")

def analyze_specific_document(tree: DocumentTree, doc_path: str):
    """Detailed analysis of a specific document"""
    
    if doc_path not in tree.nodes:
        print(f"Document {doc_path} not found")
        available = list(tree.nodes.keys())[:5]
        print(f"Available documents (sample): {available}")
        return
    
    node = tree.nodes[doc_path]
    metadata = node.metadata
    
    print(f"\n{'='*60}")
    print(f"DETAILED DOCUMENT ANALYSIS")
    print(f"{'='*60}")
    
    print(f"Path: {doc_path}")
    print(f"Title: {metadata.title}")
    print(f"Type: {metadata.doc_type.value if metadata.doc_type else 'unknown'}")
    print(f"Complexity: {metadata.complexity.value if metadata.complexity else 'unknown'}")
    print(f"Difficulty Score: {metadata.difficulty_score:.2f}" if metadata.difficulty_score else "N/A")
    
    print(f"\n--- Content Statistics ---")
    print(f"Word count: {metadata.word_count:,}")
    print(f"Reading time: {metadata.estimated_reading_time} minutes")
    print(f"Headings: {len(metadata.headings)}")
    print(f"Code blocks: {len(metadata.code_blocks)}")
    print(f"Links: {len(metadata.links)}")
    print(f"Primary language: {metadata.primary_language or 'None'}")
    print(f"Has examples: {metadata.has_examples}")
    print(f"Has API docs: {metadata.has_api_docs}")
    
    print(f"\n--- Semantic Summary ---")
    print(metadata.semantic_summary or "No summary available")
    
    print(f"\n--- Topics Covered ---")
    for topic in metadata.topics:
        print(f"• {topic}")
    
    print(f"\n--- Key Concepts ---")
    for concept in metadata.key_concepts:
        print(f"• {concept}")
    
    print(f"\n--- Learning Objectives ---")
    for objective in metadata.learning_objectives:
        print(f"• {objective}")
    
    print(f"\n--- Prerequisites ---")
    for prereq in metadata.prerequisites:
        print(f"• {prereq}")
    
    print(f"\n--- Document Relationships ---")
    print(f"Related documents ({len(node.related_documents)}):")
    for related in node.related_documents[:3]:
        if related in tree.nodes:
            related_title = tree.nodes[related].metadata.title
            print(f"  • {related_title}")
    
    print(f"Prerequisite documents ({len(node.prerequisite_documents)}):")
    for prereq in node.prerequisite_documents[:3]:
        if prereq in tree.nodes:
            prereq_title = tree.nodes[prereq].metadata.title
            print(f"  • {prereq_title}")
    
    print(f"Follow-up documents ({len(node.follow_up_documents)}):")
    for followup in node.follow_up_documents[:3]:
        if followup in tree.nodes:
            followup_title = tree.nodes[followup].metadata.title
            print(f"  • {followup_title}")

def main():
    """Enhanced example usage"""
    
    # Initialize enhanced builder
    builder = DocumentTreeBuilder()
    
    # Test with a documentation repository
    repo_url = "https://github.com/modelcontextprotocol/docs"
    
    try:
        print("Building enhanced document tree...")
        print("This will take longer due to LLM analysis of each document.")
        
        # Build enhanced tree
        tree = builder.build_tree(repo_url, force_rebuild=False)
        
        # Print comprehensive analysis
        print_enhanced_summary(tree)
        
        # Analyze a specific document
        if tree.nodes:
            # Find an interesting document to analyze
            tutorial_docs = tree.document_categories.get(DocumentType.TUTORIAL, [])
            overview_docs = tree.document_categories.get(DocumentType.OVERVIEW, [])
            
            analyze_doc = None
            if tutorial_docs:
                analyze_doc = tutorial_docs[0]
            elif overview_docs:
                analyze_doc = overview_docs[0]
            else:
                analyze_doc = list(tree.nodes.keys())[0]
            
            analyze_specific_document(tree, analyze_doc)
        
        return tree
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()