#!/usr/bin/env python3
"""
DSPy-based Adaptive Tutor Agent with MCP Integration
Uses MCP Educational Server tools directly through DSPy ReAct pattern
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Literal, Union
from datetime import datetime
from enum import Enum

import dspy
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums for better type safety
class LearningStyle(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"

class KnowledgeLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class TeachingStrategy(str, Enum):
    SOCRATIC = "socratic"
    EXPLANATORY = "explanatory"
    CONVERSATIONAL = "conversational"
    EXAMPLE_DRIVEN = "example-driven"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    role: Literal["student", "tutor", "system"] = Field(..., description="Who sent the message")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the message was sent")
    concepts_mentioned: List[str] = Field(default_factory=list, description="MCP concepts referenced")

class StudentProfile(BaseModel):
    """Student learning profile and preferences with validation"""
    model_config = ConfigDict(use_enum_values=True)
    
    id: str = Field(..., min_length=1, description="Unique student identifier")
    name: str = Field(..., min_length=1, description="Student name")
    learning_style: LearningStyle = Field(default=LearningStyle.VISUAL, description="Preferred learning style")
    knowledge_level: KnowledgeLevel = Field(default=KnowledgeLevel.BEGINNER, description="Current knowledge level")
    interests: List[str] = Field(default_factory=lambda: ["technology", "programming"], description="Student interests")
    learning_goals: List[str] = Field(default_factory=lambda: ["understand MCP concepts"], description="Learning objectives")
    strengths: List[str] = Field(default_factory=list, description="Areas of strength")
    struggle_areas: List[str] = Field(default_factory=list, description="Areas needing improvement")
    preferred_complexity: DifficultyLevel = Field(default=DifficultyLevel.INTERMEDIATE, description="Preferred explanation complexity")
    
    @field_validator('interests', 'learning_goals', 'strengths', 'struggle_areas')
    def validate_lists_not_empty_strings(cls, v):
        """Ensure list items are not empty strings"""
        return [item.strip() for item in v if item.strip()]

class ConversationContext(BaseModel):
    """Context from previous interactions with validation"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        use_enum_values=True
    )
    
    student_id: str = Field(..., min_length=1, description="Student identifier")
    messages: List[ConversationMessage] = Field(default_factory=list, description="Conversation history")
    current_topic: Optional[str] = Field(None, description="Current discussion topic")
    teaching_strategy: Optional[TeachingStrategy] = Field(None, description="Current teaching approach")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction timestamp")
    session_start: datetime = Field(default_factory=datetime.now, description="When session started")
    concepts_covered: List[str] = Field(default_factory=list, description="Concepts covered in session")
    
    def add_message(self, role: Literal["student", "tutor", "system"], content: str, concepts: List[str] = None):
        """Add a message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            concepts_mentioned=concepts or []
        )
        self.messages.append(message)
        self.last_interaction = datetime.now()
        
        # Update concepts covered
        if concepts:
            for concept in concepts:
                if concept not in self.concepts_covered:
                    self.concepts_covered.append(concept)
    
    @property
    def session_duration(self) -> float:
        """Get session duration in minutes"""
        if self.last_interaction:
            return (self.last_interaction - self.session_start).total_seconds() / 60
        return 0.0

class TeachingResponse(BaseModel):
    """Complete teaching response with metadata"""
    model_config = ConfigDict(use_enum_values=True)
    
    response: str = Field(..., min_length=1, description="The actual teaching response")
    teaching_strategy: TeachingStrategy = Field(..., description="Strategy used for this response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in response quality")
    concepts_covered: List[str] = Field(..., description="Concepts addressed in response")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level of response")
    tools_used: List[str] = Field(default_factory=list, description="MCP tools used in generating response")
    reasoning_steps: List[str] = Field(default_factory=list, description="DSPy reasoning trajectory")

class ProgressMetrics(BaseModel):
    """Student progress tracking metrics"""
    model_config = ConfigDict(use_enum_values=True)
    
    student_id: str = Field(..., description="Student identifier")
    total_interactions: int = Field(default=0, ge=0, description="Total number of interactions")
    concepts_learned: List[str] = Field(default_factory=list, description="Concepts the student has learned")
    current_knowledge_level: KnowledgeLevel = Field(default=KnowledgeLevel.BEGINNER, description="Estimated current level")
    engagement_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Engagement level (0-1)")
    learning_velocity: float = Field(default=1.0, ge=0.1, le=3.0, description="Rate of learning (concepts/hour)")
    session_count: int = Field(default=0, ge=0, description="Number of learning sessions")
    average_session_duration: float = Field(default=0.0, ge=0.0, description="Average session duration in minutes")

# DSPy Signatures for MCP Educational Tutor

class MCPEducationalTutorSignature(dspy.Signature):
    """
    DSPy signature for educational tutoring using MCP server tools.
    Uses ReAct pattern to decide which MCP tools to call for personalized learning.
    """
    
    student_query: str = dspy.InputField(desc="The student's question or learning request about MCP concepts")
    student_profile: str = dspy.InputField(desc="JSON string of student's learning style, knowledge level, interests, and goals")
    conversation_history: str = dspy.InputField(desc="JSON string of recent conversation messages showing learning progress")
    
    educational_response: str = dspy.OutputField(
        desc="Comprehensive educational response that addresses the student's query. Should be personalized to their learning style and knowledge level, incorporating information gathered from MCP tools."
    )

class ConceptExplorationSignature(dspy.Signature):
    """
    Signature for exploring specific MCP concepts in depth using available tools.
    """
    
    concept_name: str = dspy.InputField(desc="The specific MCP concept to explore (e.g., 'tools', 'resources', 'prompts')")
    student_level: str = dspy.InputField(desc="Student's knowledge level: beginner, intermediate, or advanced")
    learning_style: str = dspy.InputField(desc="Student's preferred learning style: visual, auditory, kinesthetic, or reading")
    
    concept_explanation: str = dspy.OutputField(
        desc="Detailed explanation of the MCP concept tailored to the student's level and learning style, using examples and documentation from MCP tools"
    )

class LearningPathSignature(dspy.Signature):
    """
    Signature for generating personalized learning paths using MCP documentation.
    """
    
    student_goals: str = dspy.InputField(desc="Student's learning goals and objectives")
    current_knowledge: str = dspy.InputField(desc="Student's current knowledge level and concepts already learned")
    available_content: str = dspy.InputField(desc="Available MCP documentation and resources from tools")
    
    learning_path: str = dspy.OutputField(
        desc="Structured learning path with recommended sequence of topics, resources, and practical exercises based on MCP documentation"
    )

class MCPAdaptiveTutor:
    """
    Enhanced DSPy-powered adaptive tutor that uses MCP Educational Server tools
    
    Uses DSPy ReAct pattern to intelligently call MCP tools for:
    - Searching MCP documentation
    - Retrieving specific documents  
    - Finding code examples
    - Listing available resources
    
    Provides personalized educational experiences through tool-augmented reasoning.
    """
    
    def __init__(self, mcp_server_path: str = "mcp_server/main.py", llm_model: str = "gpt-4o-mini"):
        """Initialize the adaptive tutor with MCP server connection"""
        self.mcp_server_path = mcp_server_path
        self.conversations: Dict[str, ConversationContext] = {}
        self.student_profiles: Dict[str, StudentProfile] = {}
        self.progress_metrics: Dict[str, ProgressMetrics] = {}
        
        # Configure DSPy
        self.configure_dspy(llm_model)
        
        # MCP server parameters
        self.server_params = StdioServerParameters(
            command="python",
            args=[self.mcp_server_path],
            env=None,
        )
        
        logger.info("✅ Enhanced MCPAdaptiveTutor initialized with MCP integration")
    
    def configure_dspy(self, model: str):
        """Configure DSPy with the specified language model"""
        try:
            dspy.configure(lm=dspy.LM(f"openai/{model}"))
            logger.info(f"✅ DSPy configured with {model}")
        except Exception as e:
            logger.warning(f"⚠️  Could not configure OpenAI model: {e}")
            logger.info("💡 Falling back to mock LM for testing")
            dspy.configure(lm=MockLanguageModel())
    
    async def teach(self, student_id: str, query: str, student_profile: Optional[StudentProfile] = None) -> TeachingResponse:
        """
        Main teaching method using MCP tools through DSPy ReAct
        
        Args:
            student_id: Unique identifier for the student
            query: Student's question or learning request
            student_profile: Optional student profile (creates default if not provided)
            
        Returns:
            TeachingResponse model with structured response and metadata
        """
        
        # Get or create student profile
        if student_profile:
            self.student_profiles[student_id] = student_profile
        elif student_id not in self.student_profiles:
            self.student_profiles[student_id] = self._create_default_profile(student_id)
        
        profile = self.student_profiles[student_id]
        
        # Get or create conversation context
        if student_id not in self.conversations:
            self.conversations[student_id] = ConversationContext(student_id=student_id)
        
        context = self.conversations[student_id]
        
        # Get or create progress metrics
        if student_id not in self.progress_metrics:
            self.progress_metrics[student_id] = ProgressMetrics(student_id=student_id)
        
        progress = self.progress_metrics[student_id]
        progress.total_interactions += 1
        
        try:
            # Use MCP tools through DSPy ReAct
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize MCP connection
                    await session.initialize()
                    
                    # Get available MCP tools
                    tools_response = await session.list_tools()
                    
                    # Convert MCP tools to DSPy tools
                    dspy_tools = []
                    for tool in tools_response.tools:
                        dspy_tools.append(dspy.Tool.from_mcp_tool(session, tool))
                    
                    logger.info(f"✅ Loaded {len(dspy_tools)} MCP tools for tutoring")
                    
                    # Create ReAct agent with MCP tools
                    react_agent = dspy.ReAct(MCPEducationalTutorSignature, tools=dspy_tools)
                    
                    # Prepare inputs for the agent
                    profile_data = profile.model_dump()
                    recent_messages = context.messages[-5:] if len(context.messages) > 5 else context.messages
                    history_data = [msg.model_dump() for msg in recent_messages]
                    
                    # Call the ReAct agent
                    result = await react_agent.acall(
                        student_query=query,
                        student_profile=json.dumps(profile_data),
                        conversation_history=json.dumps(history_data)
                    )
                    
                    # Extract tools used and reasoning from trajectory
                    tools_used = []
                    reasoning_steps = []
                    
                    if hasattr(result, 'trajectory') and result.trajectory:
                        for key, value in result.trajectory.items():
                            if key.startswith('tool_name_') and value != 'finish':
                                tools_used.append(value)
                            elif key.startswith('thought_'):
                                reasoning_steps.append(value)
                    
                    # Determine teaching strategy based on tools used and content
                    teaching_strategy = self._determine_teaching_strategy(tools_used, result.educational_response, profile)
                    
                    # Extract concepts from response and tools used
                    concepts_covered = self._extract_concepts_from_response(result.educational_response, tools_used)
                    
                    # Create structured response
                    teaching_response = TeachingResponse(
                        response=result.educational_response,
                        teaching_strategy=teaching_strategy,
                        confidence=getattr(result, 'confidence', 0.8),  # DSPy ReAct doesn't provide confidence by default
                        concepts_covered=concepts_covered,
                        difficulty_level=self._estimate_difficulty_level(result.educational_response, profile),
                        tools_used=tools_used,
                        reasoning_steps=reasoning_steps
                    )
                    
                    # Update conversation context
                    context.add_message("student", query, concepts_covered)
                    context.add_message("tutor", result.educational_response, concepts_covered)
                    context.current_topic = concepts_covered[0] if concepts_covered else None
                    context.teaching_strategy = teaching_strategy
                    
                    # Update progress metrics
                    await self._update_progress_metrics(student_id, concepts_covered, teaching_response.confidence)
                    
                    return teaching_response
                    
        except Exception as e:
            logger.error(f"❌ Error in MCP-enhanced teaching method: {e}")
            # Return a safe fallback response
            return TeachingResponse(
                response="I apologize, but I encountered an issue accessing the MCP educational resources. Let me help you with general MCP concepts. Could you please rephrase your question or ask about a specific MCP topic?",
                teaching_strategy=TeachingStrategy.CONVERSATIONAL,
                confidence=0.3,
                concepts_covered=[],
                difficulty_level=DifficultyLevel.BEGINNER,
                tools_used=[],
                reasoning_steps=["Fallback response due to MCP connection error"]
            )
    
    async def explore_concept(self, student_id: str, concept_name: str) -> TeachingResponse:
        """
        Explore a specific MCP concept in depth using available tools
        """
        if student_id not in self.student_profiles:
            self.student_profiles[student_id] = self._create_default_profile(student_id)
        
        profile = self.student_profiles[student_id]
        
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()
                    
                    dspy_tools = []
                    for tool in tools_response.tools:
                        dspy_tools.append(dspy.Tool.from_mcp_tool(session, tool))
                    
                    # Create specialized concept exploration agent
                    concept_agent = dspy.ReAct(ConceptExplorationSignature, tools=dspy_tools)
                    
                    result = await concept_agent.acall(
                        concept_name=concept_name,
                        student_level=profile.knowledge_level.value,
                        learning_style=profile.learning_style.value
                    )
                    
                    # Extract metadata from trajectory
                    tools_used = []
                    reasoning_steps = []
                    
                    if hasattr(result, 'trajectory') and result.trajectory:
                        for key, value in result.trajectory.items():
                            if key.startswith('tool_name_') and value != 'finish':
                                tools_used.append(value)
                            elif key.startswith('thought_'):
                                reasoning_steps.append(value)
                    
                    return TeachingResponse(
                        response=result.concept_explanation,
                        teaching_strategy=TeachingStrategy.EXPLANATORY,
                        confidence=0.85,
                        concepts_covered=[concept_name],
                        difficulty_level=DifficultyLevel(profile.knowledge_level.value),
                        tools_used=tools_used,
                        reasoning_steps=reasoning_steps
                    )
                    
        except Exception as e:
            logger.error(f"❌ Error in concept exploration: {e}")
            return TeachingResponse(
                response=f"I encountered an issue exploring the concept '{concept_name}'. Let me provide a general overview instead.",
                teaching_strategy=TeachingStrategy.CONVERSATIONAL,
                confidence=0.4,
                concepts_covered=[concept_name],
                difficulty_level=DifficultyLevel.BEGINNER,
                tools_used=[],
                reasoning_steps=["Fallback due to exploration error"]
            )
    
    def _determine_teaching_strategy(self, tools_used: List[str], response: str, profile: StudentProfile) -> TeachingStrategy:
        """Determine teaching strategy based on tools used and response content"""
        if "get_code_example" in tools_used:
            return TeachingStrategy.EXAMPLE_DRIVEN
        elif "search_mcp_concepts" in tools_used and len(tools_used) > 1:
            return TeachingStrategy.EXPLANATORY
        elif "?" in response and response.count("?") > 2:
            return TeachingStrategy.SOCRATIC
        else:
            return TeachingStrategy.CONVERSATIONAL
    
    def _extract_concepts_from_response(self, response: str, tools_used: List[str]) -> List[str]:
        """Extract MCP concepts mentioned in the response"""
        mcp_concepts = [
            "tools", "resources", "prompts", "server", "client", "protocol",
            "handlers", "context", "parameters", "responses", "errors",
            "authentication", "security", "schemas", "validation"
        ]
        
        concepts_found = []
        response_lower = response.lower()
        
        for concept in mcp_concepts:
            if concept in response_lower:
                concepts_found.append(concept)
        
        # Add concepts implied by tools used
        if "search_mcp_concepts" in tools_used:
            concepts_found.extend(["search", "documentation"])
        if "get_code_example" in tools_used:
            concepts_found.extend(["examples", "implementation"])
        
        return list(set(concepts_found))  # Remove duplicates
    
    def _estimate_difficulty_level(self, response: str, profile: StudentProfile) -> DifficultyLevel:
        """Estimate difficulty level of the response content"""
        # Simple heuristic based on response complexity and student level
        word_count = len(response.split())
        code_blocks = response.count("```")
        technical_terms = sum(1 for term in ["implementation", "architecture", "protocol", "schema"] if term in response.lower())
        
        if profile.knowledge_level == KnowledgeLevel.BEGINNER:
            if word_count < 200 and technical_terms < 2:
                return DifficultyLevel.BEGINNER
            else:
                return DifficultyLevel.INTERMEDIATE
        elif profile.knowledge_level == KnowledgeLevel.INTERMEDIATE:
            if code_blocks > 2 or technical_terms > 3:
                return DifficultyLevel.ADVANCED
            else:
                return DifficultyLevel.INTERMEDIATE
        else:  # Advanced
            if technical_terms > 5 or word_count > 500:
                return DifficultyLevel.EXPERT
            else:
                return DifficultyLevel.ADVANCED

    def _create_default_profile(self, student_id: str) -> StudentProfile:
        """Create a default student profile"""
        return StudentProfile(
            id=student_id,
            name=f"Student_{student_id}",
            learning_style="visual",
            knowledge_level="beginner",
            interests=["programming", "technology"],
            learning_goals=["understand MCP concepts", "build MCP applications"]
        )

    async def _update_progress_metrics(self, student_id: str, concepts_covered: List[str], confidence: float):
        """Update student progress metrics"""
        if student_id not in self.progress_metrics:
            self.progress_metrics[student_id] = ProgressMetrics(student_id=student_id)
        
        progress = self.progress_metrics[student_id]
        
        # Update concepts learned (avoid duplicates)
        for concept in concepts_covered:
            if concept not in progress.concepts_learned:
                progress.concepts_learned.append(concept)
        
        # Update engagement score based on confidence
        progress.engagement_score = (progress.engagement_score * 0.8 + confidence * 0.2)
        
        # Update learning velocity (concepts per interaction)
        if progress.total_interactions > 0:
            progress.learning_velocity = len(progress.concepts_learned) / progress.total_interactions
        
        logger.info(f"📊 Progress updated for {student_id}: {len(concepts_covered)} new concepts, confidence: {confidence:.2f}")
    
    def get_student_progress(self, student_id: str) -> Dict[str, Any]:
        """Get current student progress and profile"""
        
        if student_id not in self.student_profiles:
            return {"error": "Student not found"}
        
        profile = self.student_profiles[student_id]
        context = self.conversations.get(student_id, ConversationContext(student_id=student_id))
        progress = self.progress_metrics.get(student_id, ProgressMetrics(student_id=student_id))
        
        return {
            "student_id": student_id,
            "profile": profile.model_dump(),
            "conversation_length": len(context.messages),
            "current_topic": context.current_topic,
            "last_strategy": context.teaching_strategy.value if context.teaching_strategy else None,
            "last_interaction": context.last_interaction.isoformat() if context.last_interaction else None,
            "concepts_learned": progress.concepts_learned,
            "engagement_score": progress.engagement_score,
            "learning_velocity": progress.learning_velocity,
            "session_duration": context.session_duration
        }
    
    async def generate_learning_path(self, student_id: str, target_concepts: List[str]) -> str:
        """Generate a personalized learning path using MCP tools"""
        if student_id not in self.student_profiles:
            self.student_profiles[student_id] = self._create_default_profile(student_id)
        
        profile = self.student_profiles[student_id]
        progress = self.progress_metrics.get(student_id, ProgressMetrics(student_id=student_id))
        
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()
                    
                    dspy_tools = []
                    for tool in tools_response.tools:
                        dspy_tools.append(dspy.Tool.from_mcp_tool(session, tool))
                    
                    # Create learning path generator
                    path_generator = dspy.ReAct(LearningPathSignature, tools=dspy_tools)
                    
                    result = await path_generator.acall(
                        student_goals=", ".join(profile.learning_goals),
                        current_knowledge=f"Level: {profile.knowledge_level.value}, Learned: {', '.join(progress.concepts_learned)}",
                        available_content="MCP documentation, tools, resources, prompts, code examples"
                    )
                    
                    return result.learning_path
                    
        except Exception as e:
            logger.error(f"❌ Error generating learning path: {e}")
            return f"Unable to generate personalized learning path. Recommended starting points: {', '.join(target_concepts[:3])}"

class MockLanguageModel:
    """Mock language model for testing without API keys"""
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Generate mock responses for testing"""
        if "MCP" in prompt or "tool" in prompt.lower():
            return "I'd be happy to explain MCP concepts! MCP (Model Context Protocol) is a standardized way for AI applications to securely access external resources and tools. Would you like to learn about tools, prompts, or resources specifically?"
        else:
            return "That's a great question! Let me help you understand this better using the available MCP tools. What specific aspect would you like to explore?"

