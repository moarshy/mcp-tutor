"""
MCP Prompts for Educational Tutor Server

Prompt definitions and handlers for educational interactions and guidance.
"""

import logging
from typing import Dict, List
from mcp.types import Prompt, PromptArgument, PromptMessage, Role, TextContent

logger = logging.getLogger(__name__)

# The introduction prompt is shown only when a user registers for the course.
INTRODUCTION_PROMPT = """
# Welcome to the Interactive Tutor!

This interactive guide will help you learn complex topics through a structured, step-by-step course.

## How This Course Works

- Each module is broken into multiple steps.
- I'll guide you through the content and examples.
- You can ask questions at any time.
- If you ever leave and come back, use the `start_course` tool to pick up where you left off.
- Use the `next_course_step` tool to move to the next step when you're ready.
- Use the `get_course_status` tool to check your progress.
- Use the `clear_course_history` tool to reset your progress and start over.

Let's get started with your first module!
"""

# This prompt wraps each module step, providing context and instructions to the AI model.
MODULE_PROMPT_TEMPLATE = """
You are an expert tutor helping the user through a structured course. Present the course content clearly using proper markdown formatting.

Please present the following course content exactly as it appears, preserving all markdown formatting (headers, lists, code blocks, etc.). After presenting the content, provide brief guidance and ask if they're ready to continue to the next step.

{content}

---

This completes the current step. When you're ready to continue to the next step, let me know and I'll advance you forward in the course!
"""

def get_module_prompt(content: str) -> str:
    """Wraps the step content in the module prompt template."""
    return MODULE_PROMPT_TEMPLATE.format(content=content)


def get_prompt_definitions() -> List[Prompt]:
    """Get all available prompt definitions"""
    return [
        Prompt(
            name="explain_concept",
            description="Explain a course concept in detail with examples",
            arguments=[
                PromptArgument(
                    name="concept",
                    description="The concept to explain",
                    required=True
                ),
                PromptArgument(
                    name="level",
                    description="Target audience level (beginner, intermediate, advanced)",
                    required=False
                ),
                PromptArgument(
                    name="context",
                    description="Additional context or specific focus area",
                    required=False
                )
            ]
        ),
        Prompt(
            name="create_assessment",
            description="Create quiz questions or exercises for a topic",
            arguments=[
                PromptArgument(
                    name="topic",
                    description="The topic to create assessment for",
                    required=True
                ),
                PromptArgument(
                    name="question_type",
                    description="Type of questions (multiple_choice, short_answer, practical)",
                    required=False
                ),
                PromptArgument(
                    name="difficulty",
                    description="Difficulty level (easy, medium, hard)",
                    required=False
                )
            ]
        ),
        Prompt(
            name="learning_path",
            description="Suggest a personalized learning path through the course content",
            arguments=[
                PromptArgument(
                    name="current_level",
                    description="Current knowledge level",
                    required=True
                ),
                PromptArgument(
                    name="goal",
                    description="Learning objective or goal",
                    required=True
                ),
                PromptArgument(
                    name="time_available",
                    description="Available time for learning (e.g., '2 weeks', '1 month')",
                    required=False
                )
            ]
        ),
        Prompt(
            name="review_content",
            description="Review and provide feedback on course content",
            arguments=[
                PromptArgument(
                    name="content",
                    description="Content to review",
                    required=True
                ),
                PromptArgument(
                    name="focus",
                    description="What aspect to focus on (clarity, accuracy, completeness)",
                    required=False
                )
            ]
        )
    ]


