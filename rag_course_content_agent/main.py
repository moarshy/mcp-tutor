import logging
from pathlib import Path
from typing import List, Optional
import dspy

from .models import LearningPath, GeneratedContent
from .managers import DocAnalyzer, RepoManager, VectorDBManager, LearningPathManager, ContentGenerationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGCourseContentAgent:
    """Main orchestrator for the RAG Course Content Agent system"""
    
    def __init__(self, 
                 cache_dir: str = ".cache",
                 vector_db_path: str = "./vector_db",
                 embedding_model: str = "text-embedding-3-small"):
        
        self.repo_manager = RepoManager(cache_dir=cache_dir)
        self.doc_analyzer = DocAnalyzer()
        self.vector_db_manager = VectorDBManager(db_path=vector_db_path)
        
        # These will be initialized after document analysis
        self.path_manager = None
        self.content_manager = None
        self.analyzed_docs = None
    
    def process_repository(self, 
                          repo_url: str, 
                          include_folders: Optional[List[str]] = None,
                          force_update: bool = False,
                          use_cache: bool = True) -> int:
        """Process a repository and extract documentation"""
        
        logger.info(f"Processing repository: {repo_url}")
        
        # Check for cached analysis first
        if use_cache:
            cached_analysis = self.repo_manager.load_analysis_cache(repo_url)
            if cached_analysis:
                logger.info(f"Using cached analysis with {len(cached_analysis)} documents")
                self.analyzed_docs = cached_analysis
                
                # Initialize managers
                self.path_manager = LearningPathManager(self.analyzed_docs, self.vector_db_manager)
                self.content_manager = ContentGenerationManager(self.vector_db_manager)
                
                # Initialize vector database if not already done
                stats = self.vector_db_manager.vector_db.get_stats()
                if stats.get("total_chunks", 0) == 0:
                    logger.info("Initializing vector database from cached analysis")
                    self.vector_db_manager.initialize_from_analysis(self.analyzed_docs)
                
                return len(self.analyzed_docs)
        
        # Clone/update repository
        repo_path = self.repo_manager.clone_or_update_repo(repo_url, force_update=force_update)
        
        # Find documentation files
        docs_files = self.repo_manager.find_documentation_files(
            repo_path, 
            include_folders=include_folders
        )
        logger.info(f"Found {len(docs_files)} documentation files")
        
        if not docs_files:
            logger.warning("No documentation files found")
            return 0
        
        # Analyze documents
        self.analyzed_docs = self.doc_analyzer.analyze_repository(docs_files)
        logger.info(f"Analyzed {len(self.analyzed_docs)} documents")
        
        # Save analysis cache
        self.repo_manager.save_analysis_cache(self.analyzed_docs, repo_url)
        
        # Initialize vector database
        logger.info("Initializing vector database...")
        self.vector_db_manager.clear_database()  # Clear any existing data
        stats = self.vector_db_manager.initialize_from_analysis(self.analyzed_docs)
        logger.info(f"Vector database initialized: {stats}")
        
        # Initialize managers
        self.path_manager = LearningPathManager(self.analyzed_docs, self.vector_db_manager)
        self.content_manager = ContentGenerationManager(self.vector_db_manager)
        
        return len(self.analyzed_docs)
    
    def create_learning_path(self, 
                           module_headings: Optional[List[str]] = None,
                           difficulty_level: str = "intermediate") -> LearningPath:
        """Create a learning path from analyzed documents"""
        
        if not self.path_manager:
            raise ValueError("No documents processed. Call process_repository() first.")
        
        logger.info(f"Creating learning path (difficulty: {difficulty_level})")
        
        learning_path = self.path_manager.create_path(
            module_headings=module_headings,
            difficulty_level=difficulty_level
        )
        
        logger.info(f"Created learning path with {len(learning_path.modules)} modules, "
                   f"estimated {learning_path.total_time} minutes")
        
        return learning_path
    
    def generate_course_content(self, 
                               learning_path: LearningPath,
                               difficulty_level: str = "intermediate") -> List[GeneratedContent]:
        """Generate complete course content from a learning path"""
        
        if not self.content_manager:
            raise ValueError("No documents processed. Call process_repository() first.")
        
        logger.info(f"Generating course content for {len(learning_path.modules)} modules")
        
        generated_content = self.content_manager.generate_course_content(
            learning_path=learning_path,
            difficulty_level=difficulty_level
        )
        
        logger.info(f"Generated content for {len(generated_content)} modules")
        
        return generated_content
    
    def get_stats(self) -> dict:
        """Get system statistics"""
        
        stats = {
            "documents_analyzed": len(self.analyzed_docs) if self.analyzed_docs else 0,
            "vector_db_stats": self.vector_db_manager.vector_db.get_stats() if self.vector_db_manager else {},
            "system_ready": self.path_manager is not None and self.content_manager is not None
        }
        
        if self.analyzed_docs:
            doc_types = {}
            for doc in self.analyzed_docs:
                doc_type = doc.classification.doc_type.value
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            stats["document_types"] = doc_types
        
        return stats

