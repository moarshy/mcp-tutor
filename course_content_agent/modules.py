import os
import pickle
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import git
import dspy
from urllib.parse import urlparse
import re
import frontmatter
import logging


from .models import (
    DocumentType, ComplexityLevel, DocumentMetadata, DocumentNode,
    DocumentTree, AssessmentPoint, LearningModule, GroupedLearningPath,
    ModuleContent, GeneratedCourse
)
from .signatures import (
    DocumentParser, DocumentClassifier, DocumentClusterer,
    WelcomeMessageGenerator, CourseIntroGenerator, ModuleIntroGenerator, ModuleMainContentGenerator, 
    ModuleConclusionGenerator, ModuleSummaryGenerator, AssessmentContentGenerator, 
    CourseConclusionGenerator
)

logger = logging.getLogger(__name__)

# =============================================================================
# Multiprocessing Helper Functions (must be at module level)
# =============================================================================

def process_single_document(args):
    """Process a single document - must be top-level function for multiprocessing"""
    file_path, repo_path, use_llm = args
    
    try:
        relative_path = str(file_path.relative_to(repo_path))
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create basic metadata
        basic_data = ContentExtractor.extract_basic_metadata(content, file_path)
        
        # For multiprocessing, we'll do LLM processing in the main thread
        # This avoids complex serialization issues with dspy modules
        doc_id = hashlib.md5(relative_path.encode()).hexdigest()
        
        return {
            'success': True,
            'relative_path': relative_path,
            'doc_id': doc_id,
            'content': content,
            'basic_data': basic_data,
            'file_path': file_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'relative_path': str(file_path.relative_to(repo_path)) if file_path else 'unknown',
            'error': str(e)
        }

def process_llm_analysis(args):
    """Process LLM analysis for a single document - must be top-level function for multiprocessing"""
    result, tree_root_path, overview_context = args
    
    try:
        relative_path = result['relative_path']
        
        # Initialize parser module for this worker process
        parser_module = DocumentParserModule()
        
        # Apply LLM analysis
        try:
            metadata = parser_module(
                content=result['content'], 
                filename=result['file_path'].name, 
                filepath=result['file_path'],
                overview_context=overview_context
            )
            llm_success = True
            error_msg = None
        except Exception as e:
            # Fall back to basic metadata if LLM fails
            metadata = create_basic_metadata_from_result(result)
            llm_success = False
            error_msg = str(e)
        
        # Create node data (don't create the actual node object due to serialization)
        node_data = {
            'id': result['doc_id'],
            'path': relative_path,
            'filename': result['file_path'].name,
            'content': result['content'],
            'metadata': metadata,
            'parent_path': str(result['file_path'].parent.relative_to(Path(tree_root_path))) 
            if result['file_path'].parent != Path(tree_root_path) else None
        }
        
        return {
            'success': True,
            'llm_success': llm_success,
            'relative_path': relative_path,
            'node_data': node_data,
            'error_msg': error_msg if not llm_success else None
        }
        
    except Exception as e:
        return {
            'success': False,
            'relative_path': result.get('relative_path', 'unknown'),
            'error': str(e)
        }


def create_basic_metadata_from_result(result):
    """Create basic metadata from processed result - helper function for multiprocessing"""
    basic_data = result['basic_data']
    
    return DocumentMetadata(
        title=basic_data['title'],
        headings=basic_data['headings'],
        code_blocks=basic_data['code_blocks'],
        frontmatter=basic_data['frontmatter'],
        doc_type=DocumentType.GUIDE,
        complexity=ComplexityLevel.INTERMEDIATE,
        topics=[],
        key_concepts=[],
        prerequisites=[],
        learning_objectives=[],
        semantic_summary=f"Documentation for {basic_data['title']}",
        primary_language=basic_data['primary_language'],
        has_examples=basic_data['has_examples'],
        has_api_docs=basic_data['has_api_docs'],
        difficulty_score=0.5
    )

# =============================================================================
# Repository Manager
# =============================================================================

