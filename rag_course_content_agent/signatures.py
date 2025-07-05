from typing import List
import dspy
from .models import DocumentType, Exercise, AssessmentQuestion, LearningObjective, CodeExample


class ClassifyDocument(dspy.Signature):
    """Classify a technical document into one of four categories based on its content and structure."""
    
    content: str = dspy.InputField(desc="The document content to classify")
    file_path: str = dspy.InputField(desc="The file path for context")
    headings: List[str] = dspy.InputField(desc="List of headings in the document")
    
    classification: DocumentType = dspy.OutputField(desc="One of: tutorial, reference, example, concept")
    confidence: float = dspy.OutputField(desc="Confidence score between 0.0 and 1.0")
    reasoning: str = dspy.OutputField(desc="Brief explanation for the classification")

class ExtractDependencies(dspy.Signature):
    """Extract prerequisite concepts and dependencies from technical documentation."""
    
    content: str = dspy.InputField(desc="The document content to analyze")
    title: str = dspy.InputField(desc="Document title or main concept")
    headings: List[str] = dspy.InputField(desc="List of headings in the document")
    
    main_concepts: List[str] = dspy.OutputField(desc="List of main concepts covered in this document")
    prerequisites: List[str] = dspy.OutputField(desc="List of prerequisite concepts needed to understand this document")
    evidence: str = dspy.OutputField(desc="Text evidence supporting the identified dependencies")

class SummarizeDocument(dspy.Signature):
    """Create a concise summary of a technical document for contextual retrieval."""
    
    content: str = dspy.InputField(desc="The full document content to summarize")
    title: str = dspy.InputField(desc="Document title")
    doc_type: str = dspy.InputField(desc="Document type (tutorial, reference, example, concept)")
    
    summary: str = dspy.OutputField(desc="Concise 5-7 sentence summary providing context about this document")

class DiscoverModules(dspy.Signature):
    """Analyze available documentation and suggest logical learning modules."""
    
    content_summary: str = dspy.InputField(desc="Summary of available documentation topics and types")
    difficulty_level: str = dspy.InputField(desc="Target difficulty: beginner, intermediate, or advanced") 
    user_modules: str = dspy.InputField(desc="User-provided modules if any, or 'none'")
    
    modules: List[str] = dspy.OutputField(desc="List of 3-8 logical learning modules")
    reasoning: str = dspy.OutputField(desc="Brief explanation of module choices and structure")

class OrderModules(dspy.Signature):
    """Order learning modules in optimal pedagogical sequence."""
    
    modules: List[str] = dspy.InputField(desc="List of learning modules to order")
    content_overview: str = dspy.InputField(desc="Overview of available content")
    difficulty_level: str = dspy.InputField(desc="Target difficulty level")
    
    ordered_modules: List[str] = dspy.OutputField(desc="Modules ordered from foundational to advanced")
    reasoning: str = dspy.OutputField(desc="Explanation of the ordering logic and prerequisites")

class GenerateSearchQueries(dspy.Signature):
    """Generate optimal search queries for finding content related to a learning module."""
    
    module_title: str = dspy.InputField(desc="The learning module title to search for")
    difficulty_level: str = dspy.InputField(desc="Target difficulty: beginner, intermediate, or advanced")
    doc_type: str = dspy.InputField(desc="Document type to search: tutorial, concept, example, or reference")
    available_content: str = dspy.InputField(desc="Brief overview of what content is available")
    
    search_queries: List[str] = dspy.OutputField(desc="List of 3-5 specific search queries optimized for this module and difficulty")
    reasoning: str = dspy.OutputField(desc="Brief explanation of the search strategy")

class SynthesizeContent(dspy.Signature):
    """Synthesize multiple content chunks into a coherent learning lesson."""
    
    module_title: str = dspy.InputField(desc="Title of the learning module")
    content_chunks: str = dspy.InputField(desc="Multiple content chunks to synthesize")
    difficulty_level: str = dspy.InputField(desc="Target difficulty level")
    bloom_level: str = dspy.InputField(desc="Bloom's taxonomy level to target")
    
    lesson_text: str = dspy.OutputField(desc="Coherent lesson text that teaches the module concepts")
    key_concepts: List[str] = dspy.OutputField(desc="List of key concepts covered in the lesson")

class GenerateExercises(dspy.Signature):
    """Generate practical exercises from code examples and tutorials."""
    
    module_title: str = dspy.InputField(desc="Title of the learning module")
    lesson_content: str = dspy.InputField(desc="The lesson content and examples")
    difficulty_level: str = dspy.InputField(desc="Target difficulty level")
    available_examples: str = dspy.InputField(desc="Available code examples and tutorials")
    
    exercises: List[Exercise] = dspy.OutputField(desc="List of 2-4 practical exercises")

class CreateAssessment(dspy.Signature):
    """Create assessment questions to test understanding of concepts."""
    
    module_title: str = dspy.InputField(desc="Title of the learning module")
    lesson_content: str = dspy.InputField(desc="The lesson content to assess")
    key_concepts: List[str] = dspy.InputField(desc="Key concepts to test")
    difficulty_level: str = dspy.InputField(desc="Target difficulty level")
    
    assessment_questions: List[AssessmentQuestion] = dspy.OutputField(desc="List of 3-6 assessment questions")

class WriteLearningObjectives(dspy.Signature):
    """Write clear, measurable learning objectives for a module."""
    
    module_title: str = dspy.InputField(desc="Title of the learning module")
    lesson_content: str = dspy.InputField(desc="The lesson content")
    difficulty_level: str = dspy.InputField(desc="Target difficulty level")
    bloom_level: str = dspy.InputField(desc="Target Bloom's taxonomy level")
    
    learning_objectives: List[LearningObjective] = dspy.OutputField(desc="List of 3-5 clear learning objectives")

class ExtractCodeExamples(dspy.Signature):
    """Extract and enhance code examples from content chunks."""
    
    module_title: str = dspy.InputField(desc="Title of the learning module")
    content_with_code: str = dspy.InputField(desc="Content chunks containing code examples")
    difficulty_level: str = dspy.InputField(desc="Target difficulty level")
    
    code_examples: List[CodeExample] = dspy.OutputField(desc="List of enhanced code examples with explanations")
