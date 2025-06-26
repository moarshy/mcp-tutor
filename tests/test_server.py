#!/usr/bin/env python3
"""
Comprehensive test suite for MCP Educational Tutor Server
Tests tools, prompts, and server functionality
"""

import asyncio
import json
import logging
from typing import Dict, Any, List

import mcp.types as types
from mcp_server.main import MCPTutorServer

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerTester:
    """Comprehensive tester for MCP server functionality"""
    
    def __init__(self):
        self.server = MCPTutorServer()
        self.test_results: Dict[str, bool] = {}
        
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting MCP Educational Tutor Server Tests")
        print("=" * 60)
        
        # Test server initialization
        await self.test_server_initialization()
        
        # Test tools functionality
        await self.test_tools_functionality()
        
        # Test prompts functionality  
        await self.test_prompts_functionality()
        
        # Test content processing
        await self.test_content_processing()
        
        # Print results summary
        self.print_test_summary()
        
        return all(self.test_results.values())
    
    async def test_server_initialization(self):
        """Test server components initialize correctly"""
        print("\n📋 Testing Server Initialization")
        print("-" * 40)
        
        try:
            # Test component initialization
            assert self.server.tools_handler is not None
            assert self.server.prompts_handler is not None
            assert self.server.ingester is not None
            
            self.test_results["server_initialization"] = True
            print("✅ Server components initialized successfully")
            
        except Exception as e:
            self.test_results["server_initialization"] = False
            print(f"❌ Server initialization failed: {e}")
    
    async def test_tools_functionality(self):
        """Test all MCP tools"""
        print("\n🔧 Testing MCP Tools")
        print("-" * 40)
        
        # Test tools listing
        await self.test_list_tools()
        
        # Test individual tool calls (without content - faster for testing)
        await self.test_search_concepts_tool()
        await self.test_list_documents_tool()
        await self.test_get_document_tool()
        await self.test_get_code_example_tool()
    
    async def test_list_tools(self):
        """Test tools listing functionality"""
        try:
            tools_list = self.server.tools_handler.get_tools_list()
            
            # Verify we have expected tools
            expected_tools = {
                "search_mcp_concepts",
                "get_document_by_key", 
                "list_available_documents",
                "get_code_example"
            }
            
            actual_tools = {tool.name for tool in tools_list}
            
            assert expected_tools == actual_tools, f"Expected {expected_tools}, got {actual_tools}"
            assert len(tools_list) == 4
            
            # Verify tool structure
            for tool in tools_list:
                assert isinstance(tool, types.Tool)
                assert tool.name
                assert tool.description
                assert tool.inputSchema
                
            self.test_results["list_tools"] = True
            print(f"✅ Tools listing: Found {len(tools_list)} tools")
            
        except Exception as e:
            self.test_results["list_tools"] = False
            print(f"❌ Tools listing failed: {e}")
    
    async def test_search_concepts_tool(self):
        """Test search_mcp_concepts tool"""
        try:
            # Test with empty query (should handle gracefully)
            result = await self.server.tools_handler.handle_tool_call(
                "search_mcp_concepts",
                {"query": ""}
            )
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Error" in result[0].text  # Should return error for empty query
            
            self.test_results["search_concepts_tool"] = True
            print("✅ Search concepts tool: Handles empty query correctly")
            
        except Exception as e:
            self.test_results["search_concepts_tool"] = False
            print(f"❌ Search concepts tool failed: {e}")
    
    async def test_list_documents_tool(self):
        """Test list_available_documents tool"""
        try:
            result = await self.server.tools_handler.handle_tool_call(
                "list_available_documents",
                {"doc_type_filter": "all"}
            )
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            # Should either show documents or indicate none loaded
            assert result[0].text
            
            self.test_results["list_documents_tool"] = True
            print("✅ List documents tool: Returns proper response")
            
        except Exception as e:
            self.test_results["list_documents_tool"] = False
            print(f"❌ List documents tool failed: {e}")
    
    async def test_get_document_tool(self):
        """Test get_document_by_key tool"""
        try:
            # Test with non-existent key
            result = await self.server.tools_handler.handle_tool_call(
                "get_document_by_key",
                {"document_key": "nonexistent_key"}
            )
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "not found" in result[0].text.lower()
            
            self.test_results["get_document_tool"] = True
            print("✅ Get document tool: Handles missing documents correctly")
            
        except Exception as e:
            self.test_results["get_document_tool"] = False
            print(f"❌ Get document tool failed: {e}")
    
    async def test_get_code_example_tool(self):
        """Test get_code_example tool"""
        try:
            result = await self.server.tools_handler.handle_tool_call(
                "get_code_example",
                {"concept": "server", "language": "python"}
            )
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            # Should either show examples or indicate none found
            assert result[0].text
            
            self.test_results["get_code_example_tool"] = True
            print("✅ Get code example tool: Returns proper response")
            
        except Exception as e:
            self.test_results["get_code_example_tool"] = False
            print(f"❌ Get code example tool failed: {e}")
    
    async def test_prompts_functionality(self):
        """Test all MCP prompts"""
        print("\n📝 Testing MCP Prompts")
        print("-" * 40)
        
        # Test prompts listing
        await self.test_list_prompts()
        
        # Test individual prompt calls
        await self.test_explain_concept_prompt()
        await self.test_socratic_dialogue_prompt()
        await self.test_code_review_prompt()
        await self.test_troubleshooting_prompt()
        await self.test_project_architect_prompt()
        await self.test_learning_path_prompt()
    
    async def test_list_prompts(self):
        """Test prompts listing functionality"""
        try:
            prompts_list = self.server.prompts_handler.get_prompts_list()
            
            # Verify we have expected prompts
            expected_prompts = {
                "explain_mcp_concept",
                "mcp_socratic_dialogue",
                "mcp_code_review",
                "mcp_troubleshooting_guide", 
                "mcp_project_architect",
                "mcp_learning_path"
            }
            
            actual_prompts = {prompt.name for prompt in prompts_list}
            
            assert expected_prompts == actual_prompts, f"Expected {expected_prompts}, got {actual_prompts}"
            assert len(prompts_list) == 6
            
            # Verify prompt structure
            for prompt in prompts_list:
                assert isinstance(prompt, types.Prompt)
                assert prompt.name
                assert prompt.description
                assert prompt.arguments is not None
                
            self.test_results["list_prompts"] = True
            print(f"✅ Prompts listing: Found {len(prompts_list)} prompts")
            
        except Exception as e:
            self.test_results["list_prompts"] = False
            print(f"❌ Prompts listing failed: {e}")
    
    async def test_explain_concept_prompt(self):
        """Test explain_mcp_concept prompt"""
        try:
            result = await self.server.prompts_handler.handle_prompt_request(
                "explain_mcp_concept",
                {"concept": "tools"}
            )
            
            assert isinstance(result, types.GetPromptResult)
            assert result.messages
            assert len(result.messages) > 0
            
            # Verify message structure
            message = result.messages[0]
            assert isinstance(message, types.PromptMessage)
            assert message.role == "user"
            assert isinstance(message.content, types.TextContent)
            assert "tools" in message.content.text.lower()
            
            self.test_results["explain_concept_prompt"] = True
            print("✅ Explain concept prompt: Generates proper educational content")
            
        except Exception as e:
            self.test_results["explain_concept_prompt"] = False
            print(f"❌ Explain concept prompt failed: {e}")
    
    async def test_socratic_dialogue_prompt(self):
        """Test mcp_socratic_dialogue prompt"""
        try:
            result = await self.server.prompts_handler.handle_prompt_request(
                "mcp_socratic_dialogue",
                {"target_concept": "prompts"}
            )
            
            assert isinstance(result, types.GetPromptResult)
            assert result.messages
            assert len(result.messages) > 0
            
            message = result.messages[0]
            assert isinstance(message, types.PromptMessage)
            assert message.role == "user"
            assert isinstance(message.content, types.TextContent)
            assert "prompts" in message.content.text.lower()
            
            self.test_results["socratic_dialogue_prompt"] = True
            print("✅ Socratic dialogue prompt: Generates Socratic questioning framework")
            
        except Exception as e:
            self.test_results["socratic_dialogue_prompt"] = False
            print(f"❌ Socratic dialogue prompt failed: {e}")
    
    async def test_code_review_prompt(self):
        """Test mcp_code_review prompt"""
        try:
            result = await self.server.prompts_handler.handle_prompt_request(
                "mcp_code_review",
                {
                    "student_code": "def hello(): print('Hello')",
                    "implementation_goal": "test function"
                }
            )
            
            assert isinstance(result, types.GetPromptResult)
            assert result.messages
            
            message = result.messages[0]
            assert isinstance(message, types.PromptMessage)
            assert message.role == "user"
            assert isinstance(message.content, types.TextContent)
            assert "review" in message.content.text.lower()
            
            self.test_results["code_review_prompt"] = True
            print("✅ Code review prompt: Generates educational code feedback framework")
            
        except Exception as e:
            self.test_results["code_review_prompt"] = False
            print(f"❌ Code review prompt failed: {e}")
    
    async def test_troubleshooting_prompt(self):
        """Test mcp_troubleshooting_guide prompt"""
        try:
            result = await self.server.prompts_handler.handle_prompt_request(
                "mcp_troubleshooting_guide",
                {"error_description": "Server not responding"}
            )
            
            assert isinstance(result, types.GetPromptResult)
            assert result.messages
            
            message = result.messages[0]
            assert isinstance(message, types.PromptMessage)
            assert message.role == "user"
            assert isinstance(message.content, types.TextContent)
            assert "troubleshooting" in message.content.text.lower()
            
            self.test_results["troubleshooting_prompt"] = True
            print("✅ Troubleshooting prompt: Generates systematic debugging framework")
            
        except Exception as e:
            self.test_results["troubleshooting_prompt"] = False
            print(f"❌ Troubleshooting prompt failed: {e}")
    
    async def test_project_architect_prompt(self):
        """Test mcp_project_architect prompt"""
        try:
            result = await self.server.prompts_handler.handle_prompt_request(
                "mcp_project_architect",
                {"project_requirements": "Build a document search system"}
            )
            
            assert isinstance(result, types.GetPromptResult)
            assert result.messages
            
            message = result.messages[0]
            assert isinstance(message, types.PromptMessage)
            assert message.role == "user"
            assert isinstance(message.content, types.TextContent)
            assert "architect" in message.content.text.lower()
            
            self.test_results["project_architect_prompt"] = True
            print("✅ Project architect prompt: Generates architectural guidance framework")
            
        except Exception as e:
            self.test_results["project_architect_prompt"] = False
            print(f"❌ Project architect prompt failed: {e}")
    
    async def test_learning_path_prompt(self):
        """Test mcp_learning_path prompt"""
        try:
            result = await self.server.prompts_handler.handle_prompt_request(
                "mcp_learning_path",
                {"learning_goal": "Master MCP development"}
            )
            
            assert isinstance(result, types.GetPromptResult)
            assert result.messages
            
            message = result.messages[0]
            assert isinstance(message, types.PromptMessage)
            assert message.role == "user"
            assert isinstance(message.content, types.TextContent)
            assert "learning" in message.content.text.lower()
            
            self.test_results["learning_path_prompt"] = True
            print("✅ Learning path prompt: Generates personalized learning framework")
            
        except Exception as e:
            self.test_results["learning_path_prompt"] = False
            print(f"❌ Learning path prompt failed: {e}")
    
    async def test_content_processing(self):
        """Test content processing functionality"""
        print("\n⚙️  Testing Content Processing")
        print("-" * 40)
        
        try:
            # Test that document processor is initialized
            assert self.server.ingester.processor is not None
            
            # Test that prepared_docs is initialized (empty until content loaded)
            assert hasattr(self.server.ingester.processor, 'prepared_docs')
            assert isinstance(self.server.ingester.processor.prepared_docs, dict)
            
            self.test_results["content_processing"] = True
            print("✅ Content processing: Document processor ready")
            
        except Exception as e:
            self.test_results["content_processing"] = False
            print(f"❌ Content processing failed: {e}")
    
    def print_test_summary(self):
        """Print comprehensive test results summary"""
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        print(f"\n📈 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        print(f"\n🔧 Tools Tests:")
        tools_tests = ["list_tools", "search_concepts_tool", "list_documents_tool", 
                      "get_document_tool", "get_code_example_tool"]
        for test in tools_tests:
            status = "✅" if self.test_results.get(test, False) else "❌"
            print(f"   {status} {test}")
        
        print(f"\n📝 Prompts Tests:")
        prompt_tests = ["list_prompts", "explain_concept_prompt", "socratic_dialogue_prompt",
                       "code_review_prompt", "troubleshooting_prompt", "project_architect_prompt", 
                       "learning_path_prompt"]
        for test in prompt_tests:
            status = "✅" if self.test_results.get(test, False) else "❌"
            print(f"   {status} {test}")
        
        print(f"\n🏗️  Infrastructure Tests:")
        infra_tests = ["server_initialization", "content_processing"]
        for test in infra_tests:
            status = "✅" if self.test_results.get(test, False) else "❌"
            print(f"   {status} {test}")
        
        if passed == total:
            print(f"\n🎉 All tests passed! MCP Educational Tutor Server is working correctly.")
        else:
            failed = total - passed
            print(f"\n⚠️  {failed} test(s) failed. Check the details above.")
        
        print("\n" + "=" * 60)

async def main():
    """Main test runner"""
    tester = MCPServerTester()
    success = await tester.run_all_tests()
    
    if success:
        print("✨ Test suite completed successfully!")
        exit(0)
    else:
        print("❌ Some tests failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 