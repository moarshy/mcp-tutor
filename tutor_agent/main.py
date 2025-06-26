#!/usr/bin/env python3
"""
Simplified DSPy-based Adaptive Tutor Agent with MCP Integration
Uses MCP Educational Server tools directly through DSPy ReAct pattern
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv
import os

import dspy
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Silence LiteLLM verbose logs
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Simplified Enums
class KnowledgeLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

# Simplified Pydantic Models
class StudentProfile(BaseModel):
    """Simple student profile"""
    model_config = ConfigDict(use_enum_values=True)
    
    id: str = Field(..., min_length=1, description="Unique student identifier")
    name: str = Field(..., min_length=1, description="Student name")
    knowledge_level: KnowledgeLevel = Field(default=KnowledgeLevel.BEGINNER, description="Current knowledge level")
    interests: List[str] = Field(default_factory=lambda: ["programming"], description="Student interests")
    learning_goals: List[str] = Field(default_factory=lambda: ["understand MCP"], description="Learning objectives")
    
    @field_validator('interests', 'learning_goals')
    def validate_lists_not_empty_strings(cls, v):
        """Ensure list items are not empty strings"""
        return [item.strip() for item in v if item.strip()]

class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    role: Literal["student", "tutor"] = Field(..., description="Who sent the message")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the message was sent")

class ConversationContext(BaseModel):
    """Simple conversation context"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    student_id: str = Field(..., min_length=1, description="Student identifier")
    messages: List[ConversationMessage] = Field(default_factory=list, description="Conversation history")
    
    def add_message(self, role: Literal["student", "tutor"], content: str):
        """Add a message to conversation history"""
        message = ConversationMessage(role=role, content=content)
        self.messages.append(message)

class TeachingResponse(BaseModel):
    """Simple teaching response"""
    response: str = Field(..., min_length=1, description="The teaching response")
    tools_used: List[str] = Field(default_factory=list, description="MCP tools used")
    reasoning: List[str] = Field(default_factory=list, description="DSPy reasoning steps")

# Simple DSPy Signature
class MCPTutorSignature(dspy.Signature):
    """
    Simple DSPy signature for MCP educational tutoring.
    Uses ReAct pattern to decide which MCP tools to call.
    """
    
    student_query: str = dspy.InputField(desc="The student's question about MCP concepts")
    student_context: str = dspy.InputField(desc="Student's knowledge level, interests, and conversation history")
    
    educational_response: str = dspy.OutputField(
        desc="Educational response that addresses the student's query using information from MCP tools"
    )

