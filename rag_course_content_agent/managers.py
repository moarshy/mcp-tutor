from typing import List, Optional, Dict, Any, Union
import hashlib
import logging
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import git
import pickle
import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException
import openai

from .models import (
    AnalyzedDocument, LearningModule, LearningPath, ContentSummary,
    GeneratedContent, ContentChunk, Exercise, AssessmentQuestion,
    LearningObjective, CodeExample, DocumentMetadata, DocumentClassification,
    DependencyRelation, DocumentChunk, QueryResult, CodeBlock, DocumentType
)
from .modules import (
    ModuleDiscoverer, ModuleOrderer, QueryGenerator,
    ContentSynthesizer, ExerciseGenerator, AssessmentCreator,
    ObjectiveWriter, CodeExampleExtractor, DocumentClassifier,
    DependencyExtractor, DocumentSummarizer
)

logger = logging.getLogger(__name__)

class RepoManager:
    """Manages repository operations (cloning, caching, file discovery)"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_repo_cache_path(self, repo_url: str) -> Path:
        """Get the cache path for a repository"""
        repo_name = urlparse(repo_url).path.strip('/').replace('/', '_')
        return self.cache_dir / repo_name
    
    def _get_analysis_cache_path(self, repo_url: str) -> Path:
        """Get the cache path for analysis results"""
        repo_name = urlparse(repo_url).path.strip('/').replace('/', '_')
        return self.cache_dir / f"{repo_name}_analysis.pkl"
    
    def clone_or_update_repo(self, repo_url: str, force_update: bool = False) -> Path:
        """Clone or update a repository"""
        
        repo_path = self._get_repo_cache_path(repo_url)
        
        if repo_path.exists() and not force_update:
            logger.info(f"Using cached repository: {repo_path}")
            return repo_path
        
        try:
            if repo_path.exists():
                # Update existing repo
                logger.info(f"Updating repository: {repo_url}")
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
            else:
                # Clone new repo
                logger.info(f"Cloning repository: {repo_url}")
                git.Repo.clone_from(repo_url, repo_path)
            
            return repo_path
            
        except Exception as e:
            logger.error(f"Error with repository {repo_url}: {e}")
            raise
    
    def find_documentation_files(self, repo_path: Path, include_folders: Optional[List[str]] = None) -> List[Path]:
        """Find documentation files in a repository"""
        
        doc_files = []
        
        # Common documentation folders
        doc_folders = include_folders or [
            "docs", "documentation", "doc", "guides", "tutorials", 
            "examples", "wiki", "help", "reference", "api", "manual"
        ]
        
        # Common documentation file patterns
        doc_patterns = [
            "*.md", "*.rst", "*.txt", "*.adoc", "*.asciidoc",
            "README*", "CHANGELOG*", "CONTRIBUTING*", "GUIDE*",
            "TUTORIAL*", "EXAMPLE*", "HOWTO*", "FAQ*"
        ]
        
        try:
            # Search in specific documentation folders
            for folder in doc_folders:
                folder_path = repo_path / folder
                if folder_path.exists() and folder_path.is_dir():
                    for pattern in doc_patterns:
                        doc_files.extend(folder_path.rglob(pattern))
            
            # Search in root for common doc files
            for pattern in doc_patterns:
                doc_files.extend(repo_path.glob(pattern))
            
            # Remove duplicates and filter
            unique_files = []
            seen = set()
            
            for file_path in doc_files:
                if file_path.resolve() not in seen:
                    seen.add(file_path.resolve())
                    # Skip very large files (>1MB) and binary files
                    if file_path.stat().st_size < 1024 * 1024:
                        unique_files.append(file_path)
            
            logger.info(f"Found {len(unique_files)} documentation files")
            return unique_files
            
        except Exception as e:
            logger.error(f"Error finding documentation files: {e}")
            return []
    
    def save_analysis_cache(self, analysis_results: List[AnalyzedDocument], repo_url: str):
        """Save analysis results to cache"""
        try:
            cache_path = self._get_analysis_cache_path(repo_url)
            
            # Convert to serializable format
            cache_data = {
                'analysis_results': [
                    {
                        'metadata': doc.metadata.dict(),
                        'classification': doc.classification.dict(),
                        'content': doc.content,
                        'dependencies': [dep.dict() for dep in doc.dependencies],
                        'summary': doc.summary
                    }
                    for doc in analysis_results
                ],
                'timestamp': hashlib.md5(str(repo_url).encode()).hexdigest()
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"Saved analysis cache: {cache_path}")
            
        except Exception as e:
            logger.error(f"Error saving analysis cache: {e}")
    
    def load_analysis_cache(self, repo_url: str) -> Optional[List[AnalyzedDocument]]:
        """Load analysis results from cache"""
        try:
            cache_path = self._get_analysis_cache_path(repo_url)
            
            if not cache_path.exists():
                return None
            
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Reconstruct AnalyzedDocument objects
            analysis_results = []
            for doc_data in cache_data['analysis_results']:
                doc = AnalyzedDocument(
                    metadata=DocumentMetadata(**doc_data['metadata']),
                    classification=DocumentClassification(**doc_data['classification']),
                    content=doc_data['content'],
                    dependencies=[DependencyRelation(**dep) for dep in doc_data['dependencies']],
                    summary=doc_data['summary']
                )
                analysis_results.append(doc)
            
            logger.info(f"Loaded {len(analysis_results)} documents from cache")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error loading analysis cache: {e}")
            return None

class DocAnalyzer:
    """Analyzes technical documentation using DSPy modules"""
    
    def __init__(self):
        self.classifier = DocumentClassifier()
        self.dependency_extractor = DependencyExtractor()
        self.summarizer = DocumentSummarizer()

    def _extract_metadata(self, file_path: Path, content: str) -> DocumentMetadata:
        """Extract metadata from document content"""
        
        # Extract title (first H1 or filename)
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem
        
        # Extract all headings
        headings = re.findall(r'^#{1,6} (.+)$', content, re.MULTILINE)
        
        # Extract code blocks
        code_blocks = []
        code_pattern = r'```(\w+)?\n(.*?)\n```'
        for i, match in enumerate(re.finditer(code_pattern, content, re.DOTALL)):
            language = match.group(1) or 'text'
            code_content = match.group(2)
            
            # Calculate line numbers (approximate)
            lines_before = content[:match.start()].count('\n')
            lines_in_block = code_content.count('\n')
            
            code_blocks.append(CodeBlock(
                language=language,
                content=code_content,
                line_start=lines_before + 1,
                line_end=lines_before + lines_in_block + 1
            ))
        
        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        link_urls = [link[1] for link in links]
        
        # Word count
        word_count = len(content.split())
        
        return DocumentMetadata(
            file_path=str(file_path),
            title=title,
            headings=headings,
            code_blocks=code_blocks,
            links=link_urls,
            word_count=word_count
        )
    
    def analyze_document(self, file_path: Path, content: str) -> AnalyzedDocument:
        """Analyze a single document"""
        
        # Extract metadata
        metadata = self._extract_metadata(file_path, content)
        
        # Classify document
        classification = self.classifier(
            content=content,
            file_path=str(file_path),
            headings=metadata.headings
        )
        
        # Extract dependencies
        dependencies = self.dependency_extractor(
            content=content,
            title=metadata.title or "",
            headings=metadata.headings
        )
        
        # Generate document summary for contextual retrieval
        doc_summary = self.summarizer(
            content=content,
            title=metadata.title or file_path.stem,
            doc_type=classification.doc_type.value
        )
        
        return AnalyzedDocument(
            metadata=metadata,
            classification=classification,
            content=content,
            dependencies=dependencies,
            summary=doc_summary
        )
    
    def analyze_repository(self, file_paths: List[Path]) -> List[AnalyzedDocument]:
        """Analyze all documents in a repository"""
        analyzed_docs = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                analyzed_doc = self.analyze_document(file_path, content)
                analyzed_docs.append(analyzed_doc)
                
                logger.info(f"Analyzed {file_path}: {analyzed_doc.classification.doc_type} (confidence: {analyzed_doc.classification.confidence:.2f})")
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                continue
        
        return analyzed_docs
    
    def get_classified_docs(self, analyzed_docs: List[AnalyzedDocument]) -> Dict[DocumentType, List[AnalyzedDocument]]:
        """Group analyzed documents by classification"""
        classified = {doc_type: [] for doc_type in DocumentType}
        
        for doc in analyzed_docs:
            classified[doc.classification.doc_type].append(doc)
        
        return classified
    
    def build_dependency_map(self, analyzed_docs: List[AnalyzedDocument]) -> Dict[str, List[str]]:
        """Build a simple dependency map from analyzed documents"""
        dependency_map = {}
        
        for doc in analyzed_docs:
            for dep_relation in doc.dependencies:
                if dep_relation.concept not in dependency_map:
                    dependency_map[dep_relation.concept] = []
                dependency_map[dep_relation.concept].extend(dep_relation.prerequisites)
        
        # Remove duplicates
        for concept in dependency_map:
            dependency_map[concept] = list(set(dependency_map[concept]))
        
        return dependency_map

class VectorDB:
    """Vector database for contextual document retrieval"""
    
    def __init__(self, 
                 db_path: str = "./vector_db",
                 collection_name: str = "docs",
                 embedding_model: str = "text-embedding-3-small",
                 chunk_size: int = 800,
                 chunk_overlap: int = 100):
        
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except InvalidCollectionException:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI()
        
        logger.info(f"VectorDB initialized: {db_path}/{collection_name}")
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def _chunk_with_context(self, doc) -> List[DocumentChunk]:
        """Chunk documents with context preservation"""
        chunks = []
        content = doc.content
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        current_size = 0
        chunk_count = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            para_words = len(paragraph.split())
            
            # If adding this paragraph would exceed chunk size, create a chunk
            if current_size + para_words > self.chunk_size and current_chunk:
                # Create chunk
                chunk_id = f"{doc.metadata.file_path}_{chunk_count}"
                
                # Add context information
                context_info = f"Document: {doc.metadata.title}\n"
                if doc.metadata.headings:
                    context_info += f"Headings: {', '.join(doc.metadata.headings[:3])}\n"
                context_info += f"Type: {doc.classification.doc_type.value}\n\n"
                
                chunk_content = context_info + current_chunk
                
                chunk = DocumentChunk(
                    id=chunk_id,
                    content=chunk_content,
                    doc_type=doc.classification.doc_type.value,
                    title=doc.metadata.title or "",
                    file_path=doc.metadata.file_path,
                    metadata={
                        "headings": doc.metadata.headings,
                        "word_count": current_size,
                        "has_code": bool(doc.metadata.code_blocks),
                        "confidence": doc.classification.confidence,
                        "dependencies": [dep.concept for dep in doc.dependencies]
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_words = current_chunk.split()[-self.chunk_overlap:]
                current_chunk = " ".join(overlap_words) + " " + paragraph
                current_size = len(overlap_words) + para_words
                chunk_count += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                    current_size += para_words
                else:
                    current_chunk = paragraph
                    current_size = para_words
        
        # Add the last chunk
        if current_chunk:
            chunk_id = f"{doc.metadata.file_path}_{chunk_count}"
            
            context_info = f"Document: {doc.metadata.title}\n"
            if doc.metadata.headings:
                context_info += f"Headings: {', '.join(doc.metadata.headings[:3])}\n"
            context_info += f"Type: {doc.classification.doc_type.value}\n\n"
            
            chunk_content = context_info + current_chunk
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_content,
                doc_type=doc.classification.doc_type.value,
                title=doc.metadata.title or "",
                file_path=doc.metadata.file_path,
                metadata={
                    "headings": doc.metadata.headings,
                    "word_count": current_size,
                    "has_code": bool(doc.metadata.code_blocks),
                    "confidence": doc.classification.confidence,
                    "dependencies": [dep.concept for dep in doc.dependencies]
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def add_documents(self, analyzed_docs: List, batch_size: int = 50):
        """Add analyzed documents to the vector database"""
        
        all_chunks = []
        for doc in analyzed_docs:
            chunks = self._chunk_with_context(doc)
            all_chunks.extend(chunks)
        
        logger.info(f"Adding {len(all_chunks)} chunks to vector database")
        
        # Process in batches
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            
            # Prepare batch data
            ids = [chunk.id for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [
                {
                    "doc_type": chunk.doc_type,
                    "title": chunk.title,
                    "file_path": chunk.file_path,
                    **chunk.metadata
                }
                for chunk in batch
            ]
            
            # Generate embeddings
            embeddings = self._generate_embeddings(documents)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
    
    def query(self, 
              query_text: str, 
              n_results: int = 5,
              doc_types: Optional[List[str]] = None,
              concepts: Optional[List[str]] = None) -> List[QueryResult]:
        """Query the vector database"""
        
        # Generate query embedding
        query_embedding = self._generate_embeddings([query_text])[0]
        
        # Build where clause for filtering
        where_clause = {}
        if doc_types:
            where_clause["doc_type"] = {"$in": doc_types}
        
        # Execute query
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        
        # Convert to QueryResult objects
        query_results = []
        for i in range(len(results['ids'][0])):
            chunk = DocumentChunk(
                id=results['ids'][0][i],
                content=results['documents'][0][i],
                doc_type=results['metadatas'][0][i]['doc_type'],
                title=results['metadatas'][0][i]['title'],
                file_path=results['metadatas'][0][i]['file_path'],
                metadata=results['metadatas'][0][i]
            )
            
            query_result = QueryResult(
                chunk=chunk,
                similarity_score=1.0 - results['distances'][0][i],  # Convert distance to similarity
                relevance_explanation=f"Matched query: {query_text}"
            )
            query_results.append(query_result)
        
        return query_results
    
    def get_stats(self):
        """Get database statistics"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self):
        """Clear the collection"""
        try:
            # Delete the collection
            self.client.delete_collection(name=self.collection_name)
            
            # Recreate it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"Cleared collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