class RepoManager:
    """Handles repository cloning, caching, and file discovery"""
    
    def __init__(self, cache_dir: str):
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
            logger.info(f"Repository already cached at {repo_path}")
            try:
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
                logger.info("Updated repository with latest changes")
            except Exception as e:
                logger.warning(f"Warning: Could not update repository: {e}")
            return repo_path
        
        if repo_path.exists():
            import shutil
            shutil.rmtree(repo_path)
            
        logger.info(f"Cloning repository to {repo_path}")
        git.Repo.clone_from(repo_url, repo_path)
        return repo_path
    
    def find_documentation_files(self, repo_path: Path, include_folders: Optional[List[str]] = None) -> List[Path]:
        """Find all markdown files in repository, optionally filtered by folders"""
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
        
        # Filter by include_folders if specified
        if include_folders:
            folder_filtered_files = []
            for file_path in filtered_files:
                # Get relative path from repo root
                rel_path = file_path.relative_to(repo_path)
                rel_path_str = str(rel_path)
                
                # Check if file is in any of the included folders
                for include_folder in include_folders:
                    # Normalize folder path (remove leading/trailing slashes)
                    include_folder = include_folder.strip('/')
                    
                    # Check if file path starts with the include folder
                    if rel_path_str.startswith(include_folder + '/') or rel_path_str.startswith(include_folder + '\\'):
                        folder_filtered_files.append(file_path)
                        break
                    # Also check if the file is directly in the include folder (for root level includes)
                    elif include_folder == '.' and '/' not in rel_path_str and '\\' not in rel_path_str:
                        folder_filtered_files.append(file_path)
                        break
                    # Check if the include folder is the exact parent directory
                    elif str(rel_path.parent) == include_folder or str(rel_path.parent).replace('\\', '/') == include_folder:
                        folder_filtered_files.append(file_path)
                        break
            
            filtered_files = folder_filtered_files
            logger.info(f"Filtered to {len(filtered_files)} files from specified folders: {include_folders}")
        
        return sorted(filtered_files)
    
    def save_tree_cache(self, tree: DocumentTree, repo_url: str):
        """Save processed document tree to cache"""
        cache_path = self._get_tree_cache_path(repo_url)
        cache_path.parent.mkdir(exist_ok=True)
        
        with open(cache_path, 'wb') as f:
            pickle.dump(tree, f)
        logger.info(f"Saved document tree cache to {cache_path}")
    
    def load_tree_cache(self, repo_url: str) -> Optional[DocumentTree]:
        """Load processed document tree from cache"""
        cache_path = self._get_tree_cache_path(repo_url)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                tree = pickle.load(f)
            logger.info(f"Loaded document tree cache from {cache_path}")
            return tree
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
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
        
        # Compute additional features
        primary_language = ContentExtractor._get_primary_language(code_blocks)
        has_examples = ContentExtractor._has_code_examples(code_blocks, clean_content)
        has_api_docs = ContentExtractor._has_api_documentation(clean_content, headings)
        
        return {
            'title': title,
            'headings': headings,
            'code_blocks': code_blocks,
            'frontmatter': frontmatter_data,
            'primary_language': primary_language,
            'has_examples': has_examples,
            'has_api_docs': has_api_docs
        }
    
    @staticmethod
    def _extract_title(content: str, frontmatter_data: dict, filename: str) -> str:
        """Extract document title"""
        if 'title' in frontmatter_data:
            return frontmatter_data['title'].strip()
        
        h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return filename.replace('.md', '').replace('.mdx', '').replace('_', ' ').replace('-', ' ').title().strip()
    
    @staticmethod
    def _extract_headings(content: str) -> List[str]:
        """Extract all headings from content, retaining Markdown # characters."""
        headings = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            hashes = match.group(1)
            text = match.group(2).strip()
            headings.append(f"{hashes} {text}")
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
# Document Parser Module
# =============================================================================