def configure_dspy(model: str = "gemini/gemini-2.5-flash", max_tokens: int = 20000):
    """Configure DSPy with the specified model"""
    dspy.configure(lm=dspy.LM(model, max_tokens=max_tokens))

def main():
    """Example usage of the RAG Course Content Agent"""
    
    # Configure DSPy
    configure_dspy()
    
    # Initialize the agent
    agent = RAGCourseContentAgent()
    
    # Example repository (MCP docs)
    repo_url = "https://github.com/modelcontextprotocol/docs"
    
    try:
        # Process repository
        doc_count = agent.process_repository(
            repo_url=repo_url,
            include_folders=["docs", "tutorials", "quickstart"]
        )
        
        if doc_count == 0:
            logger.error("No documents found in repository")
            return
        
        # Show stats
        stats = agent.get_stats()
        logger.info(f"System stats: {stats}")
        
        # Create learning path
        learning_path = agent.create_learning_path(
            difficulty_level="intermediate"
        )
        
        # Print learning path summary
        print(f"\n📚 Learning Path Created:")
        print(f"Difficulty: {learning_path.difficulty_level}")
        print(f"Total modules: {learning_path.module_count}")
        print(f"Estimated time: {learning_path.total_time} minutes")
        print(f"Discovery reasoning: {learning_path.discovery_reasoning}")
        print(f"Ordering reasoning: {learning_path.ordering_reasoning}")
        
        if learning_path.content_gaps:
            print(f"Content gaps: {learning_path.content_gaps}")
        
        print(f"\n📖 Modules:")
        for i, module in enumerate(learning_path.modules, 1):
            print(f"{i}. {module.title} ({module.estimated_time} min)")
            print(f"   Content: {module.content_summary}")
        
        # Generate course content for first module as example
        if learning_path.modules:
            logger.info("Generating content for first module as example...")
            
            first_module_content = agent.content_manager.generate_single_module_content(
                learning_module=learning_path.modules[0],
                difficulty_level="intermediate"
            )
            
            print(f"\n🎯 Generated Content for '{first_module_content.module_title}':")
            print(f"Learning objectives: {len(first_module_content.learning_objectives)}")
            print(f"Code examples: {len(first_module_content.code_examples)}")
            print(f"Exercises: {len(first_module_content.exercises)}")
            print(f"Assessment questions: {len(first_module_content.assessment_questions)}")
            print(f"Key concepts: {first_module_content.key_concepts}")
            
            # Show first learning objective
            if first_module_content.learning_objectives:
                obj = first_module_content.learning_objectives[0]
                print(f"\nExample objective: {obj.objective}")
                print(f"Bloom level: {obj.bloom_level}")
                print(f"Outcome: {obj.measurable_outcome}")
        
        logger.info("✅ RAG Course Content Agent demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
