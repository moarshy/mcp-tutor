#!/usr/bin/env python3
"""
Simple MCP stdio client to list available tools and prompts from the MCP Educational Tutor Server.
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def list_server_capabilities():
    """Connect to MCP server and list all available tools and prompts."""
    
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.main"],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                print("=" * 60)
                print("MCP EDUCATIONAL TUTOR SERVER - CAPABILITIES")
                print("=" * 60)
                
                # List all available tools
                print("\n🛠️  AVAILABLE TOOLS:")
                print("-" * 40)
                
                try:
                    tools_result = await session.list_tools()
                    if tools_result.tools:
                        for i, tool in enumerate(tools_result.tools, 1):
                            print(f"{i:2d}. {tool.name}")
                            if tool.description:
                                print(f"    Description: {tool.description}")
                            
                            # Display tool arguments from inputSchema
                            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                                schema = tool.inputSchema
                                if 'properties' in schema and schema['properties']:
                                    print(f"    Arguments:")
                                    for prop_name, prop_info in schema['properties'].items():
                                        is_required = prop_name in schema.get('required', [])
                                        prop_type = prop_info.get('type', 'unknown')
                                        prop_desc = prop_info.get('description', 'No description')
                                        required_text = " (required)" if is_required else " (optional)"
                                        
                                        if 'enum' in prop_info:
                                            enum_values = ', '.join(prop_info['enum'])
                                            print(f"      • {prop_name} ({prop_type}){required_text}: {prop_desc}")
                                            print(f"        Allowed values: {enum_values}")
                                        else:
                                            print(f"      • {prop_name} ({prop_type}){required_text}: {prop_desc}")
                                else:
                                    print(f"    Arguments: None")
                            print()
                    else:
                        print("    No tools available")
                except Exception as e:
                    print(f"    Error listing tools: {e}")
                
                # # List all available prompts
                # print("\n💬 AVAILABLE PROMPTS:")
                # print("-" * 40)
                
                # try:
                #     prompts_result = await session.list_prompts()
                #     if prompts_result.prompts:
                #         for i, prompt in enumerate(prompts_result.prompts, 1):
                #             print(f"{i:2d}. {prompt.name}")
                #             if prompt.description:
                #                 print(f"    Description: {prompt.description}")
                #             if hasattr(prompt, 'arguments') and prompt.arguments:
                #                 print(f"    Arguments:")
                #                 for arg in prompt.arguments:
                #                     is_required = getattr(arg, 'required', False)
                #                     required_text = " (required)" if is_required else " (optional)"
                #                     arg_desc = getattr(arg, 'description', 'No description')
                #                     print(f"      • {arg.name}{required_text}: {arg_desc}")
                #             else:
                #                 print(f"    Arguments: None")
                #             print()
                #     else:
                #         print("    No prompts available")
                # except Exception as e:
                #     print(f"    Error listing prompts: {e}")
                
                # Test the list_courses tool
                print("\n📚 TESTING LIST_COURSES TOOL:")
                print("-" * 40)
                
                try:
                    # Call the list_courses tool
                    tool_result = await session.call_tool("list_courses", {})
                    
                    if tool_result.content:
                        for content in tool_result.content:
                            if hasattr(content, 'text'):
                                print(content.text)
                            else:
                                print(str(content))
                    else:
                        print("No content returned from list_courses")
                        
                except Exception as e:
                    print(f"    Error calling list_courses: {e}")
                
                # Test the get_course_outline tool
                print("\n📋 TESTING GET_COURSE_OUTLINE TOOL:")
                print("-" * 40)
                print("Getting outline for 'beginner' course...")
                print()
                
                try:
                    # Call the get_course_outline tool with beginner level
                    outline_result = await session.call_tool("get_course_outline", {"level": "beginner"})
                    
                    if outline_result.content:
                        for content in outline_result.content:
                            if hasattr(content, 'text'):
                                print(content.text)
                            else:
                                print(str(content))
                    else:
                        print("No content returned from get_course_outline")
                        
                except Exception as e:
                    print(f"    Error calling get_course_outline: {e}")
                
                # Test the get_step_content tool for each step
                print("\n📖 TESTING GET_STEP_CONTENT TOOL (All Steps):")
                print("-" * 40)
                print("Getting each step for 'beginner' course, 'module_01'...")
                print()
                
                step_types = ["intro", "main", "conclusion", "assessments", "summary"]
                step_emojis = {"intro": "👋", "main": "📚", "conclusion": "🎯", "assessments": "✅", "summary": "📝"}
                
                for step_type in step_types:
                    print(f"{step_emojis.get(step_type, '📄')} Step: {step_type.upper()}")
                    print("=" * 30)
                    
                    try:
                        # Call the get_step_content tool for each step
                        step_result = await session.call_tool("get_step_content", {
                            "level": "beginner",
                            "module_id": "module_01",
                            "step_type": step_type
                        })
                        
                        if step_result.content:
                            for content in step_result.content:
                                if hasattr(content, 'text'):
                                    # Truncate long content for display
                                    text = content.text
                                    # if len(text) > 800:
                                    #     text = text[:800] + "\n\n... [Content truncated for display] ..."
                                    print(text)
                                else:
                                    print(str(content))
                        else:
                            print(f"No content returned for {step_type} step")
                            
                    except Exception as e:
                        print(f"    Error calling get_step_content for {step_type}: {e}")
                    
                    print("\n" + "-" * 50 + "\n")
                
                # Test the search_course_content tool
                print("\n🔍 TESTING SEARCH_COURSE_CONTENT TOOL:")
                print("-" * 40)
                
                # Test search without level filter
                print("🔎 Searching for 'protocol' across all courses...")
                print()
                
                try:
                    search_result = await session.call_tool("search_course_content", {
                        "query": "protocol"
                    })
                    
                    if search_result.content:
                        for content in search_result.content:
                            if hasattr(content, 'text'):
                                text = content.text
                                # Truncate very long search results
                                if len(text) > 1200:
                                    text = text[:1200] + "\n\n... [Search results truncated for display] ..."
                                print(text)
                            else:
                                print(str(content))
                    else:
                        print("No search results found")
                        
                except Exception as e:
                    print(f"    Error calling search_course_content: {e}")
                
                print("\n" + "-" * 50 + "\n")
                
                # Test search with level filter
                print("🔎 Searching for 'MCP' in 'beginner' course only...")
                print()
                
                try:
                    search_result_filtered = await session.call_tool("search_course_content", {
                        "query": "MCP",
                        "level": "beginner"
                    })
                    
                    if search_result_filtered.content:
                        for content in search_result_filtered.content:
                            if hasattr(content, 'text'):
                                text = content.text
                                # Truncate very long search results
                                if len(text) > 1200:
                                    text = text[:1200] + "\n\n... [Search results truncated for display] ..."
                                print(text)
                            else:
                                print(str(content))
                    else:
                        print("No search results found")
                        
                except Exception as e:
                    print(f"    Error calling search_course_content with level filter: {e}")
                
                print("\n" + "=" * 60)
                print("CONNECTION SUCCESSFUL ✅")
                print("=" * 60)
                
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print("\nMake sure the MCP server is properly configured and dependencies are installed.")
        return False


async def main():
    """Main entry point."""
    print("Connecting to MCP Educational Tutor Server...")
    print("Server command: python -m mcp_server.main")
    print()
    
    success = await list_server_capabilities()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 