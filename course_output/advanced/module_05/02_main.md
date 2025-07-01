# Building Model Context Protocol (MCP) Clients

This module provides a comprehensive guide for developers to build their own LLM-powered chatbot clients that can seamlessly integrate with Model Context Protocol (MCP) servers. It covers the essential steps from setting up your development environment and securely configuring API keys to implementing the fundamental code structure for managing connections, processing user queries, and handling complex interactions involving tool calls and LLM completions.

## Understanding MCP Client Architecture

In the Model Context Protocol (MCP) client-server architecture, **Clients** are applications that maintain 1:1 connections with **Servers**, typically operating within a **Host** application (like an IDE or desktop app). The client's primary role is to facilitate communication between the user's LLM application and the MCP server, which provides context, tools, and prompts.

Clients and servers communicate over a **Transport Layer** using **JSON-RPC 2.0** messages. These messages can be:

*   **Requests**: Expect a response from the other side.
*   **Results**: Successful responses to requests.
*   **Errors**: Indicate a failed request.
*   **Notifications**: One-way messages that do not expect a response.

## Setting Up Your Development Environment

Before you begin building your MCP client, ensure your system meets the necessary requirements and is properly configured. The setup process involves creating a project directory, initializing a project, and installing required dependencies.

### System Requirements

Generally, you will need:

*   A Mac or Windows computer.
*   The latest stable version of your chosen programming language's runtime (e.g., Python, Node.js 17+, Java 17+, .NET 8.0+).
*   The corresponding package manager (e.g., `uv` or `pip` for Python, `npm` for Node.js, `Maven` or `Gradle` for Java/Kotlin, `dotnet` for C#).

### Project Initialization and Dependencies

1.  **Create Project Directory**: Start by creating a new directory for your client project.
    *   `mkdir mcp-client` (or `md mcp-client` on Windows)
    *   `cd mcp-client`

2.  **Initialize Project**: Use your language's package manager to initialize a new project.
    *   **Python**: `uv init mcp-client`
    *   **Node.js**: `npm init -y`
    *   **Java/Kotlin**: `gradle init` (select Application, Kotlin/Java, Java 17) or use IntelliJ IDEA project wizard.
    *   **C#**: `dotnet new console -n QuickstartClient`

3.  **Install Dependencies**: Install the MCP SDK, an LLM SDK (e.g., Anthropic), and a dotenv library for environment variable management.
    *   **Python**: `uv add mcp anthropic python-dotenv`
    *   **Node.js**: `npm install @anthropic-ai/sdk @modelcontextprotocol/sdk dotenv` (and `npm install -D @types/node typescript` for TypeScript)
    *   **Java/Kotlin**: Add `spring-ai-starter-mcp-client`, `spring-ai-starter-model-anthropic` (for Spring AI) or `io.modelcontextprotocol:kotlin-sdk`, `com.anthropic:anthropic-java` (for Kotlin SDK) to your `build.gradle` or `pom.xml`.
    *   **C#**: `dotnet add package ModelContextProtocol --prerelease`, `dotnet add package Anthropic.SDK`, `dotnet add package Microsoft.Extensions.Hosting`

4.  **Configure Build (TypeScript/Java/Kotlin)**:
    *   **TypeScript**: Create `tsconfig.json` and update `package.json` scripts for `build` (e.g., `tsc`) and `start`.
    *   **Java/Kotlin**: Ensure `build.gradle` or `pom.xml` is correctly configured for dependencies and potentially for building a runnable JAR (e.g., using `shadow` plugin for Kotlin).

## Setting Up Your API Key Securely

To interact with LLMs like Anthropic's Claude, you'll need an API key. It's crucial to keep this key secure and avoid hardcoding it directly into your source code.

1.  **Obtain API Key**: Get your Anthropic API key from the [Anthropic Console](https://console.anthropic.com/settings/keys).

2.  **Store Key**: Use environment variables or a `.env` file.
    *   **Python/Node.js**: Create a `.env` file in your project root and add `ANTHROPIC_API_KEY=<your key here>`. Libraries like `python-dotenv` or `dotenv` will load this automatically.
    *   **Java/Kotlin**: Set the API key as an environment variable (e.g., `export ANTHROPIC_API_KEY='your-anthropic-api-key-here'`). For Spring AI, you might configure it in `application.yml` referencing the environment variable.
    *   **C#**: Use .NET User Secrets: `dotnet user-secrets init` then `dotnet user-secrets set "ANTHROPIC_API_KEY" "<your key here>"`. This stores the key outside your project directory.

3.  **Add to `.gitignore`**: Always add `.env` to your `.gitignore` file to prevent accidentally committing your sensitive keys to version control.
    *   `echo ".env" >> .gitignore`

## Creating the Client: Basic Structure and Server Connection

Your MCP client will typically be structured as a class that manages the connection to the MCP server and handles interactions with the LLM.

### Basic Client Structure

Initialize your client class with instances of your LLM client (e.g., `Anthropic`) and the MCP `Client` (or `ClientSession` in Python). It's good practice to use an asynchronous context manager or similar mechanism for proper resource cleanup.

```python
# Python example (simplified)
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
    # methods will go here
```

### Server Connection Management

The client needs to establish a connection with the MCP server. MCP primarily uses **Stdio Transport** for local communication, which involves launching the server as a child process and communicating via its standard input/output streams.

1.  **Determine Server Command**: The client needs to know how to execute the server script. This typically involves checking the script's file extension (`.py`, `.js`, `.jar`, `.csproj`) to determine the correct command (`python`, `node`, `java -jar`, `dotnet run`).

2.  **Initialize Stdio Transport**: Create an instance of `StdioClientTransport` (or equivalent) providing the command and arguments for the server script.

3.  **Connect Client Session**: Connect your MCP client instance to the transport. For Python, this involves creating a `ClientSession` with the input/output streams from the transport. For other SDKs, the `Client` object directly connects to the transport.

4.  **Initialize Session**: After connecting, send an `initialize` request to the server. This handshake establishes the protocol version and capabilities.

5.  **List Tools**: Once initialized, you can request the list of available tools from the server using `list_tools()` (or `listTools()` in other SDKs). This is crucial for informing the LLM about the functionalities it can leverage.

```python
# Python example (simplified connect_to_server method)
async def connect_to_server(self, server_script_path: str):
    is_python = server_script_path.endswith('.py')
    command = "python" if is_python else "node"
    server_params = StdioServerParameters(command=command, args=[server_script_path])

    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
    self.stdio, self.write = stdio_transport
    self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

    await self.session.initialize()
    response = await self.session.list_tools()
    print("Connected to server with tools:", [tool.name for tool in response.tools])
```

## Query Processing Logic and Tool Call Handling

This is the core of your chatbot client, where user queries are processed, sent to the LLM, and tool calls are managed.

1.  **Maintain Conversation Context**: Keep a list of messages (user queries and LLM responses) to provide conversational history to the LLM.

2.  **Retrieve Available Tools**: Before sending a query to the LLM, fetch the current list of tools from the MCP server. Format these tools according to the LLM's expected tool schema.

3.  **Initial LLM Call**: Send the user's query and the available tools to your chosen LLM (e.g., Claude's `messages.create` API). The LLM will decide whether to respond directly or to use one of the provided tools.

4.  **Process LLM Response**: Iterate through the LLM's response content:
    *   **Text Content**: If the LLM provides a text response, append it to your `final_text` output.
    *   **Tool Use Content**: If the LLM decides to use a tool (`content.type == 'tool_use'`):
        *   Extract the `tool_name` and `tool_args` from the LLM's response.
        *   **Execute Tool Call**: Use your MCP client's `call_tool()` method (e.g., `await self.session.call_tool(tool_name, tool_args)`) to send the tool execution request to the MCP server.
        *   **Integrate Tool Results**: The MCP server will execute the tool and return the result. Append this result back into your conversation history, typically as a `tool_result` message from the 'user' role, so the LLM can see the outcome of its tool call.
        *   **Subsequent LLM Call**: Make another call to the LLM, including the new `tool_result` in the messages. This allows the LLM to interpret the tool's output and generate a natural language response based on it.

```python
# Python example (simplified process_query method)
async def process_query(self, query: str) -> str:
    messages = [{"role": "user", "content": query}]
    response = await self.session.list_tools()
    available_tools = [{ "name": tool.name, "description": tool.description, "input_schema": tool.inputSchema } for tool in response.tools]

    claude_response = self.anthropic.messages.create(model="claude-3-5-sonnet-20241022", messages=messages, tools=available_tools)

    final_text = []
    for content in claude_response.content:
        if content.type == 'text':
            final_text.append(content.text)
        elif content.type == 'tool_use':
            tool_name = content.name
            tool_args = content.input
            result = await self.session.call_tool(tool_name, tool_args)
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            messages.append({"role": "assistant", "content": [content]})
            messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": content.id, "content": result.content}]})

            claude_response_after_tool = self.anthropic.messages.create(model="claude-3-5-sonnet-20241022", messages=messages, tools=available_tools)
            final_text.append(claude_response_after_tool.content[0].text)

    return "\n".join(final_text)
```

## Interactive Chat Interface and Main Entry Point

To make your client usable, you'll need an interactive loop and a main execution function.

1.  **Chat Loop**: Implement an asynchronous loop that prompts the user for input, calls your `process_query` method, and prints the response. Include a way to exit the loop (e.g., typing 'quit').

2.  **Cleanup**: Implement a `cleanup` method to properly close connections and release resources when the application exits or an error occurs. For Python, `AsyncExitStack` handles this gracefully. For Kotlin, `AutoCloseable` can be used. For C#, `await using` on the `McpClientFactory.CreateAsync` result ensures proper disposal.

3.  **Main Entry Point**: Create a `main` function that parses command-line arguments (specifically the path to the MCP server script), initializes your `MCPClient`, connects to the server, runs the chat loop, and ensures cleanup is performed in a `try-finally` block.

```python
# Python example (simplified chat_loop and main)
async def chat_loop(self):
    print("\nMCP Client Started!\nType your queries or 'quit' to exit.")
    while True:
        query = input("\nQuery: ").strip()
        if query.lower() == 'quit': break
        try: print("\n" + await self.process_query(query))
        except Exception as e: print(f"\nError: {str(e)}")

async def cleanup(self): await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2: print("Usage: python client.py <path_to_server_script>"); sys.exit(1)
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally: await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
```

## Key Components Explained

*   **Client Initialization**: Sets up the necessary SDK clients (MCP and LLM) and resource management tools.
*   **Server Connection**: Establishes communication with the MCP server, typically via stdio, and performs the initial handshake to discover server capabilities and tools.
*   **Query Processing**: The core logic that orchestrates the interaction between user input, the LLM, and MCP server tools. It manages conversation history and integrates tool results.
*   **Interactive Interface**: Provides a user-friendly way to interact with the chatbot, handling input and displaying responses.
*   **Resource Management**: Ensures that all connections and resources are properly closed and cleaned up, even in the event of errors.

## Common Customization Points

*   **Tool Handling**: Modify `process_query()` to implement custom logic for specific tool types, add advanced error handling for tool calls, or format tool-specific responses.
*   **Response Processing**: Customize how LLM responses and tool results are formatted, add filtering or transformation logic, or implement custom logging for debugging.
*   **User Interface**: Extend beyond a command-line interface to build a GUI or web interface, add features like command history, auto-completion, or rich console output.

## Running the Client

To run your client, you'll typically execute your main client script and provide the path to the MCP server script as an argument.

```bash
# For Python client with a Python server
uv run client.py path/to/server.py

# For Node.js client with a Node.js server
npm run build # (if using TypeScript)
node build/index.js path/to/build/index.js

# For Java/Kotlin client with a Java server
./gradlew build # or ./mvnw clean install
java -jar build/libs/<your-jar-name>.jar path/to/server.jar

# For C# client with a .NET server
dotnet run -- path/to/server.csproj
```

## How It Works: The Client-Server-LLM Workflow

When you submit a query to your MCP client, the following sequence of events typically occurs:

1.  **Client Gets Tools**: The client first retrieves the list of available tools from the connected MCP server.
2.  **Query to LLM**: Your query, along with the descriptions of the available tools, is sent to the LLM (e.g., Claude).
3.  **LLM Decides**: The LLM processes the query and decides whether to generate a direct response or to use one or more of the provided tools to fulfill the request.
4.  **Client Executes Tool**: If the LLM decides to use a tool, the client intercepts this `tool_use` instruction and sends a `call_tool` request to the MCP server.
5.  **Server Executes Tool**: The MCP server receives the `call_tool` request, executes the specified tool (which might involve interacting with external services or local resources), and returns the result to the client.
6.  **Results to LLM**: The client receives the tool's result and sends it back to the LLM, providing the context of the tool's execution.
7.  **LLM Responds**: The LLM processes the tool's result and generates a natural language response, which is then sent back to the client.
8.  **Client Displays Response**: The client receives the final response from the LLM and displays it to you.

## Best Practices for MCP Client Development

*   **Error Handling**: Always wrap tool calls and network operations in `try-catch` blocks. Provide meaningful error messages to the user and gracefully handle connection issues, timeouts, and failed tool executions.
*   **Resource Management**: Use appropriate mechanisms (e.g., `AsyncExitStack` in Python, `AutoCloseable` in Kotlin, `using` in C#, `transport.close()` in Node.js) to ensure all connections are properly closed and resources are released when the client exits or encounters an error.
*   **Security**: Store API keys securely (e.g., `.env` files, user secrets, environment variables). Validate all incoming messages and server responses. Be cautious with tool permissions and the data they can access or modify.
*   **Response Timing**: Be aware that initial responses might take longer (up to 30 seconds) due to server initialization, LLM processing, and tool execution. Subsequent responses are typically faster.

## Troubleshooting Common Issues

*   **Server Path Issues**: Double-check that the path to your server script is correct. Use absolute paths if relative paths cause problems. Ensure the file has the correct extension (`.py`, `.js`, `.jar`, `.csproj`).
*   **Connection Refused**: Verify that the server script exists, has correct permissions, and is executable. Try running the server script directly to check for any startup errors.
*   **Tool Execution Failed**: Check the server's logs for specific error messages. Ensure that any environment variables or configurations required by the tool are correctly set.
*   **API Key Not Set**: If you see errors like `ANTHROPIC_API_KEY is not set`, verify your `.env` file, user secrets, or environment variables are correctly configured and loaded.
*   **Response Timing**: The first response can be slow. Do not interrupt the process during this initial waiting period.

## Understanding MCP Transports

Transports are the underlying mechanisms for communication between MCP clients and servers. They handle the conversion of MCP protocol messages to and from the **JSON-RPC 2.0** wire format.

### Built-in Transport Types

1.  **Standard Input/Output (Stdio)**:
    *   **Use Case**: Ideal for local integrations, command-line tools, and simple process communication on the same machine.
    *   **Mechanism**: Uses standard input and output streams for message exchange.
    *   **Implementation**: Clients typically launch the server as a child process and pipe messages through its stdio.

2.  **Server-Sent Events (SSE)**:
    *   **Use Case**: Suitable for scenarios requiring server-to-client streaming over HTTP, with HTTP POST for client-to-server messages.
    *   **Mechanism**: Leverages HTTP for communication, making it compatible with web environments.

### Custom Transports

MCP allows for custom transport implementations by conforming to a `Transport` interface. This enables developers to use specialized communication channels, integrate with existing systems, or optimize performance for unique requirements.

### Transport Error Handling

Robust transport implementations should handle:

*   Connection errors (e.g., `FileNotFoundError`, `Connection refused`).
*   Message parsing errors (invalid JSON-RPC).
*   Network timeouts.
*   Proper resource cleanup on disconnection.

## Sampling: LLM Completions via the Client

Sampling is an advanced MCP feature that allows servers to request LLM completions through the client. This design ensures that users maintain control over what the LLM sees and generates, promoting security and privacy.

### How Sampling Works

1.  **Server Request**: The MCP server sends a `sampling/createMessage` request to the client.
2.  **Client Review (Prompt)**: The client reviews the proposed prompt (messages, system prompt, context inclusion) and can modify or reject it, potentially showing it to the user for approval.
3.  **Client Samples LLM**: The client then samples from an LLM (e.g., Claude) using the reviewed prompt and specified model preferences (hints, cost/speed/intelligence priority, temperature, max tokens, stop sequences).
4.  **Client Review (Completion)**: The client reviews the generated completion from the LLM, and can modify or reject it, potentially showing it to the user for approval.
5.  **Client Returns Result**: The client returns the final completion result to the server.

### Message Format (Server to Client)

The `sampling/createMessage` request includes:

*   `messages`: Conversation history with `role` (user/assistant) and `content` (text/image).
*   `modelPreferences`: Hints for model selection (e.g., `name: "claude-3"`) and priority values for cost, speed, and intelligence (0-1).
*   `systemPrompt`: An optional system prompt for the LLM.
*   `includeContext`: Specifies what MCP context to include (`none`, `thisServer`, `allServers`). The client makes the final decision.
*   `temperature`, `maxTokens`, `stopSequences`, `metadata`: Standard LLM sampling parameters.

### Response Format (Client to Server)

The client returns a completion result containing:

*   `model`: Name of the model used.
*   `stopReason`: Why generation stopped (e.g., `endTurn`, `maxTokens`).
*   `role`: Role of the generated content (e.g., `assistant`).
*   `content`: The generated message content (text or image).

### Human-in-the-Loop Controls

Sampling is designed with human oversight:

*   **For Prompts**: Clients should display proposed prompts, allow users to modify or reject them, and control context inclusion.
*   **For Completions**: Clients should display generated completions, allow users to modify or reject them, and control which model is used.

### Security Considerations for Sampling

*   **Validation**: Validate all message content and sanitize sensitive information.
*   **Rate Limiting**: Implement appropriate rate limits to prevent abuse.
*   **Data Privacy**: Handle user data privacy according to regulations.
*   **Cost Control**: Monitor sampling usage and control cost exposure.
*   **Timeouts**: Implement timeouts for LLM calls.

### Limitations

*   Sampling depends on client capabilities and user controls.
*   Context size and rate limits apply.
*   Model availability and response times can vary.