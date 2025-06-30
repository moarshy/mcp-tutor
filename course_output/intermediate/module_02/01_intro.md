Welcome to **Module 2: Core MCP Capabilities: Context and Actions**!

In Module 1, we laid the groundwork by exploring the fundamental architecture of the Model Context Protocol (MCP), understanding how clients, servers, and LLMs communicate through a robust transport and protocol layer. With that foundational knowledge in place, we're now ready to dive into the heart of what makes MCP so powerful: the specific capabilities that MCP servers expose to clients and, by extension, to Large Language Models (LLMs).

This module will illuminate how MCP servers empower LLMs to understand their environment and interact with the real world. We will explore four critical capabilities:

*   **Resources**: Discover how servers provide essential data and context to LLMs, enabling them to access relevant information. You'll learn about the structure and purpose of Resource URIs and types.
*   **Tools**: Understand how MCP allows LLMs to perform real-world actions by invoking external functionalities. We'll cover the definition, discovery, and invocation of Tools.
*   **Prompts**: Learn about reusable interaction templates that streamline communication and ensure consistent LLM behavior. We'll examine their components and how clients utilize them.
*   **Sampling**: Explore how MCP facilitates the generation of LLM completions, providing control over the output process. You'll identify the key parameters involved in `sampling/createMessage` requests.

By the end of this module, you will have a comprehensive understanding of these core MCP capabilities, equipping you with the knowledge to build sophisticated LLM applications that can effectively leverage context and perform actions.