class VectorDBManager:
    """High-level manager for vector database operations"""
    
    def __init__(self, db_path: str = "./vector_db"):
        self.vector_db = VectorDB(db_path=db_path)
    
    def initialize_from_analysis(self, analyzed_docs: List):
        """Initialize vector database from analyzed documents"""
        logger.info(f"Initializing vector database with {len(analyzed_docs)} documents")
        self.vector_db.add_documents(analyzed_docs)
    
    def search(self, query: str, n_results: int = 5, doc_types: List[str] = None) -> List[QueryResult]:
        """Search the vector database"""
        return self.vector_db.query(query, n_results, doc_types)
    
    def search_by_heading(self, query: str, heading_keyword: str, n_results: int = 5) -> List[QueryResult]:
        """Search with a focus on specific headings"""
        
        # First search normally
        results = self.vector_db.query(query, n_results * 2)
        
        # Filter and re-rank based on heading matches
        heading_matches = []
        other_matches = []
        
        for result in results:
            headings = result.chunk.metadata.get('headings', [])
            if any(heading_keyword.lower() in heading.lower() for heading in headings):
                heading_matches.append(result)
            else:
                other_matches.append(result)
        
        # Return heading matches first, then others
        return (heading_matches + other_matches)[:n_results]
    
    def search_by_code_language(self, query: str, language: str, n_results: int = 5) -> List[QueryResult]:
        """Search for content with specific programming language"""
        
        # Search normally first
        results = self.vector_db.query(query, n_results * 2)
        
        # Filter for chunks that likely contain code in the specified language
        code_matches = []
        other_matches = []
        
        for result in results:
            content = result.chunk.content.lower()
            # Look for code blocks with the specified language
            if f"```{language}" in content or f"```{language.lower()}" in content:
                code_matches.append(result)
            # Or look for language-specific patterns
            elif language.lower() in content and "```" in content:
                code_matches.append(result)
            else:
                other_matches.append(result)
        
        return (code_matches + other_matches)[:n_results]
    
    def search_by_dependency(self, query: str, required_concept: str, n_results: int = 5) -> List[QueryResult]:
        """Search for content related to a specific concept dependency"""
        
        # Search normally first
        results = self.vector_db.query(query, n_results * 2)
        
        # Filter for chunks that mention the required concept
        concept_matches = []
        other_matches = []
        
        for result in results:
            dependencies = result.chunk.metadata.get('dependencies', [])
            content = result.chunk.content.lower()
            
            # Check if the concept is mentioned in dependencies or content
            if (required_concept.lower() in [dep.lower() for dep in dependencies] or
                required_concept.lower() in content):
                concept_matches.append(result)
            else:
                other_matches.append(result)
        
        return (concept_matches + other_matches)[:n_results]
    
    def get_chunk_analysis(self, chunk: DocumentChunk) -> Dict:
        """Get detailed analysis of a specific chunk"""
        
        return {
            "id": chunk.id,
            "doc_type": chunk.doc_type,
            "title": chunk.title,
            "word_count": chunk.metadata.get('word_count', 0),
            "has_code": chunk.metadata.get('has_code', False),
            "headings": chunk.metadata.get('headings', []),
            "dependencies": chunk.metadata.get('dependencies', []),
            "confidence": chunk.metadata.get('confidence', 0.0)
        }
    
    def find_learning_prerequisites(self, concept: str, n_results: int = 5) -> List[QueryResult]:
        """Find content that could serve as prerequisites for a concept"""
        
        # Search for foundational content
        prereq_query = f"introduction basics fundamentals {concept}"
        results = self.vector_db.query(prereq_query, n_results * 2)
        
        # Filter for content that's likely foundational
        foundational_matches = []
        other_matches = []
        
        for result in results:
            content = result.chunk.content.lower()
            title = result.chunk.title.lower()
            
            # Look for foundational keywords
            foundational_keywords = ["introduction", "basics", "fundamentals", "getting started", "overview"]
            if any(keyword in content or keyword in title for keyword in foundational_keywords):
                foundational_matches.append(result)
            else:
                other_matches.append(result)
        
        return (foundational_matches + other_matches)[:n_results]
    
    def clear_database(self):
        """Clear the entire database"""
        self.vector_db.clear_collection()