class DocumentParserModule(dspy.Module):
    """Enhanced DSPy module for comprehensive document parsing"""
    
    def __init__(self):
        super().__init__()
        self.parser = dspy.ChainOfThought(DocumentParser)
        self.classifier = dspy.ChainOfThought(DocumentClassifier)
    
    def forward(self, content: str, filename: str, filepath: Path, overview_context: str = "") -> DocumentMetadata:
        """Parse document and extract comprehensive metadata"""
        
        # Extract basic metadata
        basic_data = ContentExtractor.extract_basic_metadata(content, filepath)
        
        # Set content limit for LLM processing
        DOCUMENT_PARSER_MAX_CHARS = 3000
        
        try:
            # Get LLM-enhanced semantic understanding
            parse_result = self.parser(
                content=content[:DOCUMENT_PARSER_MAX_CHARS],
                filename=filename,
                overview_context=overview_context
            )
            
            # Parse LLM outputs - now direct access since they're List[str] with safe extraction
            key_concepts = getattr(parse_result, 'key_concepts', []) if hasattr(parse_result, 'key_concepts') and isinstance(getattr(parse_result, 'key_concepts'), list) else []
            learning_objectives = getattr(parse_result, 'learning_objectives', []) if hasattr(parse_result, 'learning_objectives') and isinstance(getattr(parse_result, 'learning_objectives'), list) else []
            prerequisites = getattr(parse_result, 'prerequisites', []) if hasattr(parse_result, 'prerequisites') and isinstance(getattr(parse_result, 'prerequisites'), list) else []
            
            # Classify the document
            classification = self.classifier(
                title=basic_data['title'],
                content=content[:DOCUMENT_PARSER_MAX_CHARS],
                headings=str(basic_data['headings'][:10]),
                semantic_summary=parse_result.semantic_summary,
                overview_context=overview_context
            )
            
            # Parse classification outputs - topics is now List[str] with safe extraction
            topics = getattr(classification, 'topics', []) if hasattr(classification, 'topics') and isinstance(getattr(classification, 'topics'), list) else []
            doc_type = self._safe_enum_parse(classification.doc_type, DocumentType, DocumentType.GUIDE)
            complexity = self._safe_enum_parse(classification.complexity, ComplexityLevel, ComplexityLevel.INTERMEDIATE)
            
        except Exception as e:
            logger.error(f"LLM parsing failed for {filename}: {e}")
            # Fallback to basic classification
            key_concepts = []
            learning_objectives = []
            prerequisites = []
            topics = []
            doc_type = DocumentType.GUIDE
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
            frontmatter=basic_data['frontmatter'],
            
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


# =============================================================================
# Learning Path Generator
# =============================================================================