class SimpleMCPTutor:
    """
    Simplified DSPy-powered tutor that uses MCP Educational Server tools
    
    Core functionality:
    1. Connect to MCP server
    2. Convert MCP tools to DSPy tools  
    3. Use DSPy ReAct to decide which tools to call
    4. Return educational response
    """
    
    def __init__(self, mcp_server_path: str = "mcp_server/main.py", llm_model: str = "gpt-4o-mini"):
        """Initialize the tutor with MCP server connection"""
        self.mcp_server_path = mcp_server_path
        self.conversations: Dict[str, ConversationContext] = {}
        self.student_profiles: Dict[str, StudentProfile] = {}
        
        # Configure DSPy
        self.configure_dspy(llm_model)
        
        # MCP server parameters
        self.server_params = StdioServerParameters(
            command="python",
            args=[self.mcp_server_path],
            env=dict(os.environ),  # Pass current environment including PATH
        )
        
        logger.info("✅ SimpleMCPTutor initialized")
    
    def configure_dspy(self, model: str):
        """Configure DSPy with the specified language model"""
        try:
            dspy.configure(lm=dspy.LM(f"openai/{model}"))
            logger.info(f"✅ DSPy configured with {model}")
        except Exception as e:
            logger.error(f"❌ Could not configure OpenAI model: {e}")
            raise e

    async def teach(self, student_id: str, query: str, student_profile: Optional[StudentProfile] = None) -> TeachingResponse:
        """
        Main teaching method using MCP tools through DSPy ReAct
        
        This follows the exact pattern from the DSPy MCP tutorial:
        1. Connect to MCP server
        2. Get available tools and convert to DSPy tools
        3. Create ReAct agent with tools
        4. Let DSPy decide which tools to call
        5. Return response
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
        
        try:
            # Step 1: Connect to MCP server (following tutorial pattern)
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize MCP connection
                    await session.initialize()
                    
                    # Step 2: Get available MCP tools
                    tools_response = await session.list_tools()
                    
                    # Step 3: Convert MCP tools to DSPy tools
                    dspy_tools = []
                    for tool in tools_response.tools:
                        dspy_tools.append(dspy.Tool.from_mcp_tool(session, tool))
                    logger.info(f"✅ Loaded {len(dspy_tools)} MCP tools")
                    
                    # Step 4: Create ReAct agent with MCP tools
                    react_agent = dspy.ReAct(MCPTutorSignature, tools=dspy_tools)
                    
                    # Step 5: Prepare context for the agent
                    student_context = self._prepare_context(profile, context)
                    logger.info(f"✅ Student context: {student_context}")
                    
                    # Step 6: Let DSPy ReAct decide which tools to call
                    try:
                        result = await react_agent.acall(
                            student_query=query,
                            student_context=student_context
                        )
                        self._log_beautiful_result(result)
                    except Exception as react_error:
                        logger.error(f"❌ DSPy ReAct error: {react_error}")
                        raise react_error

                    # Step 7: Extract tools used and reasoning from trajectory
                    tools_used, reasoning_steps = self._extract_trajectory_info(result)
                    
                    # Step 8: Update conversation
                    context.add_message("student", query)
                    context.add_message("tutor", result.educational_response)
                    
                    return TeachingResponse(
                        response=result.educational_response,
                        tools_used=tools_used,
                        reasoning=reasoning_steps
                    )
                    
        except Exception as e:
            logger.error(f"❌ Error in MCP teaching method: {e}")
            
            # Simple fallback
            return self._fallback_response(student_id, query)
    
    def _prepare_context(self, profile: StudentProfile, context: ConversationContext) -> str:
        """Prepare simple context string for DSPy"""
        recent_messages = context.messages[-3:] if len(context.messages) > 3 else context.messages
        
        context_info = {
            "knowledge_level": profile.knowledge_level,  # Already a string due to use_enum_values=True
            "interests": profile.interests,
            "goals": profile.learning_goals,
            "recent_conversation": [{"role": msg.role, "content": msg.content} for msg in recent_messages]
        }
        
        return json.dumps(context_info)
    
    def _extract_trajectory_info(self, result) -> tuple[List[str], List[str]]:
        """Extract tools used and reasoning from DSPy trajectory"""
        tools_used = []
        reasoning_steps = []
        
        if hasattr(result, 'trajectory') and result.trajectory:
            for key, value in result.trajectory.items():
                if key.startswith('tool_name_') and value != 'finish':
                    tools_used.append(value)
                elif key.startswith('thought_'):
                    reasoning_steps.append(value)
        
        return tools_used, reasoning_steps
    
    def _create_default_profile(self, student_id: str) -> StudentProfile:
        """Create a simple default student profile"""
        return StudentProfile(
            id=student_id,
            name=f"Student_{student_id}",
            knowledge_level=KnowledgeLevel.BEGINNER,
            interests=["programming"],
            learning_goals=["understand MCP concepts"]
        )
    
    def get_conversation(self, student_id: str) -> Optional[ConversationContext]:
        """Get conversation history for a student"""
        return self.conversations.get(student_id)

    def _fallback_response(self, student_id: str, query: str) -> TeachingResponse:
        """Provide a fallback response when MCP connection fails"""
        fallback_response = f"I'd be happy to help you learn about MCP! Could you tell me more about what specifically interests you?"
        
        context = self.conversations.get(student_id)
        if context:
            context.add_message("student", query)
            context.add_message("tutor", fallback_response)
        
        return TeachingResponse(
            response=fallback_response,
            tools_used=[],
            reasoning=["Fallback response due to MCP connection error"]
        )

    def _log_beautiful_result(self, result):
        """Log the DSPy result in a beautiful, readable format"""
        print("\n" + "="*80)
        print("🤖 DSPy ReAct Result")
        print("="*80)
        
        # Main response
        print(f"\n📝 Educational Response:")
        print(f"   {result.educational_response}")
        
        # Trajectory details if available
        if hasattr(result, 'trajectory') and result.trajectory:
            print(f"\n🧠 Reasoning Trajectory:")
            
            step_num = 0
            for key, value in result.trajectory.items():
                if key.startswith('thought_'):
                    step_num += 1
                    print(f"   💭 Step {step_num}: {value}")
                elif key.startswith('tool_name_') and value != 'finish':
                    print(f"   🔧 Tool Used: {value}")
                elif key.startswith('tool_args_'):
                    if isinstance(value, dict):
                        args_str = ', '.join([f"{k}={v}" for k, v in value.items()])
                        print(f"   ⚙️  Args: {args_str}")
                elif key.startswith('observation_'):
                    # Truncate long observations
                    obs = str(value)
                    if len(obs) > 200:
                        obs = obs[:200] + "..."
                    print(f"   👁️  Observation: {obs}")
        
        # Additional metadata
        if hasattr(result, 'reasoning'):
            print(f"\n🎯 Reasoning Summary: {result.reasoning}")
            
        print("="*80 + "\n")

async def main():
    """Simple demo of the MCP tutor"""
    print("🚀 Starting Simple MCP Tutor...")
    
    # Initialize the tutor
    tutor = SimpleMCPTutor(
        mcp_server_path="mcp_server/main.py",
        llm_model="gpt-4o"
    )
    
    # Create simple student profile
    student = StudentProfile(
        id="demo_student",
        name="Demo Student",
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        interests=["web development", "APIs"],
        learning_goals=["understand MCP", "build MCP server"]
    )
    
    # Demo conversation
    print("\n💬 Demo Conversation:")
    print("=" * 50)
    
    queries = [
        "What is MCP?",
        "How do I create MCP tools?",
        "Show me an example of an MCP server"
    ]
    
    for query in queries:
        print(f"\n Student: {query}")
        
        result = await tutor.teach("demo_student", query, student)
        
        print(f"🤖 Tutor: {result.response[:200]}...")
        if result.tools_used:
            print(f"🔧 Tools Used: {', '.join(result.tools_used)}")
        if result.reasoning:
            print(f"🧠 Reasoning: {result.reasoning[0]}")
        
        print("-" * 30)
    
    # Show conversation history
    conversation = tutor.get_conversation("demo_student")
    if conversation:
        print(f"\n📜 Conversation History: {len(conversation.messages)} messages")
    
    print("\n✨ Simple MCP Tutor Demo Complete!")

if __name__ == "__main__":
    asyncio.run(main()) 