class PathBuilder:
    """Builds learning paths using LLM intelligence and vector search"""
    
    def __init__(self, analyzed_docs: List, vector_db_manager):
        self.analyzed_docs = analyzed_docs
        self.vector_db = vector_db_manager
        self.module_discoverer = ModuleDiscoverer()
        self.module_orderer = ModuleOrderer()
        self.query_generator = QueryGenerator()
    
    def _create_available_content_summary(self) -> str:
        """Create a brief summary of available content types"""
        doc_types = {}
        sample_topics = set()
        
        for doc in self.analyzed_docs:
            doc_type = doc.classification.doc_type.value
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # Add some sample topics
            if len(sample_topics) < 20:
                sample_topics.add(doc.metadata.title or "Untitled")
        
        summary = f"Available: {doc_types}. Sample topics: {', '.join(list(sample_topics)[:10])}"
        return summary
    
    def _search_content_for_module(self, module_title: str, difficulty_level: str) -> Dict[str, List[str]]:
        """Search for content related to a module using AI-generated queries"""
        
        content = {
            "tutorial": [],
            "concept": [],
            "example": [],
            "reference": []
        }
        
        # Create overview of available content for query generation
        available_content = self._create_available_content_summary()
        
        # Generate queries for each document type using LLM
        for doc_type in content.keys():
            logger.info(f"Generating search queries for {module_title} - {doc_type} - {difficulty_level}")
            
            try:
                # Generate intelligent search queries
                search_queries, reasoning = self.query_generator(
                    module_title=module_title,
                    difficulty_level=difficulty_level,
                    doc_type=doc_type,
                    available_content=available_content
                )
                
                logger.info(f"Generated queries for {doc_type}: {search_queries}")
                logger.info(f"Reasoning: {reasoning}")
                
                # Execute each generated query
                for query in search_queries:
                    try:
                        results = self.vector_db.search(
                            query=query,
                            n_results=3,
                            doc_types=[doc_type]
                        )
                        
                        chunk_ids = [result.chunk.id for result in results]
                        content[doc_type].extend(chunk_ids)
                        
                    except Exception as e:
                        logger.warning(f"Search failed for '{query}' in {doc_type}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Query generation failed for {module_title} - {doc_type}: {e}")
                # Fallback to simple query
                try:
                    results = self.vector_db.search(
                        query=f"{module_title} {doc_type}",
                        n_results=3,
                        doc_types=[doc_type]
                    )
                    chunk_ids = [result.chunk.id for result in results]
                    content[doc_type].extend(chunk_ids)
                except:
                    continue
        
        # Remove duplicates
        for doc_type in content:
            content[doc_type] = list(dict.fromkeys(content[doc_type]))  # Preserve order
        
        return content
    
    def _create_rich_content_summary(self) -> str:
        """Create rich content summary with complete document information"""
        
        # Group documents by type for better organization
        docs_by_type = {}
        for doc in self.analyzed_docs:
            doc_type = doc.classification.doc_type.value
            if doc_type not in docs_by_type:
                docs_by_type[doc_type] = []
            docs_by_type[doc_type].append(doc)
        
        summary_text = f"Available Documentation for Learning Path Creation:\n\n"
        summary_text += f"Total Documents: {len(self.analyzed_docs)}\n\n"
        
        # Add ALL documents organized by type - no limits
        for doc_type, docs in docs_by_type.items():
            summary_text += f"{doc_type.upper()} DOCUMENTS ({len(docs)} total):\n"
            
            # Include ALL documents - no truncation
            for i, doc in enumerate(docs):
                doc_context = f"""  {i+1}. Title: {doc.metadata.title or 'Untitled'}
     Headings: {', '.join(doc.metadata.headings)}
     Summary: {doc.summary}
"""
                summary_text += doc_context
            
            summary_text += "\n"
        
        return summary_text
    
    def _create_content_overview_for_ordering(self, modules: List[str]) -> str:
        """Create complete content overview for module ordering"""
        
        overview = f"Content Overview for Module Ordering:\n\n"
        overview += f"Proposed Modules: {', '.join(modules)}\n\n"
        
        # For each proposed module, show ALL related content
        for module in modules:
            overview += f"CONTENT AVAILABLE FOR '{module.upper()}':\n"
            
            # Find ALL documents that might relate to this module
            related_docs = []
            for doc in self.analyzed_docs:
                # Check if module name appears in title, headings, or summary
                search_text = f"{doc.metadata.title} {' '.join(doc.metadata.headings)} {doc.summary}".lower()
                if (module.lower() in search_text or 
                    any(word in search_text for word in module.lower().split())):
                    related_docs.append(doc)
            
            if related_docs:
                # Include ALL related docs - no limits
                for doc in related_docs:
                    overview += f"  - {doc.classification.doc_type.value}: {doc.metadata.title}\n"
                    overview += f"    Headings: {', '.join(doc.metadata.headings)}\n"
                    overview += f"    Summary: {doc.summary}\n"
            else:
                overview += f"  - No directly related content found for this module\n"
            
            overview += "\n"
        
        return overview
    
    def _estimate_module_time(self, content: Dict[str, List[str]]) -> int:
        """Estimate time for a module based on content"""
        
        time_estimates = {
            "tutorial": 15,    # 15 minutes per tutorial chunk
            "concept": 10,     # 10 minutes per concept chunk
            "example": 8,      # 8 minutes per example chunk
            "reference": 5     # 5 minutes per reference chunk
        }
        
        total_time = 0
        for doc_type, chunks in content.items():
            total_time += len(chunks) * time_estimates.get(doc_type, 10)
        
        return max(total_time, 15)  # Minimum 15 minutes per module
    
    def _create_content_summary_for_module(self, content: Dict[str, List[str]]) -> str:
        """Create a summary of content found for a module"""
        
        summary_parts = []
        for doc_type, chunks in content.items():
            if chunks:
                summary_parts.append(f"{len(chunks)} {doc_type} chunks")
        
        return ", ".join(summary_parts) if summary_parts else "No content found"
    
    def build_learning_path(self, 
                          module_headings: Optional[List[str]] = None,
                          difficulty_level: str = "intermediate") -> LearningPath:
        """Build a complete learning path with AI-generated search queries"""
        
        logger.info(f"Building learning path for difficulty: {difficulty_level}")
        
        # Step 1: Create complete rich content summary
        content_summary_text = self._create_rich_content_summary()
        logger.info(f"Created complete content summary with {len(self.analyzed_docs)} documents")
        
        # Step 2: Discover modules
        if module_headings:
            modules = module_headings
            discovery_reasoning = f"Using user-provided modules: {', '.join(modules)}"
            logger.info(f"Using provided modules: {modules}")
        else:
            modules, discovery_reasoning = self.module_discoverer(
                content_summary=content_summary_text,
                difficulty_level=difficulty_level
            )
            logger.info(f"Discovered modules: {modules}")
        
        # Step 3: Create complete targeted overview for ordering
        content_overview = self._create_content_overview_for_ordering(modules)
        
        # Step 4: Order modules
        ordered_modules, ordering_reasoning = self.module_orderer(
            modules=modules,
            content_overview=content_overview,
            difficulty_level=difficulty_level
        )
        
        logger.info(f"Ordered modules: {ordered_modules}")
        
        # Step 5: Build learning modules with AI-generated queries
        learning_modules = []
        content_gaps = []
        total_time = 0
        
        for module_title in ordered_modules:
            logger.info(f"Building content for module: {module_title}")
            
            # Search for content using AI-generated queries
            content = self._search_content_for_module(module_title, difficulty_level)
            
            # Check for content gaps
            empty_types = [doc_type for doc_type, chunks in content.items() if not chunks]
            if empty_types:
                content_gaps.append(f"Module '{module_title}' missing: {', '.join(empty_types)}")
            
            # Calculate time
            module_time = self._estimate_module_time(content)
            total_time += module_time
            
            # Create learning module
            learning_module = LearningModule(
                title=module_title,
                tutorial_content=content["tutorial"],
                concept_content=content["concept"],
                example_content=content["example"],
                reference_content=content["reference"],
                estimated_time=module_time,
                content_summary=self._create_content_summary_for_module(content)
            )
            
            learning_modules.append(learning_module)
        
        # Step 6: Create final learning path
        learning_path = LearningPath(
            modules=learning_modules,
            difficulty_level=difficulty_level,
            total_time=total_time,
            module_count=len(learning_modules),
            discovery_reasoning=discovery_reasoning,
            ordering_reasoning=ordering_reasoning,
            content_gaps=content_gaps
        )
        
        logger.info(f"Built learning path: {len(learning_modules)} modules, {total_time} minutes")
        return learning_path