class LearningPathGenerator(dspy.Module):
    """DSPy module to generate comprehensive learning paths with Introduction → Topic modules → Conclusion"""
    
    def __init__(self):
        super().__init__()
        self.clusterer = dspy.ChainOfThought(DocumentClusterer)
        self.welcome_generator = dspy.ChainOfThought(WelcomeMessageGenerator)
    
    def forward(self, documents: List[DocumentNode], complexity: ComplexityLevel, 
                repo_name: str, overview_context: str = "") -> GroupedLearningPath:
        """
        Generate a comprehensive learning path for the given complexity level
        
        Args:
            documents: All available documents (no pre-filtering by complexity)
            complexity: Target complexity level
            repo_name: Name of the repository/project
            overview_context: Overview document content for context
            
        Returns:
            GroupedLearningPath: Complete learning path with modules and welcome message
        """
        
        logger.info(f"Generating learning path for {complexity.value} level with {len(documents)} documents")
        
        # Prepare comprehensive document information for the LLM
        documents_info = self._prepare_documents_info(documents)
        
        # Use LLM to intelligently cluster documents into modules
        try:
            cluster_result = self.clusterer(
                documents_info=json.dumps(documents_info),
                target_complexity=complexity.value,
                overview_context=overview_context
            )
            
            # Parse the modules from LLM output
            modules = self._parse_modules_from_llm(cluster_result.modules, documents)
            
        except Exception as e:
            logger.error(f"Error in LLM clustering: {e}")
        
        if not modules:
            logger.warning(f"No modules generated for {complexity.value} level")
            return None
        
        # Generate welcome message
        welcome_msg = self._generate_welcome_message(modules, complexity, repo_name)
        
        # Create the complete learning path
        grouped_path = GroupedLearningPath(
            pathway_id=f"{repo_name}_{complexity.value}",
            title=f"{repo_name.title()} - {complexity.value.title()} Course",
            description=f"Complete {complexity.value} level course for {repo_name}",
            target_complexity=complexity,
            modules=modules,
            welcome_message=welcome_msg
        )
        
        logger.info(f"Generated learning path with {len(modules)} modules for {complexity.value}")
        return grouped_path
    
    def generate_grouped_paths(self, tree: DocumentTree, overview_context: str = "") -> List[GroupedLearningPath]:
        """Generate learning paths for all complexity levels"""
        grouped_paths = []
        
        # Get all documents (no complexity filtering - let LLM decide)
        all_documents = list(tree.nodes.values())
        
        if not all_documents:
            logger.warning("No documents found for learning path generation")
            return grouped_paths
            
        logger.info(f"Generating learning paths for {len(all_documents)} documents")
        
        for complexity in ComplexityLevel:
            try:
                # Generate learning path for this complexity level
                grouped_path = self.forward(
                    documents=all_documents,
                    complexity=complexity,
                    repo_name=tree.repo_name or "Documentation",
                    overview_context=overview_context
                )
                
                if grouped_path:
                    grouped_paths.append(grouped_path)
                    
            except Exception as e:
                logger.error(f"Error generating learning path for {complexity.value}: {e}")
                continue
        
        return grouped_paths
    
    def _prepare_documents_info(self, documents: List[DocumentNode]) -> Dict[str, Any]:
        """Prepare comprehensive document information for the LLM"""
        
        docs_info = {}
        
        for doc in documents:
            # Create rich document information
            doc_info = {
                'title': doc.metadata.title,
                'filename': doc.filename,
                # 'doc_type': doc.metadata.doc_type.value if doc.metadata.doc_type else 'unknown',
                'semantic_summary': doc.metadata.semantic_summary or "No summary available",
                'topics': doc.metadata.topics or [],
                'key_concepts': doc.metadata.key_concepts or [],
                'learning_objectives': doc.metadata.learning_objectives or [],
                'prerequisites': doc.metadata.prerequisites or [],
                'has_examples': doc.metadata.has_examples,
                'has_api_docs': doc.metadata.has_api_docs,
                'primary_language': doc.metadata.primary_language,
                'headings': doc.metadata.headings[:5] if doc.metadata.headings else [],  # First 5 headings
                # 'content_length': len(doc.content),
                # 'difficulty_score': doc.metadata.difficulty_score
            }
            
            docs_info[doc.path] = doc_info
        
        logger.info(f"Prepared information for {len(docs_info)} documents")
        return docs_info
    
    def _parse_modules_from_llm(self, modules_json: str, documents: List[DocumentNode]) -> List[LearningModule]:
        """Parse modules from LLM JSON output and create LearningModule objects"""
        
        try:
            modules_data = json.loads(modules_json)
            if not isinstance(modules_data, list):
                logger.error("LLM output is not a list of modules")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM modules JSON: {e}")
            return []
        
        modules = []
        doc_path_map = {doc.path: doc for doc in documents}
        
        for i, module_data in enumerate(modules_data):
            try:
                # Extract module information
                module_id = module_data.get('id', f"module_{i+1:02d}")
                name = module_data.get('name', f"Module {i+1}")
                description = module_data.get('detailed_description', module_data.get('description', ''))
                linked_docs = module_data.get('linked_docs', [])
                learning_objectives = module_data.get('learning_objectives', [])
                theme = module_data.get('theme', 'General')
                
                # Validate linked documents exist
                valid_linked_docs = []
                for doc_path in linked_docs:
                    if doc_path in doc_path_map:
                        valid_linked_docs.append(doc_path)
                    else:
                        logger.warning(f"Document not found: {doc_path}")
                
                # Create assessment
                assessment = AssessmentPoint(
                    assessment_id=f"{module_id}_assessment",
                    title=f"{name} Assessment",
                    concepts_to_assess=module_data.get('key_concepts', [name.lower()])[:5]
                )
                
                # Create learning module
                module = LearningModule(
                    module_id=module_id,
                    title=name,
                    theme=theme,
                    description=description,
                    documents=valid_linked_docs,
                    learning_objectives=learning_objectives,
                    assessment=assessment
                )
                
                modules.append(module)
                
            except Exception as e:
                logger.error(f"Error parsing module {i}: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(modules)} modules from LLM output")
        return modules
    
    def _generate_welcome_message(self, modules: List[LearningModule], 
                                complexity: ComplexityLevel, repo_name: str) -> str:
        """Generate welcome message for the learning path"""
        
        # Create modules overview
        modules_overview = []
        for i, module in enumerate(modules):
            modules_overview.append(f"Module {i+1}: {module.title}")
        
        try:
            welcome_result = self.welcome_generator(
                pathway_title=f"{repo_name.title()} - {complexity.value.title()} Course",
                target_complexity=complexity.value,
                modules_overview="\n".join(modules_overview)
            )
            
            return welcome_result.welcome_message
            
        except Exception as e:
            logger.error(f"Error generating welcome message: {e}")
            raise
    

