"""
MCP Prompts implementation for educational tutoring.
Contains all user-controlled prompts for structured teaching approaches.
"""

import logging
from typing import Any, Dict, List, Optional

import mcp.types as types

logger = logging.getLogger(__name__)


class MCPPrompts:
    """MCP Prompts handler for educational content delivery"""
    
    def __init__(self, tools_handler):
        self.tools = tools_handler
    
    def get_prompts_list(self) -> List[types.Prompt]:
        """Return list of available MCP prompts"""
        return [
            types.Prompt(
                name="explain_mcp_concept",
                description="Explain an MCP concept with examples and analogies tailored to student background",
                arguments=[
                    types.PromptArgument(
                        name="concept",
                        description="MCP concept to explain (e.g., 'tools', 'prompts', 'resources', 'server implementation')",
                        required=True
                    ),
                    types.PromptArgument(
                        name="student_background",
                        description="Student's programming background (beginner, intermediate, experienced)",
                        required=False
                    ),
                    types.PromptArgument(
                        name="explanation_style",
                        description="Preferred explanation style (conceptual, practical, example-driven)",
                        required=False
                    ),
                    types.PromptArgument(
                        name="analogy_domain",
                        description="Domain for analogies (web APIs, databases, operating systems, REST APIs)",
                        required=False
                    )
                ]
            ),
            
            types.Prompt(
                name="mcp_socratic_dialogue",
                description="Guide student to discover MCP concepts through Socratic questioning",
                arguments=[
                    types.PromptArgument(
                        name="target_concept",
                        description="MCP concept student should discover",
                        required=True
                    ),
                    types.PromptArgument(
                        name="student_current_understanding",
                        description="What student currently thinks about the concept",
                        required=False
                    ),
                    types.PromptArgument(
                        name="misconceptions",
                        description="Common misconceptions to address",
                        required=False
                    )
                ]
            ),
            
            types.Prompt(
                name="mcp_code_review",
                description="Provide constructive feedback on student's MCP implementation",
                arguments=[
                    types.PromptArgument(
                        name="student_code",
                        description="Student's MCP implementation code",
                        required=True
                    ),
                    types.PromptArgument(
                        name="implementation_goal",
                        description="What the student was trying to accomplish",
                        required=True
                    ),
                    types.PromptArgument(
                        name="focus_areas",
                        description="Specific aspects to focus feedback on (protocol compliance, best practices, security, etc.)",
                        required=False
                    )
                ]
            ),
            
            types.Prompt(
                name="mcp_troubleshooting_guide",
                description="Help student debug MCP implementation issues systematically",
                arguments=[
                    types.PromptArgument(
                        name="error_description",
                        description="Description of the problem student is facing",
                        required=True
                    ),
                    types.PromptArgument(
                        name="code_context",
                        description="Relevant code where error occurs",
                        required=False
                    ),
                    types.PromptArgument(
                        name="attempted_solutions",
                        description="What student has already tried",
                        required=False
                    )
                ]
            ),
            
            types.Prompt(
                name="mcp_project_architect",
                description="Guide student through designing an MCP-based solution",
                arguments=[
                    types.PromptArgument(
                        name="project_requirements",
                        description="What the student wants to build",
                        required=True
                    ),
                    types.PromptArgument(
                        name="constraints",
                        description="Technical or business constraints",
                        required=False
                    ),
                    types.PromptArgument(
                        name="student_experience_level",
                        description="Student's experience with MCP and related technologies",
                        required=False
                    )
                ]
            ),
            
            types.Prompt(
                name="mcp_learning_path",
                description="Create a personalized learning path for mastering MCP concepts",
                arguments=[
                    types.PromptArgument(
                        name="learning_goal",
                        description="What the student wants to achieve (e.g., 'build an MCP server', 'understand MCP architecture')",
                        required=True
                    ),
                    types.PromptArgument(
                        name="current_knowledge",
                        description="Student's current understanding of MCP and related technologies",
                        required=False
                    ),
                    types.PromptArgument(
                        name="time_commitment",
                        description="Available time for learning (hours per week)",
                        required=False
                    ),
                    types.PromptArgument(
                        name="preferred_learning_style",
                        description="How student learns best (hands-on, reading, video, projects)",
                        required=False
                    )
                ]
            )
        ]
    
    async def handle_prompt_request(self, name: str, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Handle prompt requests and route to appropriate methods"""
        
        if name == "explain_mcp_concept":
            return await self._get_explain_concept_prompt(arguments)
        elif name == "mcp_socratic_dialogue":
            return await self._get_socratic_dialogue_prompt(arguments)
        elif name == "mcp_code_review":
            return await self._get_code_review_prompt(arguments)
        elif name == "mcp_troubleshooting_guide":
            return await self._get_troubleshooting_prompt(arguments)
        elif name == "mcp_project_architect":
            return await self._get_project_architect_prompt(arguments)
        elif name == "mcp_learning_path":
            return await self._get_learning_path_prompt(arguments)
        else:
            raise ValueError(f"Unknown prompt: {name}")

    async def _get_explain_concept_prompt(self, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Generate structured prompt for explaining MCP concepts"""
        concept = arguments.get("concept", "")
        background = arguments.get("student_background", "intermediate")
        style = arguments.get("explanation_style", "practical")
        analogy_domain = arguments.get("analogy_domain", "web APIs")
        
        # Use tools to get relevant documentation
        search_results = await self.tools._search_concepts(concept, "any")
        context_content = ""
        if search_results and search_results[0].text:
            # Extract key information from search results
            content = search_results[0].text
            if len(content) > 2000:
                content = content[:2000] + "..."
            context_content = f"\n\nRelevant MCP documentation:\n{content}"
        
        system_prompt = f"""You are an expert MCP tutor with deep knowledge of the Model Context Protocol. You have access to the official MCP documentation and examples.

Your task: Explain '{concept}' to a {background} developer using a {style} approach.

Key principles for MCP education:
1. **Start with WHY**: Explain the problem MCP solves before diving into how
2. **Use analogies**: Draw comparisons to {analogy_domain} to make concepts concrete
3. **Include practical examples**: Always show working code when relevant
4. **Connect to ecosystem**: Explain how this concept fits into the broader MCP architecture
5. **Address misconceptions**: Anticipate and clarify common misunderstandings

Teaching approach based on style:
- **conceptual**: Focus on mental models and architectural understanding
- **practical**: Emphasize implementation details and step-by-step processes  
- **example-driven**: Use extensive code samples and real-world scenarios

Structure your explanation:
1. **Problem/Need**: What problem does {concept} solve?
2. **Core Concept**: What is {concept} in simple terms?
3. **How it Works**: Technical details appropriate for {background} level
4. **Practical Example**: Real code or implementation
5. **Common Gotchas**: Things students often struggle with
6. **Next Steps**: What to learn after mastering this concept

Always end with: "What questions do you have about {concept}?" to encourage interaction.{context_content}"""

        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"{system_prompt}\n\nPlease explain {concept} in MCP. I want to understand it clearly."
                    )
                )
            ]
        )

    async def _get_socratic_dialogue_prompt(self, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Generate Socratic questioning prompt for concept discovery"""
        target_concept = arguments.get("target_concept", "")
        current_understanding = arguments.get("student_current_understanding", "")
        misconceptions = arguments.get("misconceptions", "")
        
        system_prompt = f"""You are a Socratic MCP tutor. Guide the student to discover '{target_concept}' through thoughtful questioning rather than direct explanation.

Current student understanding: {current_understanding}
Known misconceptions to address: {misconceptions}

Socratic method principles for MCP concepts:
1. **Start with their assumptions** - Ask what they think {target_concept} does
2. **Probe deeper** - "Why do you think that?" "What would happen if...?"
3. **Reveal contradictions** - Help them find gaps in their reasoning
4. **Guide discovery** - Lead them to insights through their own thinking
5. **Test understanding** - Use hypothetical scenarios to verify comprehension

Question patterns to use:
- **Clarification**: "What do you mean when you say...?"
- **Evidence**: "What makes you think that?"
- **Perspective**: "How might this work differently from [alternative]?"
- **Implications**: "What would happen if we didn't have this feature?"
- **Scenarios**: "Can you think of a case where this would be useful?"

MCP-specific questioning strategies:
- Compare to familiar concepts (HTTP, APIs, function calls)
- Use concrete examples from the documentation
- Focus on the WHY behind MCP design decisions
- Help them understand the problem MCP solves

Never give direct answers. Always respond with questions that lead to insight.
When they discover something correct, acknowledge it and build on their understanding.
Guide them to understand {target_concept} as part of MCP's overall architecture."""

        user_message = f"I want to understand {target_concept} in MCP. Can you help me figure it out?"
        if current_understanding:
            user_message += f" I think {current_understanding}"

        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text", 
                        text=f"{system_prompt}\n\n{user_message}"
                    )
                )
            ]
        )

    async def _get_code_review_prompt(self, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Generate structured code review prompt for MCP implementations"""
        student_code = arguments.get("student_code", "")
        implementation_goal = arguments.get("implementation_goal", "")
        focus_areas = arguments.get("focus_areas", "general best practices")
        
        # Get relevant code examples for comparison
        code_examples = await self.tools._get_code_example("server", "any")
        example_context = ""
        if code_examples and code_examples[0].text:
            content = code_examples[0].text
            if len(content) > 1500:
                content = content[:1500] + "..."
            example_context = f"\n\nFor reference, here's a working MCP example:\n{content}"

        system_prompt = f"""You are an expert MCP code reviewer. Provide constructive, educational feedback on this student's implementation.

Implementation goal: {implementation_goal}
Focus areas: {focus_areas}

Review criteria for MCP code:
1. **Protocol Compliance**: Does it follow MCP specifications correctly?
   - Proper JSON-RPC message structure
   - Correct tool/prompt/resource schemas
   - Appropriate error handling

2. **Schema Design**: Are input/output schemas well-defined?
   - Clear, descriptive property names
   - Appropriate data types and constraints
   - Required vs optional fields properly marked

3. **Error Handling**: How does it handle errors and edge cases?
   - Graceful failure modes
   - Informative error messages
   - Proper exception propagation

4. **Security**: Are there security considerations?
   - Input validation and sanitization
   - Safe file operations
   - Appropriate permission checks

5. **Best Practices**: Does it follow MCP development patterns?
   - Clear separation of concerns
   - Proper async/await usage
   - Good naming conventions

6. **Code Quality**: Is the code maintainable and readable?
   - Clear function/variable names
   - Appropriate comments
   - Logical structure

Review format:
1. **What's Working Well**: Acknowledge good practices
2. **Areas for Improvement**: Specific issues with explanations
3. **Security Concerns**: Any potential vulnerabilities
4. **Suggestions**: Concrete improvements with code examples
5. **Learning Resources**: Relevant documentation or examples

Be encouraging and educational. Focus on helping them understand WHY certain patterns are better, not just WHAT to change.{example_context}"""

        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"{system_prompt}\n\nPlease review my MCP implementation. My goal was: {implementation_goal}\n\nHere's my code:\n\n```\n{student_code}\n```"
                    )
                )
            ]
        )

    async def _get_troubleshooting_prompt(self, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Generate systematic troubleshooting prompt for MCP issues"""
        error_description = arguments.get("error_description", "")
        code_context = arguments.get("code_context", "")
        attempted_solutions = arguments.get("attempted_solutions", "")
        
        system_prompt = f"""You are an expert MCP troubleshooting guide. Help the student debug their issue systematically using proven debugging methodologies.

Problem description: {error_description}
Code context: {code_context}
Already attempted: {attempted_solutions}

MCP Debugging Framework:
1. **Understand the Problem**
   - What exactly is happening vs what should happen?
   - When does the error occur (startup, tool call, specific conditions)?
   - Are there error messages or logs?

2. **Check the Basics**
   - MCP protocol compliance (JSON-RPC format)
   - Schema validation (required fields, data types)
   - Connection and transport issues
   - Environment and dependencies

3. **Isolate the Issue**
   - Can you reproduce it consistently?
   - Does it happen with minimal code?
   - Is it client-side, server-side, or transport-related?

4. **Common MCP Issues & Solutions**
   - **Schema mismatches**: Check inputSchema vs actual arguments
   - **Async/await problems**: Ensure proper async handling
   - **Transport errors**: Verify stdio setup and message framing
   - **Tool registration**: Confirm tools are properly registered
   - **Import/dependency issues**: Check MCP library versions

5. **Systematic Investigation**
   - Add logging at key points
   - Test with minimal examples
   - Compare with working code
   - Check MCP specification compliance

6. **Prevention Strategies**
   - Proper error handling patterns
   - Input validation best practices
   - Testing approaches for MCP code

Approach:
1. Ask clarifying questions to understand the exact issue
2. Suggest specific debugging steps
3. Provide code examples for common fixes
4. Help them understand the root cause, not just the symptoms
5. Share prevention strategies for future development

Be patient and methodical. Help them learn debugging skills, not just solve the immediate problem."""

        user_message = f"I'm having trouble with my MCP implementation. {error_description}"
        if code_context:
            user_message += f"\n\nRelevant code:\n```\n{code_context}\n```"
        if attempted_solutions:
            user_message += f"\n\nI've already tried: {attempted_solutions}"

        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text", 
                        text=f"{system_prompt}\n\n{user_message}"
                    )
                )
            ]
        )

    async def _get_project_architect_prompt(self, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Generate architectural guidance prompt for MCP projects"""
        project_requirements = arguments.get("project_requirements", "")
        constraints = arguments.get("constraints", "")
        experience_level = arguments.get("student_experience_level", "intermediate")
        
        system_prompt = f"""You are an expert MCP solution architect. Guide the student through designing an MCP-based solution from requirements to implementation plan.

Project requirements: {project_requirements}
Constraints: {constraints}
Student experience: {experience_level}

MCP Architecture Design Process:
1. **Requirements Analysis**
   - What capabilities does the system need?
   - Who are the users (humans, agents, other systems)?
   - What data or operations need to be exposed?

2. **MCP Component Design**
   - **Tools**: What operations should be model-controlled?
   - **Prompts**: What user-controlled interactions are needed?
   - **Resources**: What content/data needs to be accessible?
   - **Server vs Client**: Which components go where?

3. **System Architecture**
   - How many MCP servers/clients are needed?
   - What's the communication topology?
   - How does data flow through the system?
   - Integration with existing systems?

4. **Technical Decisions**
   - Programming language and framework choices
   - Data storage and persistence needs
   - Authentication and security requirements
   - Scalability and performance considerations

5. **Implementation Strategy**
   - Which components to build first (MVP approach)
   - How to structure the codebase
   - Testing and validation approach
   - Deployment and operational concerns

Design principles for {experience_level} developers:
- Start simple, add complexity gradually
- Use established patterns and examples
- Focus on clear interfaces and schemas
- Plan for error handling and edge cases
- Consider the user experience (both human and AI)

Guidance approach:
1. Ask clarifying questions about requirements
2. Suggest MCP-specific architectural patterns
3. Provide concrete implementation recommendations
4. Share relevant code examples and patterns
5. Help prioritize features for iterative development
6. Discuss trade-offs and alternatives

Focus on teaching sound architectural thinking, not just solving the immediate design problem."""

        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"{system_prompt}\n\nI want to build an MCP-based solution. Here's what I need: {project_requirements}"
                    )
                )
            ]
        )

    async def _get_learning_path_prompt(self, arguments: Dict[str, Any]) -> types.GetPromptResult:
        """Generate personalized learning path for MCP mastery"""
        learning_goal = arguments.get("learning_goal", "")
        current_knowledge = arguments.get("current_knowledge", "")
        time_commitment = arguments.get("time_commitment", "")
        learning_style = arguments.get("preferred_learning_style", "hands-on")
        
        system_prompt = f"""You are an expert MCP learning advisor. Create a personalized, structured learning path to help the student achieve their MCP goals.

Learning goal: {learning_goal}
Current knowledge: {current_knowledge}
Time commitment: {time_commitment}
Learning style: {learning_style}

MCP Learning Framework:
1. **Foundation Level** (Understanding the Why)
   - What problems does MCP solve?
   - How does it compare to other protocols?
   - Core concepts: tools, prompts, resources, transport

2. **Architecture Level** (Understanding the How)
   - MCP protocol structure and JSON-RPC
   - Client-server communication patterns
   - Schema design and validation

3. **Implementation Level** (Building Things)
   - Setting up MCP servers and clients
   - Implementing tools, prompts, and resources
   - Error handling and best practices

4. **Advanced Level** (Mastery and Optimization)
   - Complex architectures and patterns
   - Security and performance considerations
   - Integration with existing systems

Learning path customization for {learning_style} learners:
- **hands-on**: Emphasize projects, coding exercises, and experiments
- **reading**: Focus on documentation, articles, and code analysis
- **video**: Suggest video tutorials and walkthroughs
- **projects**: Build progressively complex real-world applications

Path structure:
1. **Assessment**: Evaluate current knowledge gaps
2. **Milestones**: Define clear learning objectives
3. **Resources**: Specific documentation, examples, and exercises
4. **Projects**: Practical applications to reinforce learning
5. **Timeline**: Realistic progression based on time commitment
6. **Checkpoints**: Ways to validate understanding

Create a learning path that:
- Builds systematically from basics to advanced
- Includes hands-on practice opportunities
- Provides clear success criteria
- Adapts to their experience level and goals
- Includes relevant MCP documentation and examples"""

        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"{system_prompt}\n\nI want to learn MCP to achieve this goal: {learning_goal}. Can you help me create a learning plan?"
                    )
                )
            ]
        ) 