class LearningPathManager:
    """High-level manager for learning path operations"""
    
    def __init__(self, analyzed_docs: List, vector_db_manager):
        self.path_builder = PathBuilder(analyzed_docs, vector_db_manager)
    
    def create_path(self, 
                   module_headings: Optional[List[str]] = None,
                   difficulty_level: str = "intermediate") -> LearningPath:
        """Create a learning path"""
        return self.path_builder.build_learning_path(module_headings, difficulty_level)
    
    def preview_available_content(self) -> ContentSummary:
        """Preview what content is available"""
        return self.path_builder._create_available_content_summary()
    
    def test_module_content(self, module_title: str, difficulty_level: str = "intermediate") -> Dict:
        """Test what content would be found for a specific module"""
        content = self.path_builder._search_content_for_module(module_title, difficulty_level)
        
        return {
            "module": module_title,
            "difficulty": difficulty_level,
            "content_found": {doc_type: len(chunks) for doc_type, chunks in content.items()},
            "total_chunks": sum(len(chunks) for chunks in content.values()),
            "estimated_time": self.path_builder._estimate_module_time(content)
        }

class ContentGenerator:
    """Generates complete learning content from learning modules"""
    
    def __init__(self, vector_db_manager):
        self.vector_db = vector_db_manager
        self.content_synthesizer = ContentSynthesizer()
        self.exercise_generator = ExerciseGenerator()
        self.assessment_creator = AssessmentCreator()
        self.objective_writer = ObjectiveWriter()
        self.code_extractor = CodeExampleExtractor()
    
    def _retrieve_content_chunks(self, chunk_ids: List[str]) -> List[ContentChunk]:
        """Retrieve actual content from chunk IDs"""
        chunks = []
        
        for chunk_id in chunk_ids[:10]:  # Limit to 10 chunks to avoid token issues
            try:
                results = self.vector_db.vector_db.collection.get(ids=[chunk_id])
                
                if results['ids']:
                    chunk = ContentChunk(
                        id=chunk_id,
                        content=results['documents'][0],
                        doc_type=results['metadatas'][0].get('doc_type', 'unknown'),
                        title=results['metadatas'][0].get('title', 'Untitled'),
                        metadata=results['metadatas'][0]
                    )
                    chunks.append(chunk)
                    
            except Exception as e:
                logger.warning(f"Could not retrieve chunk {chunk_id}: {e}")
                continue
        
        return chunks
    
    def generate_content(self, 
                        learning_module, 
                        difficulty_level: str = "intermediate",
                        bloom_level: str = "understand") -> GeneratedContent:
        """Generate complete learning content for a module"""
        
        logger.info(f"Generating content for module: {learning_module.title}")
        
        # Step 1: Retrieve content chunks (limit to avoid token issues)
        all_chunk_ids = (
            learning_module.tutorial_content[:5] +
            learning_module.concept_content[:5] +
            learning_module.example_content[:3] +
            learning_module.reference_content[:3]
        )
        
        content_chunks = self._retrieve_content_chunks(all_chunk_ids)
        logger.info(f"Retrieved {len(content_chunks)} content chunks")
        
        # Initialize with defaults to avoid validation errors
        lesson_text = f"Learning content for {learning_module.title}"
        key_concepts = [learning_module.title]
        code_examples = []
        exercises = []
        assessment_questions = []
        learning_objectives = []
        
        if content_chunks:
            try:
                # Step 2: Synthesize main lesson content
                lesson_text, key_concepts = self.content_synthesizer(
                    module_title=learning_module.title,
                    content_chunks=content_chunks,
                    difficulty_level=difficulty_level,
                    bloom_level=bloom_level
                )
            except Exception as e:
                logger.error(f"Error in content synthesis: {e}")
            
            try:
                # Step 3: Extract code examples
                code_content = "\n\n".join([
                    chunk.content[:500] for chunk in content_chunks 
                    if '```' in chunk.content or chunk.doc_type in ['tutorial', 'example']
                ][:3])  # Limit content
                
                if code_content:
                    code_examples = self.code_extractor(
                        module_title=learning_module.title,
                        content_with_code=code_content,
                        difficulty_level=difficulty_level
                    )
            except Exception as e:
                logger.error(f"Error extracting code examples: {e}")
                code_examples = []
            
            try:
                # Step 4: Generate exercises
                example_content = "\n\n".join([
                    chunk.content[:400] for chunk in content_chunks
                    if chunk.doc_type in ['tutorial', 'example']
                ][:3])
                
                exercises = self.exercise_generator(
                    module_title=learning_module.title,
                    lesson_content=lesson_text,
                    difficulty_level=difficulty_level,
                    available_examples=example_content
                )
            except Exception as e:
                logger.error(f"Error generating exercises: {e}")
                exercises = []
            
            try:
                # Step 5: Create assessment questions
                assessment_questions = self.assessment_creator(
                    module_title=learning_module.title,
                    lesson_content=lesson_text,
                    key_concepts=key_concepts,
                    difficulty_level=difficulty_level
                )
            except Exception as e:
                logger.error(f"Error creating assessment: {e}")
                assessment_questions = []
            
            try:
                # Step 6: Write learning objectives
                learning_objectives = self.objective_writer(
                    module_title=learning_module.title,
                    lesson_content=lesson_text,
                    difficulty_level=difficulty_level,
                    bloom_level=bloom_level
                )
            except Exception as e:
                logger.error(f"Error writing objectives: {e}")
                learning_objectives = []
        
        # Ensure all fields have valid defaults
        generated_content = GeneratedContent(
            module_title=learning_module.title,
            learning_objectives=learning_objectives or [],
            lesson_text=lesson_text,
            code_examples=code_examples or [],
            exercises=exercises or [],
            assessment_questions=assessment_questions or [],
            estimated_time=learning_module.estimated_time,
            key_concepts=key_concepts or []
        )
        
        logger.info(f"Generated content for {learning_module.title}: "
                   f"{len(code_examples)} examples, {len(exercises)} exercises, "
                   f"{len(assessment_questions)} questions")
        
        return generated_content

class ContentGenerationManager:
    """High-level manager for content generation"""
    
    def __init__(self, vector_db_manager):
        self.content_generator = ContentGenerator(vector_db_manager)
    
    def generate_course_content(self, 
                               learning_path, 
                               difficulty_level: str = "intermediate") -> List[GeneratedContent]:
        """Generate content for an entire learning path"""
        
        generated_modules = []
        
        for module in learning_path.modules:
            try:
                generated_content = self.content_generator.generate_content(
                    learning_module=module,
                    difficulty_level=difficulty_level
                )
                generated_modules.append(generated_content)
                
            except Exception as e:
                logger.error(f"Error generating content for {module.title}: {e}")
                continue
        
        return generated_modules
    
    def generate_single_module_content(self, 
                                     learning_module, 
                                     difficulty_level: str = "intermediate",
                                     bloom_level: str = "understand") -> GeneratedContent:
        """Generate content for a single module"""
        
        return self.content_generator.generate_content(
            learning_module=learning_module,
            difficulty_level=difficulty_level,
            bloom_level=bloom_level
        )

