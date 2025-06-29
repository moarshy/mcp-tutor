import dspy
from typing import List

# =============================================================================
# Enhanced DSPy Signatures
# =============================================================================

class DocumentParser(dspy.Signature):
    """Parse a markdown document and extract structured metadata with semantic understanding"""
    content: str = dspy.InputField(desc="Raw markdown content")
    filename: str = dspy.InputField(desc="Document filename")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project for context")
    
    # Structured outputs - now using List[str] directly
    semantic_summary: str = dspy.OutputField(desc="2-3 sentence summary of the document's purpose and content")
    key_concepts: List[str] = dspy.OutputField(desc="List of 3-5 key concepts or terms covered in this document")
    learning_objectives: List[str] = dspy.OutputField(desc="List of what a reader should learn from this document")
    prerequisites: List[str] = dspy.OutputField(desc="List of concepts/knowledge needed before reading this document")

class DocumentClassifier(dspy.Signature):
    """Classify document type, complexity, and extract topics"""
    title: str = dspy.InputField(desc="Document title")
    content: str = dspy.InputField(desc="Document content sample")
    headings: str = dspy.InputField(desc="Document headings list")
    semantic_summary: str = dspy.InputField(desc="Semantic summary of the document")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project for context")
    
    doc_type: str = dspy.OutputField(desc="Document type: reference, guide, api, example, overview, configuration, troubleshooting, changelog")
    complexity: str = dspy.OutputField(desc="Complexity level: beginner, intermediate, advanced")
    topics: List[str] = dspy.OutputField(desc="List of 3-7 main topics/technologies covered")
    difficulty_score: float = dspy.OutputField(desc="Difficulty score from 0.0 (very easy) to 1.0 (very hard)")

class DocumentClusterer(dspy.Signature):
    """Group related documents into learning modules for a comprehensive course"""
    documents_info: str = dspy.InputField(desc="JSON of documents with topics, types, summaries, and metadata")
    target_complexity: str = dspy.InputField(desc="Target complexity level: beginner, intermediate, advanced")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project for context")
    
    modules: str = dspy.OutputField(desc="JSON list of modules with name, detailed_description, linked_docs, and learning_objectives. Should include Introduction, core topic modules, and Conclusion modules for a complete learning path")

class WelcomeMessageGenerator(dspy.Signature):
    """Generate welcome message for learning path"""
    pathway_title: str = dspy.InputField(desc="Learning path title")
    target_complexity: str = dspy.InputField(desc="Target complexity level")
    modules_overview: str = dspy.InputField(desc="Overview of modules in the path")
    
    welcome_message: str = dspy.OutputField(desc="Welcome message for the learning path")

class CourseIntroGenerator(dspy.Signature):
    """Generate course introduction module using project overview context"""
    course_title: str = dspy.InputField(desc="Title of the course")
    course_description: str = dspy.InputField(desc="Description of the course")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project")
    target_complexity: str = dspy.InputField(desc="Target complexity level for this course")
    
    introduction: str = dspy.OutputField(desc="Course introduction content in markdown format")

class ModuleIntroGenerator(dspy.Signature):
    """Generate module introduction with full context"""
    module_title: str = dspy.InputField(desc="Title of the module")
    module_description: str = dspy.InputField(desc="Detailed description of the module")
    learning_objectives: List[str] = dspy.InputField(desc="List of learning objectives")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project")
    course_context: str = dspy.InputField(desc="How this fits in the overall course")
    
    introduction: str = dspy.OutputField(desc="Module introduction in markdown format")

class ModuleMainContentGenerator(dspy.Signature):
    """Generate comprehensive module main content from source documents. You must output well-formatted markdown content, NOT JSON or configuration formats."""
    module_title: str = dspy.InputField(desc="Title of the module")
    module_description: str = dspy.InputField(desc="Detailed description of the module")
    learning_objectives: List[str] = dspy.InputField(desc="List of learning objectives")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project")
    source_documents: str = dspy.InputField(desc="Markdown documentation content for this module")
    
    main_content: str = dspy.OutputField(desc="Comprehensive module content in markdown format ONLY. Do NOT return JSON, YAML, or configuration file formats. Start with markdown headers and provide educational content.")

class ModuleConclusionGenerator(dspy.Signature):
    """Generate module conclusion"""
    module_title: str = dspy.InputField(desc="Title of the module")
    learning_objectives: List[str] = dspy.InputField(desc="List of learning objectives covered")
    key_concepts: List[str] = dspy.InputField(desc="Key concepts from the module")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project")
    
    conclusion: str = dspy.OutputField(desc="Module conclusion in markdown format")

class ModuleSummaryGenerator(dspy.Signature):
    """Generate module summary/wrap-up"""
    module_title: str = dspy.InputField(desc="Title of the module")
    learning_objectives: List[str] = dspy.InputField(desc="Learning objectives covered")
    key_concepts: List[str] = dspy.InputField(desc="Key concepts from the module")
    overview_context: str = dspy.InputField(desc="Overview of the entire documentation project")
    
    summary: str = dspy.OutputField(desc="Module summary in markdown format")

class AssessmentMetadataGenerator(dspy.Signature):
    """Generate assessment metadata (title and concepts to assess)"""
    module_theme: str = dspy.InputField(desc="Theme of the module")
    learning_objectives: List[str] = dspy.InputField(desc="List of learning objectives for the module")
    key_concepts: List[str] = dspy.InputField(desc="List of key concepts covered in the module")
    
    assessment_title: str = dspy.OutputField(desc="Title for the assessment")
    concepts_to_assess: List[str] = dspy.OutputField(desc="List of key concepts to assess")

class AssessmentContentGenerator(dspy.Signature):
    """Generate actual assessment content"""
    assessment_title: str = dspy.InputField(desc="Title of the assessment")
    concepts_to_assess: List[str] = dspy.InputField(desc="List of concepts to test")
    module_theme: str = dspy.InputField(desc="Theme of the module")
    
    assessment_content: str = dspy.OutputField(desc="Complete assessment with questions AND detailed answers in markdown format")

class CourseConclusionGenerator(dspy.Signature):
    """Generate course conclusion"""
    course_title: str = dspy.InputField(desc="Title of the course")
    modules_completed: str = dspy.InputField(desc="Summary of modules completed")
    
    conclusion: str = dspy.OutputField(desc="Course conclusion in markdown format") 