async def handle_prompt_request(name: str, arguments: Dict[str, str], course_processor=None) -> List[PromptMessage]:
    """Handle prompt requests for educational interactions"""
    
    try:
        if name == "explain_concept":
            return await _handle_explain_concept(arguments)
        elif name == "create_assessment":
            return await _handle_create_assessment(arguments)
        elif name == "learning_path":
            return await _handle_learning_path(arguments, course_processor)
        elif name == "review_content":
            return await _handle_review_content(arguments)
        else:
            error_text = f"Unknown prompt: {name}"
            return [PromptMessage(role=Role.user, content=TextContent(type="text", text=error_text))]
    
    except Exception as e:
        logger.error(f"Error handling prompt {name}: {e}")
        error_text = f"Error processing prompt: {str(e)}"
        return [PromptMessage(role=Role.user, content=TextContent(type="text", text=error_text))]


async def _handle_explain_concept(arguments: Dict[str, str]) -> List[PromptMessage]:
    """Handle explain_concept prompt"""
    concept = arguments.get("concept", "")
    level = arguments.get("level", "intermediate")
    context = arguments.get("context", "")
    
    prompt_text = f"""You are an expert educational tutor. Please explain the concept of "{concept}" in a clear, comprehensive way.

Target audience: {level} level learners
{f"Additional context: {context}" if context else ""}

Your explanation should:
1. Start with a simple, clear definition
2. Provide practical examples
3. Explain why this concept is important
4. Include common misconceptions to avoid
5. Suggest next steps for deeper learning

Make your explanation engaging and easy to understand."""

    return [PromptMessage(role=Role.user, content=TextContent(type="text", text=prompt_text))]


async def _handle_create_assessment(arguments: Dict[str, str]) -> List[PromptMessage]:
    """Handle create_assessment prompt"""
    topic = arguments.get("topic", "")
    question_type = arguments.get("question_type", "mixed")
    difficulty = arguments.get("difficulty", "medium")
    
    prompt_text = f"""Create educational assessment questions for the topic: "{topic}"

Requirements:
- Question type: {question_type}
- Difficulty level: {difficulty}
- Create 5-7 questions that test understanding
- Include answer keys with explanations
- Focus on practical application, not just memorization

Format your response with:
1. Question number and text
2. Answer options (if multiple choice)
3. Correct answer
4. Brief explanation of why the answer is correct

Make questions that encourage critical thinking and real-world application."""

    return [PromptMessage(role=Role.user, content=TextContent(type="text", text=prompt_text))]


async def _handle_learning_path(arguments: Dict[str, str], course_processor=None) -> List[PromptMessage]:
    """Handle learning_path prompt"""
    current_level = arguments.get("current_level", "")
    goal = arguments.get("goal", "")
    time_available = arguments.get("time_available", "")
    
    # Get available courses for context
    courses_info = ""
    if course_processor:
        courses = course_processor.list_courses()
        courses_info = f"Available courses: {', '.join([f'{level} ({title})' for level, title in courses.items()])}"
    
    prompt_text = f"""Create a personalized learning path based on the following:

Current Level: {current_level}
Learning Goal: {goal}
{f"Time Available: {time_available}" if time_available else ""}

{courses_info}

Please provide:
1. Assessment of current knowledge gaps
2. Recommended learning sequence
3. Specific modules/topics to focus on
4. Estimated time for each phase
5. Milestones and checkpoints
6. Resources and study strategies
7. How to measure progress

Make the path practical and achievable, with clear next steps."""

    return [PromptMessage(role=Role.user, content=TextContent(type="text", text=prompt_text))]


async def _handle_review_content(arguments: Dict[str, str]) -> List[PromptMessage]:
    """Handle review_content prompt"""
    content = arguments.get("content", "")
    focus = arguments.get("focus", "overall quality")
    
    prompt_text = f"""Please review the following educational content with a focus on {focus}:

Content to review:
{content}

Provide feedback on:
1. Clarity and readability
2. Accuracy of information
3. Completeness of coverage
4. Educational effectiveness
5. Suggestions for improvement
6. Missing elements or concepts
7. Overall assessment and rating

Be constructive and specific in your feedback, providing actionable recommendations."""

    return [PromptMessage(role=Role.user, content=TextContent(type="text", text=prompt_text))] 