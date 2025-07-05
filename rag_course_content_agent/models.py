from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set
from dataclasses import dataclass
from enum import Enum
import json
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    EXAMPLE = "example"
    CONCEPT = "concept"

class CodeBlock(BaseModel):
    language: str
    content: str
    line_start: int
    line_end: int

class DocumentMetadata(BaseModel):
    file_path: str
    title: Optional[str] = None
    headings: List[str] = Field(default_factory=list)
    code_blocks: List[CodeBlock] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    word_count: int = 0

class DocumentClassification(BaseModel):
    file_path: str
    doc_type: DocumentType
    confidence: float
    reasoning: str

class DependencyRelation(BaseModel):
    concept: str
    prerequisites: List[str] = Field(default_factory=list)
    confidence: float
    evidence: str

class AnalyzedDocument(BaseModel):
    metadata: DocumentMetadata
    classification: DocumentClassification
    content: str
    dependencies: List[DependencyRelation] = Field(default_factory=list)
    summary: str = ""

class DocumentChunk(BaseModel):
    """Represents a chunk with contextual information"""
    id: str
    content: str
    contextual_content: str  # Original content + document summary
    metadata: Dict[str, Any]

class QueryResult(BaseModel):
    """Result from vector database query"""
    chunk: DocumentChunk
    score: float

class LearningModule(BaseModel):
    """A learning module covering a specific topic"""
    title: str
    tutorial_content: List[str] = Field(default_factory=list)  # chunk IDs
    concept_content: List[str] = Field(default_factory=list)   # chunk IDs  
    example_content: List[str] = Field(default_factory=list)   # chunk IDs
    reference_content: List[str] = Field(default_factory=list) # chunk IDs
    estimated_time: int = 0  # minutes
    content_summary: str = ""

class LearningPath(BaseModel):
    """Complete learning path with ordered modules"""
    modules: List[LearningModule]
    difficulty_level: str = "intermediate"
    total_time: int = 0
    module_count: int = 0
    discovery_reasoning: str = ""
    ordering_reasoning: str = ""
    content_gaps: List[str] = Field(default_factory=list)

class ContentSummary(BaseModel):
    """Summary of available documentation content"""
    total_docs: int
    doc_types: Dict[str, int]  # {"tutorial": 5, "concept": 10, ...}
    main_topics: List[str]
    sample_titles: List[str]

class CodeExample(BaseModel):
    """A code example with explanation"""
    title: str
    code: str
    language: str
    explanation: str
    difficulty_level: str

class Exercise(BaseModel):
    """A practical exercise for learners"""
    title: str
    description: str
    instructions: List[str]
    hints: List[str] = Field(default_factory=list)
    expected_outcome: str
    difficulty_level: str

class AssessmentQuestion(BaseModel):
    """An assessment question to test understanding"""
    question: str
    question_type: str  # multiple_choice, true_false, short_answer, code_completion
    options: List[str] = Field(default_factory=list)  # For multiple choice
    correct_answer: str
    explanation: str
    difficulty_level: str

class LearningObjective(BaseModel):
    """A specific learning objective"""
    objective: str
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    measurable_outcome: str

class GeneratedContent(BaseModel):
    """Complete generated content for a learning module"""
    module_title: str
    learning_objectives: List[LearningObjective]
    lesson_text: str
    code_examples: List[CodeExample]
    exercises: List[Exercise]
    assessment_questions: List[AssessmentQuestion]
    estimated_time: int
    prerequisites: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)

class ContentChunk(BaseModel):
    """Content chunk retrieved from vector DB"""
    id: str
    content: str
    doc_type: str
    title: str
    metadata: Dict[str, Any]
