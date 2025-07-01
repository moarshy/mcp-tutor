#!/usr/bin/env python3
"""
Simple MCP stdio client to list available tools and prompts from the MCP Educational Tutor Server.
"""

import asyncio
import sys
import os
import shutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_server_capabilities():
    """Connect to MCP server and list all available tools and prompts."""
    
    # Clear any existing cache for a clean test run
    if os.path.exists(".cache"):
        shutil.rmtree(".cache")
        print("Cleared .cache/ for a clean test run.")
        
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
                            
                            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                                schema = tool.inputSchema
                                if 'properties' in schema and schema['properties']:
                                    print(f"    Arguments:")
                                    for prop_name, prop_info in schema['properties'].items():
                                        is_required = prop_name in schema.get('required', [])
                                        prop_type = prop_info.get('type', 'unknown')
                                        prop_desc = prop_info.get('description', 'No description')
                                        required_text = " (required)" if is_required else ""
                                        print(f"      • {prop_name} ({prop_type}){required_text}: {prop_desc}")
                                else:
                                    print(f"    Arguments: None")
                            print()
                    else:
                        print("    No tools available")
                except Exception as e:
                    print(f"    Error listing tools: {e}")

                # --- Test Execution ---
                print("\n" + "=" * 60)
                print("RUNNING END-TO-END TESTS")
                print("=" * 60)

                # 1. List courses
                print("\n🧪 TEST 1: list_courses")
                print("-" * 40)
                try:
                    tool_result = await session.call_tool("list_courses", {})
                    if tool_result.content:
                        for content in tool_result.content:
                            if hasattr(content, 'text'):
                                print(f"Response:\n{content.text}")
                    else:
                        print("No content returned from list_courses")
                except Exception as e:
                    print(f"    Error calling list_courses: {e}")

                # 2. Try to start a course without being registered
                print("\n🧪 TEST 2: start_course (unregistered)")
                print("-" * 40)
                try:
                    tool_result = await session.call_tool("start_course", {"level": "beginner"})
                    if tool_result.content:
                        for content in tool_result.content:
                            if hasattr(content, 'text'):
                                print(f"Response: {content.text}")
                    else:
                        print("No content returned from start_course")
                except Exception as e:
                    print(f"    Error calling start_course: {e}")

                # 3. Register a new user
                print("\n🧪 TEST 3: register_user (new user)")
                print("-" * 40)
                try:
                    tool_result = await session.call_tool("register_user", {"email": "test.user@example.com"})
                    if tool_result.content:
                        for content in tool_result.content:
                            if hasattr(content, 'text'):
                                print(f"Response:\n{content.text}")
                    else:
                        print("No content returned from register_user")
                except Exception as e:
                    print(f"    Error calling register_user: {e}")

                # 4. Try to register again
                print("\n🧪 TEST 4: register_user (already registered)")
                print("-" * 40)
                try:
                    tool_result = await session.call_tool("register_user", {"email": "another.user@example.com"})
                    if tool_result.content:
                        for content in tool_result.content:
                            if hasattr(content, 'text'):
                                print(f"Response:\n{content.text}")
                    else:
                        print("No content returned from register_user")
                except Exception as e:
                    print(f"    Error calling register_user: {e}")

                # 5. Start a course after being registered
                print("\n🧪 TEST 5: start_course (registered)")
                print("-" * 40)
                try:
                    tool_result = await session.call_tool("start_course", {"level": "beginner"})
                    if tool_result.content:
                        for content in tool_result.content:
                            if hasattr(content, 'text'):
                                print(f"Response:\n{content.text}")
                    else:
                        print("No content returned from start_course")
                except Exception as e:
                    print(f"    Error calling start_course: {e}")

                # 6. Get the course status
                print("\n🧪 TEST 6: get_course_status")
                print("-" * 40)
                try:
                    tool_result = await session.call_tool("get_course_status", {})
                    if tool_result.content:
                        for content in tool_result.content:
                            if hasattr(content, 'text'):
                                print(f"Response:\n{content.text}")
                    else:
                        print("No content returned from get_course_status")
                except Exception as e:
                    print(f"    Error calling get_course_status: {e}")
                
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
    
    success = await test_server_capabilities()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 