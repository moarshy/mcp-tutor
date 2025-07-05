from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import re
import dspy

from .models import (
    DocumentType, DocumentMetadata, DocumentClassification, 
    DependencyRelation, AnalyzedDocument, CodeBlock, Exercise, 
    AssessmentQuestion, LearningObjective, CodeExample, ContentChunk
)
from .signatures import (
    ClassifyDocument, ExtractDependencies, SummarizeDocument,
    DiscoverModules, OrderModules, GenerateSearchQueries,
    SynthesizeContent, GenerateExercises, CreateAssessment,
    WriteLearningObjectives, ExtractCodeExamples
)
from .utils import (
    FallbackParser, ContentFallbackParser, truncate_num_words
)

logger = logging.getLogger(__name__)

NUM_WORDS = 3000

class DocumentClassifier(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classify = dspy.ChainOfThought(ClassifyDocument)
    
    def forward(self, content: str, file_path: str, headings: List[str]):
        try:
            result = self.classify(
                content=content[:2000],  # Truncate for efficiency
                file_path=file_path,
                headings=headings
            )
            
            # Check if we got structured output or string
            if hasattr(result, 'classification') and hasattr(result, 'confidence') and hasattr(result, 'reasoning'):
                # Structured output - validate and convert
                doc_type_mapping = {
                    "tutorial": DocumentType.TUTORIAL,
                    "reference": DocumentType.REFERENCE, 
                    "example": DocumentType.EXAMPLE,
                    "concept": DocumentType.CONCEPT
                }
                
                # Handle both enum and string responses
                if isinstance(result.classification, DocumentType):
                    doc_type = result.classification
                else:
                    doc_type = doc_type_mapping.get(str(result.classification).lower(), DocumentType.CONCEPT)
                
                confidence = float(result.confidence) if result.confidence else 0.5
                confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
                
                return DocumentClassification(
                    file_path=file_path,
                    doc_type=doc_type,
                    confidence=confidence,
                    reasoning=str(result.reasoning)
                )
            else:
                # String output - use fallback parser
                logger.warning(f"Got string response for classification, using fallback parser")
                response_str = str(result) if hasattr(result, '__str__') else str(result.classification) if hasattr(result, 'classification') else ""
                return FallbackParser.parse_classification_response(response_str, file_path)
                
        except Exception as e:
            logger.error(f"Error in document classification: {e}")
            # Return default classification
            return DocumentClassification(
                file_path=file_path,
                doc_type=DocumentType.CONCEPT,
                confidence=0.3,
                reasoning=f"Classification failed: {str(e)}"
            )

class DependencyExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractDependencies)
    
    def forward(self, content: str, title: str, headings: List[str]):
        try:
            result = self.extract(
                content=content[:3000],  # Larger context for dependencies
                title=title,
                headings=headings
            )
            
            # Check if we got structured output
            if (hasattr(result, 'main_concepts') and 
                hasattr(result, 'prerequisites') and 
                hasattr(result, 'evidence')):
                
                # Structured output - process lists
                main_concepts = result.main_concepts
                prerequisites = result.prerequisites
                evidence = str(result.evidence)
                
                # Handle both list and string responses for concepts/prerequisites
                if isinstance(main_concepts, str):
                    main_concepts = [c.strip() for c in main_concepts.split(",") if c.strip()]
                if isinstance(prerequisites, str):
                    prerequisites = [p.strip() for p in prerequisites.split(",") if p.strip()]
                
                dependencies = []
                for concept in main_concepts:
                    if concept.strip():  # Only add non-empty concepts
                        dependencies.append(DependencyRelation(
                            concept=concept.strip(),
                            prerequisites=prerequisites,
                            confidence=0.8,
                            evidence=evidence
                        ))
                
                return dependencies
            else:
                # String output - use fallback parser
                logger.warning(f"Got string response for dependencies, using fallback parser")
                response_str = str(result) if hasattr(result, '__str__') else ""
                return FallbackParser.parse_dependencies_response(response_str)
                
        except Exception as e:
            logger.error(f"Error in dependency extraction: {e}")
            # Return minimal dependency
            return [DependencyRelation(
                concept=title or "Unknown",
                prerequisites=[],
                confidence=0.3,
                evidence=f"Dependency extraction failed: {str(e)}"
            )]  
        
class DocumentSummarizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.summarize = dspy.ChainOfThought(SummarizeDocument)
    
    def forward(self, content: str, title: str, doc_type: str):
        result = self.summarize(
            content=truncate_num_words(content, NUM_WORDS),
            title=title,
            doc_type=doc_type
        )
        return result.summary

class ModuleDiscoverer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.discover = dspy.ChainOfThought(DiscoverModules)
    
    def forward(self, content_summary: str, difficulty_level: str, user_modules: Optional[List[str]] = None):
        try:
            user_modules_str = ", ".join(user_modules) if user_modules else "none"
            
            result = self.discover(
                content_summary=content_summary,
                difficulty_level=difficulty_level,
                user_modules=user_modules_str
            )
            
            # Check if we got structured output
            if hasattr(result, 'modules') and hasattr(result, 'reasoning'):
                modules = result.modules
                reasoning = str(result.reasoning)
                
                # Handle case where modules is a string
                if isinstance(modules, str):
                    modules, reasoning = FallbackParser.parse_modules_response(modules)
                
                return modules, reasoning
            else:
                # String response - use fallback
                response_str = str(result)
                return FallbackParser.parse_modules_response(response_str)
                
        except Exception as e:
            logger.error(f"Error in module discovery: {e}")
            return ["Introduction", "Core Concepts", "Implementation"], "Fallback modules used due to error"

class ModuleOrderer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.order = dspy.ChainOfThought(OrderModules)
    
    def forward(self, modules: List[str], content_overview: str, difficulty_level: str):
        try:
            result = self.order(
                modules=modules,
                content_overview=content_overview,
                difficulty_level=difficulty_level
            )
            
            # Check if we got structured output
            if hasattr(result, 'ordered_modules') and hasattr(result, 'reasoning'):
                ordered_modules = result.ordered_modules
                reasoning = str(result.reasoning)
                
                # Handle case where ordered_modules is a string
                if isinstance(ordered_modules, str):
                    ordered_modules, reasoning = FallbackParser.parse_ordering_response(ordered_modules, modules)
                
                return ordered_modules, reasoning
            else:
                # String response - use fallback
                response_str = str(result)
                return FallbackParser.parse_ordering_response(response_str, modules)
                
        except Exception as e:
            logger.error(f"Error in module ordering: {e}")
            return modules, "Original order preserved due to error"

class QueryGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateSearchQueries)
    
    def forward(self, module_title: str, difficulty_level: str, doc_type: str, available_content: str):
        try:
            result = self.generate(
                module_title=module_title,
                difficulty_level=difficulty_level,
                doc_type=doc_type,
                available_content=available_content
            )
            
            # Check if we got structured output
            if hasattr(result, 'search_queries') and hasattr(result, 'reasoning'):
                queries = result.search_queries
                reasoning = str(result.reasoning)
                
                # Handle case where queries is a string
                if isinstance(queries, str):
                    queries = self._parse_queries_from_string(queries)
                
                return queries, reasoning
            else:
                # String response - parse it
                response_str = str(result)
                queries = self._parse_queries_from_string(response_str)
                return queries, "Generated from LLM response"
                
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            # Fallback to simple queries
            return [f"{module_title} {doc_type}", f"how to {module_title}"], "Fallback queries used"
    
    def _parse_queries_from_string(self, response: str) -> List[str]:
        """Parse search queries from string response"""
        queries = []
        
        try:
            # Look for numbered lists, bullet points, or quoted strings
            patterns = [
                r'\d+\.\s*["\']?([^"\'\n]+)["\']?',  # 1. "query"
                r'[-•*]\s*["\']?([^"\'\n]+)["\']?',  # - "query"
                r'"([^"]+)"',  # "quoted strings"
                r"'([^']+)'",  # 'quoted strings'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response)
                if matches:
                    queries = [q.strip() for q in matches if len(q.strip()) > 5][:5]
                    break
            
            # If no structured queries found, split by lines
            if not queries:
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                queries = [line for line in lines if len(line) > 5 and '?' not in line][:3]
            
            # Ensure we have at least one query
            if not queries:
                queries = ["basic information"]
                
        except Exception as e:
            logger.warning(f"Error parsing queries: {e}")
            queries = ["basic information"]
        
        return queries

class ContentSynthesizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.synthesize = dspy.ChainOfThought(SynthesizeContent)
    
    def forward(self, module_title: str, content_chunks: List[ContentChunk], 
                difficulty_level: str, bloom_level: str = "understand"):
        try:
            # Limit content to avoid token limits
            chunks_text = "\n\n".join([
                f"[{chunk.doc_type.upper()}] {chunk.title}:\n{chunk.content[:500]}..."  # Limit each chunk
                for chunk in content_chunks[:5]  # Limit number of chunks
            ])
            
            result = self.synthesize(
                module_title=module_title,
                content_chunks=chunks_text,
                difficulty_level=difficulty_level,
                bloom_level=bloom_level
            )
            
            if hasattr(result, 'lesson_text') and hasattr(result, 'key_concepts'):
                lesson_text = str(result.lesson_text) if result.lesson_text else f"Learning content for {module_title}"
                key_concepts = result.key_concepts if result.key_concepts else [module_title]
                
                if isinstance(key_concepts, str):
                    key_concepts = [c.strip() for c in key_concepts.split(',') if c.strip()]
                
                return lesson_text, key_concepts
            else:
                response_str = str(result) if result else f"Learning content for {module_title}"
                return response_str, [module_title]
                
        except Exception as e:
            logger.error(f"Error in content synthesis: {e}")
            return f"Learning content for {module_title}. This module covers important concepts related to {module_title}.", [module_title]

class ExerciseGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateExercises)
    
    def forward(self, module_title: str, lesson_content: str, 
                difficulty_level: str, available_examples: str):
        try:
            result = self.generate(
                module_title=module_title,
                lesson_content=lesson_content[:1500],  # Limit for token efficiency
                difficulty_level=difficulty_level,
                available_examples=available_examples[:1000]  # Limit examples too
            )
            
            if hasattr(result, 'exercises') and result.exercises is not None:
                exercises = result.exercises
                
                if isinstance(exercises, str):
                    exercises = ContentFallbackParser.parse_exercises_response(
                        exercises, module_title, difficulty_level
                    )
                elif not isinstance(exercises, list):
                    exercises = []
                
                return exercises if exercises else self._create_fallback_exercise(module_title, difficulty_level)
            else:
                response_str = str(result) if result else ""
                parsed = ContentFallbackParser.parse_exercises_response(
                    response_str, module_title, difficulty_level
                )
                return parsed if parsed else self._create_fallback_exercise(module_title, difficulty_level)
                
        except Exception as e:
            logger.error(f"Error generating exercises: {e}")
            return self._create_fallback_exercise(module_title, difficulty_level)
    
    def _create_fallback_exercise(self, module_title: str, difficulty_level: str) -> List[Exercise]:
        """Create fallback exercise when generation fails"""
        return [Exercise(
            title=f"Practice {module_title}",
            description=f"Apply the concepts learned in {module_title}",
            instructions=[
                f"Review the key concepts of {module_title}",
                f"Try implementing a simple example",
                f"Test your understanding with practical application"
            ],
            expected_outcome=f"Demonstrate understanding of {module_title} concepts",
            difficulty_level=difficulty_level
        )]

class AssessmentCreator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.create = dspy.ChainOfThought(CreateAssessment)
    
    def forward(self, module_title: str, lesson_content: str, 
                key_concepts: List[str], difficulty_level: str):
        try:
            result = self.create(
                module_title=module_title,
                lesson_content=lesson_content[:1500],
                key_concepts=key_concepts[:5],  # Limit concepts
                difficulty_level=difficulty_level
            )
            
            if hasattr(result, 'assessment_questions') and result.assessment_questions is not None:
                questions = result.assessment_questions
                
                if isinstance(questions, str):
                    questions = ContentFallbackParser.parse_assessment_response(
                        questions, module_title, difficulty_level
                    )
                elif not isinstance(questions, list):
                    questions = []
                
                return questions if questions else self._create_fallback_assessment(module_title, difficulty_level)
            else:
                response_str = str(result) if result else ""
                parsed = ContentFallbackParser.parse_assessment_response(
                    response_str, module_title, difficulty_level
                )
                return parsed if parsed else self._create_fallback_assessment(module_title, difficulty_level)
                
        except Exception as e:
            logger.error(f"Error creating assessment: {e}")
            return self._create_fallback_assessment(module_title, difficulty_level)
    
    def _create_fallback_assessment(self, module_title: str, difficulty_level: str) -> List[AssessmentQuestion]:
        """Create fallback assessment when generation fails"""
        return [
            AssessmentQuestion(
                question=f"What are the main concepts of {module_title}?",
                question_type="short_answer",
                correct_answer=f"The main concepts include the core principles and applications of {module_title}",
                explanation=f"Tests basic understanding of {module_title}",
                difficulty_level=difficulty_level
            ),
            AssessmentQuestion(
                question=f"How would you apply {module_title} in practice?",
                question_type="short_answer",
                correct_answer=f"Practical application involves implementing {module_title} concepts in real scenarios",
                explanation=f"Tests practical application skills",
                difficulty_level=difficulty_level
            )
        ]

