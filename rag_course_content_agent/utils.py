from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import hashlib
import git
import pickle
import logging
import json
import re
from collections import defaultdict
from urllib.parse import urlparse

from .models import (
    DocumentType, DocumentMetadata, DocumentClassification, 
    DependencyRelation, AnalyzedDocument, DocumentChunk, 
    QueryResult, CodeBlock, Exercise, AssessmentQuestion, 
    LearningObjective, CodeExample, ContentChunk
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 3000
CHUNK_OVERLAP = 100

def truncate_num_words(text: str, num_words: int = 3000):
    words = text.split()
    return ' '.join(words[:num_words])

class FallbackParser:
    @staticmethod
    def parse_classification_response(response: str, file_path: str) -> DocumentClassification:
        """Parse string response for classification when structured output fails"""
        
        # Default values
        doc_type = DocumentType.CONCEPT
        confidence = 0.5
        reasoning = "Fallback classification"
        
        try:
            # Try to extract classification type
            classification_patterns = [
                r"classification[:\s]+(\w+)",
                r"type[:\s]+(\w+)",
                r"category[:\s]+(\w+)",
                r"(tutorial|reference|example|concept)"
            ]
            
            for pattern in classification_patterns:
                match = re.search(pattern, response.lower())
                if match:
                    found_type = match.group(1).lower()
                    if found_type in ["tutorial", "reference", "example", "concept"]:
                        doc_type = DocumentType(found_type)
                        break
            
            # Try to extract confidence
            confidence_patterns = [
                r"confidence[:\s]+([0-9]*\.?[0-9]+)",
                r"score[:\s]+([0-9]*\.?[0-9]+)",
                r"([0-9]*\.?[0-9]+)"
            ]
            
            for pattern in confidence_patterns:
                match = re.search(pattern, response)
                if match:
                    try:
                        found_confidence = float(match.group(1))
                        if 0.0 <= found_confidence <= 1.0:
                            confidence = found_confidence
                            break
                        elif found_confidence > 1.0:  # Handle percentage
                            confidence = found_confidence / 100.0
                            break
                    except ValueError:
                        continue
            
            # Extract reasoning (usually the whole response or a specific part)
            reasoning_match = re.search(r"reasoning[:\s]+(.+)", response, re.IGNORECASE | re.DOTALL)
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
            else:
                reasoning = response[:200] + "..." if len(response) > 200 else response
                
        except Exception as e:
            logger.warning(f"Error parsing classification response: {e}")
        
        return DocumentClassification(
            file_path=file_path,
            doc_type=doc_type,
            confidence=confidence,
            reasoning=reasoning
        )
    
    @staticmethod
    def parse_dependencies_response(response: str) -> List[DependencyRelation]:
        """Parse string response for dependencies when structured output fails"""
        
        dependencies = []
        
        try:
            # Try to extract main concepts
            main_concepts = []
            concepts_patterns = [
                r"main concepts?[:\s]+(.+?)(?=prerequisites|evidence|$)",
                r"concepts?[:\s]+(.+?)(?=prerequisites|evidence|$)",
                r"topics?[:\s]+(.+?)(?=prerequisites|evidence|$)"
            ]
            
            for pattern in concepts_patterns:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    concepts_text = match.group(1)
                    # Split by common delimiters
                    main_concepts = [
                        c.strip().strip(',-.')
                        for c in re.split(r'[,\n\-•*]', concepts_text)
                        if c.strip() and len(c.strip()) > 2
                    ][:5]  # Limit to 5 concepts
                    break
            
            # Try to extract prerequisites
            prerequisites = []
            prereq_patterns = [
                r"prerequisites?[:\s]+(.+?)(?=evidence|main|$)",
                r"requires?[:\s]+(.+?)(?=evidence|main|$)",
                r"dependencies?[:\s]+(.+?)(?=evidence|main|$)"
            ]
            
            for pattern in prereq_patterns:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    prereq_text = match.group(1)
                    prerequisites = [
                        p.strip().strip(',-.')
                        for p in re.split(r'[,\n\-•*]', prereq_text)
                        if p.strip() and len(p.strip()) > 2
                    ][:5]  # Limit to 5 prerequisites
                    break
            
            # Extract evidence
            evidence = "Extracted from fallback parsing"
            evidence_patterns = [
                r"evidence[:\s]+(.+)",
                r"explanation[:\s]+(.+)",
                r"reasoning[:\s]+(.+)"
            ]
            
            for pattern in evidence_patterns:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    evidence = match.group(1).strip()[:500]  # Limit length
                    break
            
            # Create dependency relations
            if not main_concepts:
                main_concepts = ["Unknown concept"]
            
            for concept in main_concepts:
                dependencies.append(DependencyRelation(
                    concept=concept,
                    prerequisites=prerequisites,
                    confidence=0.6,  # Lower confidence for fallback
                    evidence=evidence
                ))
                
        except Exception as e:
            logger.warning(f"Error parsing dependencies response: {e}")
            # Return minimal dependency if parsing fails completely
            dependencies = [DependencyRelation(
                concept="Unknown concept",
                prerequisites=[],
                confidence=0.3,
                evidence="Fallback parsing failed"
            )]
        
        return dependencies

    @staticmethod
    def parse_modules_response(response: str) -> tuple[List[str], str]:
        """Parse module list from string response"""
        modules = []
        reasoning = ""
        
        try:
            # Look for numbered lists or bullet points
            module_patterns = [
                r'\d+\.\s*([^\n]+)',  # 1. Module Name
                r'[-•*]\s*([^\n]+)',  # - Module Name  
                r'^([A-Z][^\n:]+)$'   # Plain module names
            ]
            
            for pattern in module_patterns:
                matches = re.findall(pattern, response, re.MULTILINE)
                if matches:
                    modules = [m.strip().strip('.,') for m in matches if len(m.strip()) > 3][:8]
                    break
            
            # If no modules found, try to split by common delimiters
            if not modules:
                lines = response.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3 and len(line) < 100:
                        # Skip lines that look like reasoning or explanations
                        if not any(word in line.lower() for word in ["because", "since", "therefore", "however", "reasoning", "based on"]):
                            modules.append(line.strip('.,'))
                    if len(modules) >= 8:
                        break
            
            # Extract reasoning
            reasoning_patterns = [
                r"reasoning[:\s]+(.+)",
                r"explanation[:\s]+(.+)",
                r"because[:\s]+(.+)"
            ]
            
            for pattern in reasoning_patterns:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    reasoning = match.group(1).strip()[:300]  # Limit length
                    break
            
            if not reasoning:
                reasoning = "Generated from content analysis"
                
        except Exception as e:
            logger.warning(f"Error parsing modules response: {e}")
            modules = ["Basic Introduction", "Core Concepts", "Advanced Topics"]
            reasoning = "Fallback module generation"
        
        return modules, reasoning

    @staticmethod
    def parse_ordering_response(response: str, original_modules: List[str]) -> tuple[List[str], str]:
        """Parse ordered module list from string response"""
        ordered_modules = []
        reasoning = ""
        
        try:
            # Look for numbered lists first
            numbered_pattern = r'\d+\.\s*([^\n]+)'
            matches = re.findall(numbered_pattern, response, re.MULTILINE)
            
            if matches:
                # Match found modules with original modules
                for match in matches:
                    match_cleaned = match.strip().strip('.,')
                    # Find best match from original modules
                    best_match = None
                    best_score = 0
                    
                    for original in original_modules:
                        # Simple similarity check
                        if original.lower() in match_cleaned.lower() or match_cleaned.lower() in original.lower():
                            score = len(set(original.lower().split()) & set(match_cleaned.lower().split()))
                            if score > best_score:
                                best_score = score
                                best_match = original
                    
                    if best_match:
                        ordered_modules.append(best_match)
                    else:
                        # If no good match, keep the original text
                        ordered_modules.append(match_cleaned)
            
            # If no numbered list found, try to find modules mentioned in order
            if not ordered_modules:
                response_lower = response.lower()
                for module in original_modules:
                    if module.lower() in response_lower:
                        ordered_modules.append(module)
            
            # If still no order found, return original order
            if not ordered_modules:
                ordered_modules = original_modules[:]
            
            # Extract reasoning
            reasoning_patterns = [
                r"reasoning[:\s]+(.+)",
                r"explanation[:\s]+(.+)",
                r"order[:\s]+(.+)"
            ]
            
            for pattern in reasoning_patterns:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    reasoning = match.group(1).strip()[:300]
                    break
            
            if not reasoning:
                reasoning = "Ordered based on logical progression"
                
        except Exception as e:
            logger.warning(f"Error parsing ordering response: {e}")
            ordered_modules = original_modules[:]
            reasoning = "Fallback ordering applied"
        
        return ordered_modules, reasoning

class ContentFallbackParser:
    @staticmethod
    def parse_exercises_response(response: str, module_title: str, difficulty_level: str) -> List[Exercise]:
        """Parse exercises from string response"""
        exercises = []
        
        try:
            # Look for numbered exercises
            exercise_patterns = [
                r'\d+\.\s*([^\n]+)',
                r'Exercise\s*\d*[:\s]*([^\n]+)',
                r'Task\s*\d*[:\s]*([^\n]+)',
                r'Problem\s*\d*[:\s]*([^\n]+)'
            ]
            
            for pattern in exercise_patterns:
                matches = re.findall(pattern, response, re.MULTILINE | re.IGNORECASE)
                if matches:
                    for i, match in enumerate(matches[:5]):  # Limit to 5 exercises
                        exercises.append(Exercise(
                            title=f"{module_title} Exercise {i+1}",
                            description=match.strip(),
                            difficulty_level=difficulty_level,
                            estimated_time=15,
                            hints=[]
                        ))
                    break
            
            # If no exercises found, create generic ones
            if not exercises:
                exercises = [
                    Exercise(
                        title=f"{module_title} Practice",
                        description=f"Practice the concepts learned in {module_title}",
                        difficulty_level=difficulty_level,
                        estimated_time=20,
                        hints=[]
                    )
                ]
                
        except Exception as e:
            logger.warning(f"Error parsing exercises response: {e}")
            exercises = [Exercise(
                title=f"{module_title} Exercise",
                description=f"Complete an exercise related to {module_title}",
                difficulty_level=difficulty_level,
                estimated_time=15,
                hints=[]
            )]
        
        return exercises

    @staticmethod
    def parse_assessment_response(response: str, module_title: str, difficulty_level: str) -> List[AssessmentQuestion]:
        """Parse assessment questions from string response"""
        questions = []
        
        try:
            # Look for numbered questions
            question_patterns = [
                r'\d+\.\s*([^\n]+)',
                r'Question\s*\d*[:\s]*([^\n]+)',
                r'Q\d*[:\s]*([^\n]+)'
            ]
            
            for pattern in question_patterns:
                matches = re.findall(pattern, response, re.MULTILINE | re.IGNORECASE)
                if matches:
                    for i, match in enumerate(matches[:5]):  # Limit to 5 questions
                        question_text = match.strip()
                        
                        # Generate some basic options
                        options = [
                            f"Option A for {module_title}",
                            f"Option B for {module_title}",
                            f"Option C for {module_title}",
                            f"Option D for {module_title}"
                        ]
                        
                        questions.append(AssessmentQuestion(
                            question=question_text,
                            options=options,
                            correct_answer=0,  # Default to first option
                            explanation=f"This question tests understanding of {module_title}",
                            difficulty_level=difficulty_level,
                            bloom_level="understand"
                        ))
                    break
            
            # If no questions found, create generic ones
            if not questions:
                questions = [
                    AssessmentQuestion(
                        question=f"What is the main concept of {module_title}?",
                        options=[
                            f"Core concept of {module_title}",
                            f"Alternative interpretation",
                            f"Related but different concept",
                            f"Unrelated concept"
                        ],
                        correct_answer=0,
                        explanation=f"This question assesses understanding of {module_title}",
                        difficulty_level=difficulty_level,
                        bloom_level="understand"
                    )
                ]
                
        except Exception as e:
            logger.warning(f"Error parsing assessment response: {e}")
            questions = [AssessmentQuestion(
                question=f"Question about {module_title}",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer=0,
                explanation=f"Assessment question for {module_title}",
                difficulty_level=difficulty_level,
                bloom_level="understand"
            )]
        
        return questions