# =============================================================================
# Course Generator
# =============================================================================

class CourseGenerator(dspy.Module):
    """Generate complete course content with all 5 module components"""
    
    def __init__(self):
        super().__init__()
        # Use Predict instead of ChainOfThought for content generators to avoid reasoning field issues
        self.course_intro_generator = dspy.Predict(CourseIntroGenerator)
        self.intro_generator = dspy.Predict(ModuleIntroGenerator)
        self.main_content_generator = dspy.Predict(ModuleMainContentGenerator)
        self.conclusion_generator = dspy.Predict(ModuleConclusionGenerator)
        self.summary_generator = dspy.Predict(ModuleSummaryGenerator)
        self.assessment_content_generator = dspy.Predict(AssessmentContentGenerator)
        self.course_conclusion_generator = dspy.Predict(CourseConclusionGenerator)
        self.max_workers = 10
    
    def forward(self, pathway: GroupedLearningPath, tree: DocumentTree, overview_context: str = "") -> GeneratedCourse:
        """Generate complete course content with full context"""
        return self.generate_course(pathway, tree, overview_context)
    
    def generate_course(self, pathway: GroupedLearningPath, tree: DocumentTree, overview_context: str = "") -> GeneratedCourse:
        """Generate complete course content with full context"""
        
        logger.info(f"Generating course content for {pathway.title}")
        
        # Generate course introduction module as the first module
        course_intro_module = self._generate_course_intro_module(pathway, overview_context)
        
        # Generate content for each module in parallel
        logger.info(f"Generating {len(pathway.modules)} modules in parallel...")
        parallel_module_contents = self._generate_modules_parallel(pathway, tree, overview_context)
        
        # Combine intro + parallel generated modules
        module_contents = [course_intro_module] + parallel_module_contents
        
        # Generate course conclusion
        course_conclusion = self._generate_course_conclusion(pathway)
        
        # Create complete course
        course = GeneratedCourse(
            course_id=pathway.pathway_id,
            title=pathway.title,
            description=pathway.description,
            welcome_message=pathway.welcome_message,
            modules=module_contents,
            course_conclusion=course_conclusion
        )
        
        logger.info(f"Generated complete course with {len(module_contents)} modules (including intro)")
        return course
    
    def _generate_modules_parallel(self, pathway: GroupedLearningPath, tree: DocumentTree, overview_context: str) -> List[ModuleContent]:
        """Generate modules in parallel using threading (DSPy modules are not picklable for multiprocessing)"""
        
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create a list of futures for each module
            futures = []
            for i, module in enumerate(pathway.modules):
                future = executor.submit(self._generate_module_content, module, pathway, tree, overview_context, i)
                futures.append(future)
            
            # Collect results
            module_contents = []
            for future in futures:
                module_contents.append(future.result())

        return module_contents

    def _generate_course_intro_module(self, pathway: GroupedLearningPath, overview_context: str) -> ModuleContent:
        """Generate course introduction module using only overview context"""
        
        logger.info("Generating course introduction module")
        
        # Generate course introduction content
        intro_content = self._generate_course_introduction(pathway, overview_context)
        
        # Create course intro module
        course_intro_module = ModuleContent(
            module_id="module_00_course_introduction",
            introduction=intro_content,
            main_content=f"# Welcome to {pathway.title}\n\n{pathway.description}\n\nThis course will guide you through understanding and mastering the concepts covered in this documentation.",
            conclusion=f"Now that you understand what this course covers, let's dive into the detailed modules!",
            assessment=f"# Course Introduction Assessment\n\n## Question 1\nWhat will you learn in this course?\n\n**Answer:** You will learn about {pathway.description.lower()}\n\n## Question 2\nWhat is the target complexity level?\n\n**Answer:** This course is designed for {pathway.target_complexity.value} level learners.",
            summary=f"Great! You now have an overview of {pathway.title}. Let's begin with the detailed modules."
        )
        
        return course_intro_module
    
    def _generate_course_introduction(self, pathway: GroupedLearningPath, overview_context: str) -> str:
        """Generate course introduction using overview context"""
        
        result = self.course_intro_generator(
            course_title=pathway.title,
            course_description=pathway.description,
            overview_context=overview_context,
            target_complexity=pathway.target_complexity.value
        )
        return result.introduction
    
    def _generate_module_content(self, module: LearningModule, pathway: GroupedLearningPath,
                               tree: DocumentTree, overview_context: str, module_index: int) -> ModuleContent:
        """Generate all 5 components for a single module with full context"""
        
        # Get source documents content
        source_documents = self._get_source_documents_content(module, tree)
        
        # Prepare course context
        course_context = f"Module {module_index} of {len(pathway.modules) + 1} in {pathway.title}"  # +1 for intro module
        
        # Generate module introduction
        introduction = self._generate_module_introduction(module, overview_context, course_context)
        
        # Generate main content (synthesized from source docs)
        main_content = self._generate_main_content(module, overview_context, source_documents)
        
        # Generate module conclusion
        conclusion = self._generate_module_conclusion(module, overview_context)
        
        # Generate assessment with answers
        assessment = self._generate_assessment_content(module, overview_context, source_documents)
        
        # Generate module summary
        summary = self._generate_module_summary(module, overview_context)
        
        return ModuleContent(
            module_id=module.module_id,
            introduction=introduction,
            main_content=main_content,
            conclusion=conclusion,
            assessment=assessment,
            summary=summary
        )
    
    def _get_source_documents_content(self, module: LearningModule, tree: DocumentTree) -> str:
        """Get filtered and cleaned content from source documents for this module"""
        
        source_content = []
        
        logger.info(f"Getting source documents for module {module.title}: {module.documents}")
        
        for doc_path in module.documents:
            if doc_path in tree.nodes:
                node = tree.nodes[doc_path]
                
                # Filter out non-documentation content
                cleaned_content = self._clean_document_content(node.content, node.filename)
                
                if cleaned_content.strip():
                    doc_content = f"""
## {node.metadata.title}

{cleaned_content}
"""
                    source_content.append(doc_content)
                    logger.info(f"Added document: {node.filename} ({len(cleaned_content)} chars)")
                else:
                    logger.info(f"Skipped document {node.filename} - no relevant content after cleaning")
            else:
                logger.warning(f"Document not found in tree.nodes: {doc_path}")
        
        result = "\n".join(source_content)
        logger.info(f"Total cleaned source content length: {len(result)} chars")
        return result
    
    def _clean_document_content(self, content: str, filename: str) -> str:
        """Clean document content to remove configuration files and focus on documentation"""
        
        # Skip common configuration files that aren't documentation
        if any(filename.lower().endswith(ext) for ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']):
            return ""
        
        # Skip if content looks like pure JSON/YAML/config
        stripped = content.strip()
        if (stripped.startswith('{') and stripped.endswith('}')) or \
           (stripped.startswith('[') and stripped.endswith(']')) or \
           stripped.startswith('---') and not any(line.startswith('#') for line in content.split('\n')[:10]):
            return ""
        
        # Remove frontmatter but keep the rest
        lines = content.split('\n')
        if lines and lines[0].strip() == '---':
            # Find end of frontmatter
            end_idx = 1
            while end_idx < len(lines) and lines[end_idx].strip() != '---':
                end_idx += 1
            if end_idx < len(lines):
                content = '\n'.join(lines[end_idx + 1:])
        
        # Remove excessive code blocks that might confuse the LLM
        import re
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if len(code_blocks) > 10:  # Too many code blocks, likely not documentation
            # Keep only the first few and add a note
            for i, block in enumerate(code_blocks[5:], 5):
                content = content.replace(block, f'\n[Code block {i+1} omitted for brevity]\n')
        
        return content
    
    def _generate_module_introduction(self, module: LearningModule, overview_context: str, course_context: str) -> str:
        """Generate module introduction with full context"""
        
        result = self.intro_generator(
            module_title=module.title,
            module_description=module.description,
            learning_objectives=module.learning_objectives,
            overview_context=overview_context,
            course_context=course_context
        )
        return result.introduction
    
    def _generate_main_content(self, module: LearningModule, overview_context: str, source_documents: str) -> str:
        """Generate synthesized main content from source documents"""
        
        result = self.main_content_generator(
            module_title=module.title,
            module_description=module.description,
            learning_objectives=module.learning_objectives,
            overview_context=overview_context,
            source_documents=source_documents[:15000]  # Limit source documents to avoid context window issues
        )
        return result.main_content
    
    def _generate_module_conclusion(self, module: LearningModule, overview_context: str) -> str:
        """Generate module conclusion"""
        
        result = self.conclusion_generator(
            module_title=module.title,
            learning_objectives=module.learning_objectives,
            key_concepts=module.assessment.concepts_to_assess,
            overview_context=overview_context
        )
        return result.conclusion
    
    def _generate_assessment_content(self, module: LearningModule, overview_context: str, source_documents: str) -> str:
        """Generate assessment with questions and answers"""
        
        result = self.assessment_content_generator(
            assessment_title=module.assessment.title,
            concepts_to_assess=module.assessment.concepts_to_assess,
            module_theme=module.theme
        )
        return result.assessment_content
    
    def _generate_module_summary(self, module: LearningModule, overview_context: str) -> str:
        """Generate module summary"""
        
        result = self.summary_generator(
            module_title=module.title,
            learning_objectives=module.learning_objectives,
            key_concepts=module.assessment.concepts_to_assess,
            overview_context=overview_context
        )
        return result.summary
    
    def _generate_course_conclusion(self, pathway: GroupedLearningPath) -> str:
        """Generate course conclusion"""
        
        modules_summary = []
        for i, module in enumerate(pathway.modules):
            modules_summary.append(f"Module {i+1}: {module.title} - {module.theme}")
        
        result = self.course_conclusion_generator(
            course_title=pathway.title,
            modules_completed="\n".join(modules_summary)
        )
        return result.conclusion


# =============================================================================
# Course Exporter
# =============================================================================

class CourseExporter:
    """Export generated course to files"""
    
    def export_to_markdown(self, course: GeneratedCourse, output_dir: str) -> None:
        """Export complete course as markdown files"""
        
        output_path = Path(output_dir)
        course_dir = output_path / course.course_id
        course_dir.mkdir(parents=True, exist_ok=True)
        
        # Export course welcome message
        with open(course_dir / "00_welcome.md", 'w', encoding='utf-8') as f:
            f.write(f"# {course.title}\n\n")
            f.write(f"{course.description}\n\n")
            f.write("---\n\n")
            f.write(course.welcome_message)
        
        # Export each module
        for i, module_content in enumerate(course.modules):
            module_num = f"{i+1:02d}"
            module_dir = course_dir / f"module_{module_num}"
            module_dir.mkdir(exist_ok=True)
            
            # Module introduction
            with open(module_dir / "01_introduction.md", 'w', encoding='utf-8') as f:
                f.write(module_content.introduction)
            
            # Main content (documents)
            content_dir = module_dir / "content"
            content_dir.mkdir(exist_ok=True)
            
            for j, doc_content in enumerate(module_content.main_content):
                doc_num = f"{j+1:02d}"
                with open(content_dir / f"{doc_num}_document.md", 'w', encoding='utf-8') as f:
                    f.write(doc_content)
            
            # Assessment
            with open(module_dir / "03_assessment.md", 'w', encoding='utf-8') as f:
                f.write(module_content.assessment)
            
            # Module summary
            with open(module_dir / "04_summary.md", 'w', encoding='utf-8') as f:
                f.write(module_content.summary)
        
        # Export course conclusion
        with open(course_dir / "99_conclusion.md", 'w', encoding='utf-8') as f:
            f.write(course.course_conclusion)
        
        # Export course info
        course_info = {
            "title": course.title,
            "description": course.description,
            "modules": [
                {
                    "module_id": module.module_id,
                    "documents_count": len(module.main_content)
                }
                for module in course.modules
            ]
        }
        
        with open(course_dir / "course_info.json", 'w', encoding='utf-8') as f:
            json.dump(course_info, f, indent=2)
        
        logger.info(f"Course exported to {course_dir}")
        print(f"Course exported to: {course_dir}") 