class ObjectiveWriter(dspy.Module):
    def __init__(self):
        super().__init__()
        self.write = dspy.ChainOfThought(WriteLearningObjectives)
    
    def forward(self, module_title: str, lesson_content: str, 
                difficulty_level: str, bloom_level: str = "understand"):
        try:
            result = self.write(
                module_title=module_title,
                lesson_content=lesson_content[:1500],
                difficulty_level=difficulty_level,
                bloom_level=bloom_level
            )
            
            if hasattr(result, 'learning_objectives') and result.learning_objectives is not None:
                objectives = result.learning_objectives
                
                if isinstance(objectives, str):
                    obj_lines = [line.strip() for line in objectives.split('\n') if line.strip()]
                    objectives = [
                        LearningObjective(
                            objective=line.strip('- •*'),
                            bloom_level=bloom_level,
                            measurable_outcome=f"Demonstrate {bloom_level} of {module_title}"
                        )
                        for line in obj_lines[:5] if len(line.strip()) > 10
                    ]
                elif not isinstance(objectives, list):
                    objectives = []
                
                return objectives if objectives else self._create_fallback_objectives(module_title, bloom_level)
            else:
                return self._create_fallback_objectives(module_title, bloom_level)
                
        except Exception as e:
            logger.error(f"Error writing objectives: {e}")
            return self._create_fallback_objectives(module_title, bloom_level)
    
    def _create_fallback_objectives(self, module_title: str, bloom_level: str) -> List[LearningObjective]:
        """Create fallback objectives when generation fails"""
        return [
            LearningObjective(
                objective=f"Understand the core concepts of {module_title}",
                bloom_level=bloom_level,
                measurable_outcome=f"Explain the key principles of {module_title}"
            ),
            LearningObjective(
                objective=f"Apply {module_title} in practical scenarios",
                bloom_level="apply",
                measurable_outcome=f"Implement {module_title} concepts in real-world examples"
            )
        ]

class CodeExampleExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractCodeExamples)
    
    def forward(self, module_title: str, content_with_code: str, difficulty_level: str):
        try:
            # Limit content to avoid token issues
            limited_content = content_with_code[:2000] if content_with_code else ""
            
            result = self.extract(
                module_title=module_title,
                content_with_code=limited_content,
                difficulty_level=difficulty_level
            )
            
            if hasattr(result, 'code_examples') and result.code_examples is not None:
                examples = result.code_examples
                
                if isinstance(examples, str):
                    examples = self._extract_code_from_string(examples, module_title, difficulty_level)
                elif not isinstance(examples, list):
                    examples = []
                
                return examples if examples else []
            else:
                response_str = str(result) if result else ""
                return self._extract_code_from_string(response_str, module_title, difficulty_level)
                
        except Exception as e:
            logger.error(f"Error extracting code examples: {e}")
            return []
    
    def _extract_code_from_string(self, content: str, module_title: str, difficulty_level: str) -> List[CodeExample]:
        """Extract code examples from string content"""
        examples = []
        
        try:
            # Look for code blocks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
            
            for i, (lang, code) in enumerate(code_blocks[:3]):  # Max 3 examples
                if code.strip():
                    examples.append(CodeExample(
                        title=f"{module_title} Example {i+1}",
                        code=code.strip(),
                        language=lang.lower() if lang else 'text',
                        explanation=f"This example demonstrates {module_title} concepts",
                        difficulty_level=difficulty_level
                    ))
        except Exception as e:
            logger.warning(f"Error parsing code examples: {e}")
        
        return examples