async def main():
    """Main entry point for the MCP-enhanced tutor agent"""
    print("🚀 Starting MCP-Enhanced Adaptive Tutor Agent...")
    
    # Initialize the tutor with MCP integration
    tutor = MCPAdaptiveTutor(
        mcp_server_path="mcp_server/main.py",  # Path to our MCP educational server
        llm_model="gpt-4o-mini"
    )
    
    # Create example student profile
    student_profile = StudentProfile(
        id="demo_student",
        name="Alex Developer",
        learning_style=LearningStyle.VISUAL,
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=["web development", "APIs", "automation"],
        learning_goals=["understand MCP architecture", "build MCP server", "integrate MCP tools"],
        preferred_complexity=DifficultyLevel.INTERMEDIATE
    )
    
    # Demo conversation showcasing MCP tool integration
    print("\n💬 Demo Conversation with MCP Tool Integration:")
    print("=" * 60)
    
    queries = [
        "What is MCP and how does it work?",
        "Can you show me how to create MCP tools?",
        "I want to build an MCP server for my project. Where should I start?",
        "What are the best practices for MCP security?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n👤 Student: {query}")
        print("-" * 40)
        
        try:
            # Use the MCP-enhanced teaching method
            result = await tutor.teach("demo_student", query, student_profile)
            
            print(f"🤖 Tutor ({result.teaching_strategy.value}):")
            print(f"Response: {result.response[:300]}...")
            print(f"📊 Confidence: {result.confidence:.2f}")
            print(f"🔧 Tools Used: {', '.join(result.tools_used)}")
            print(f"📚 Concepts: {', '.join(result.concepts_covered)}")
            print(f"🎯 Difficulty: {result.difficulty_level.value}")
            
            if result.reasoning_steps:
                print(f"🧠 Reasoning: {result.reasoning_steps[0]}")
            
        except Exception as e:
            print(f"❌ Error in demo: {e}")
        
        if i < len(queries):
            print("\n" + "─" * 50)
    
    # Demonstrate concept exploration
    print(f"\n🔍 Concept Exploration Demo:")
    print("=" * 40)
    
    concept_result = await tutor.explore_concept("demo_student", "tools")
    print(f"📖 Exploring 'tools' concept:")
    print(f"Response: {concept_result.response[:200]}...")
    print(f"🔧 Tools Used: {', '.join(concept_result.tools_used)}")
    
    # Show student progress
    progress = tutor.get_student_progress("demo_student")
    print(f"\n📈 Student Progress Summary:")
    print("=" * 40)
    print(f"👤 Student: {progress['profile']['name']}")
    print(f"💬 Interactions: {progress['conversation_length']}")
    print(f"🎯 Current Topic: {progress['current_topic']}")
    print(f"📚 Concepts Learned: {len(progress['concepts_learned'])}")
    print(f"📊 Engagement Score: {progress['engagement_score']:.2f}")
    print(f"⚡ Learning Velocity: {progress['learning_velocity']:.2f} concepts/interaction")
    print(f"⏱️  Session Duration: {progress['session_duration']:.1f} minutes")
    
    # Generate learning path
    print(f"\n🗺️  Personalized Learning Path:")
    print("=" * 40)
    
    learning_path = await tutor.generate_learning_path("demo_student", ["servers", "clients", "authentication"])
    print(f"Path: {learning_path[:200]}...")
    
    print("\n✨ MCP-Enhanced Adaptive Tutor Agent Demo Complete!")
    print("\n🎓 Key Features Demonstrated:")
    print("  • MCP tool integration through DSPy ReAct")
    print("  • Personalized responses based on student profiles")
    print("  • Automatic concept extraction and progress tracking")
    print("  • Teaching strategy adaptation based on tool usage")
    print("  • Structured learning path generation")
    print("  • Real-time access to MCP educational resources")

if __name__ == "__main__":
    asyncio.run(main()) 