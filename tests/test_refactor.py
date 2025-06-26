#!/usr/bin/env python3
"""
Test script to verify the refactored MCP server structure
"""

import asyncio
from mcp_server.main import MCPTutorServer

async def test_modular_structure():
    """Test that the refactored server components work correctly"""
    
    print("🧪 Testing refactored MCP server structure...")
    
    # Initialize server (without running it)
    server = MCPTutorServer()
    
    # Test tools handler
    print(f"✅ Tools handler initialized: {type(server.tools_handler).__name__}")
    tools_list = server.tools_handler.get_tools_list()
    print(f"✅ Found {len(tools_list)} tools:")
    for tool in tools_list:
        print(f"   - {tool.name}: {tool.description[:50]}...")
    
    # Test prompts handler
    print(f"✅ Prompts handler initialized: {type(server.prompts_handler).__name__}")
    prompts_list = server.prompts_handler.get_prompts_list()
    print(f"✅ Found {len(prompts_list)} prompts:")
    for prompt in prompts_list:
        print(f"   - {prompt.name}: {prompt.description[:50]}...")
    
    # Test ingester
    print(f"✅ Ingester initialized: {type(server.ingester).__name__}")
    print(f"✅ Document processor available: {type(server.ingester.processor).__name__}")
    
    print("\n🎉 All components successfully initialized!")
    print("\n📁 File structure breakdown:")
    print("   📄 mcp_server/main.py       - Server orchestration & handlers")
    print("   🔧 mcp_server/tools.py      - 4 MCP tools implementation")  
    print("   📝 mcp_server/prompts.py    - 6 educational prompts implementation")
    print("   ⚙️  mcp_server/content_processing.py - Repository ingestion & document processing")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_modular_structure())
    if result:
        print("\n✨ Refactoring verification completed successfully!")
    else:
        print("\n❌ Refactoring verification failed!")
        exit(1) 