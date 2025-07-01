This module guides client developers through building an LLM-powered chatbot client capable of integrating with Model Context Protocol (MCP) servers. It covers environment setup, API key configuration, and the fundamental code structure for managing connections and processing queries in both Python and Node.js (TypeScript).

MCP follows a client-server architecture where clients maintain 1:1 connections with servers, inside a host application. The client initiates the connection by sending an `initialize` request, and after the server responds, the client sends an `initialized` notification, after which normal message exchange begins. Clients and servers can exchange requests (expecting a response) and notifications (one-way messages).

## Building an MCP Client in Python

This section details how to build an LLM-powered chatbot client in Python that connects to MCP servers.

### System Requirements

Before starting, ensure your system meets these requirements:
*   Mac or Windows computer
*   Latest Python version installed
*   Latest version of `uv` installed

### Setting Up Your Environment

First, create a new Python project with `uv`:

```bash
# Create project directory
uv init mcp-client
cd mcp-client

# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate

# Install required packages
uv add mcp anthropic python-dotenv

# Remove boilerplate files
rm main.py

# Create our main file
touch client.py
```

### Setting Up Your API Key

You'll need an Anthropic API key from the [Anthropic Console](https://console.anthropic.com/settings/keys).

Create a `.env` file to store it:

```bash
# Create .env file
touch .env
```

Add your key to the `.env` file:
```bash
ANTHROPIC_API_KEY=<your key here>
```

Add `.env` to your `.gitignore`:
```bash
echo ".env" >> .gitignore
```

<Warning>
Make sure you keep your `ANTHROPIC_API_KEY` secure!
</Warning>

### Basic Client Structure

First, let's set up our imports and create the basic client class in `client.py`:

```python
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
    # methods will go here
```

### Server Connection Management

Next, implement the method to connect to an MCP server:

```python
async def connect_to_server(self, server_script_path: str):
    """Connect to an MCP server

    Args:
        server_script_path: Path to the server script (.py or .js)
    """
    is_python = server_script_path.endswith('.py')
    is_js = server_script_path.endswith('.js')
    if not (is_python or is_js):
        raise ValueError("Server script must be a .py or .js file")

    command = "python" if is_python else "node"
    server_params = StdioServerParameters(
        command=command,
        args=[server_script_path],
        env=None
    )

    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
    self.stdio, self.write = stdio_transport
    self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

    await self.session.initialize()

    # List available tools
    response = await self.session.list_tools()
    tools = response.tools
    print("\nConnected to server with tools:", [tool.name for tool in tools])
```

### Query Processing Logic

Now add the core functionality for processing queries and handling tool calls:

```python
async def process_query(self, query: str) -> str:
    """Process a query using Claude and available tools"""
    messages = [
        {
            "role": "user",
            "content": query
        }
    ]

    response = await self.session.list_tools()
    available_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in response.tools]

    # Initial Claude API call
    response = self.anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=messages,
        tools=available_tools
    )

    # Process response and handle tool calls
    final_text = []

    assistant_message_content = []
    for content in response.content:
        if content.type == 'text':
            final_text.append(content.text)
            assistant_message_content.append(content)
        elif content.type == 'tool_use':
            tool_name = content.name
            tool_args = content.input

            # Execute tool call
            result = await self.session.call_tool(tool_name, tool_args)
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            assistant_message_content.append(content)
            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    }
                ]
            })

            # Get next response from Claude
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )

            final_text.append(response.content[0].text)

    return "\n".join(final_text)
```

### Interactive Chat Interface

Now add the chat loop and cleanup functionality:

```python
async def chat_loop(self):
    """Run an interactive chat loop"""
    print("\nMCP Client Started!")
    print("Type your queries or 'quit' to exit.")

    while True:
        try:
            query = input("\nQuery: ").strip()

            if query.lower() == 'quit':
                break

            response = await self.process_query(query)
            print("\n" + response)

        except Exception as e:
            print(f"\nError: {str(e)}")

async def cleanup(self):
    """Clean up resources"""
    await self.exit_stack.aclose()
```

### Main Entry Point

Finally, add the main execution logic:

```python
async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
```

### Key Components Explained (Python)

1.  **Client Initialization**: The `MCPClient` class initializes with session management and API clients. It uses `AsyncExitStack` for proper resource management and configures the Anthropic client for Claude interactions.
2.  **Server Connection**: The `connect_to_server` method supports both Python and Node.js servers, validates the server script type, sets up proper communication channels using `StdioServerParameters` and `stdio_client`, initializes the `ClientSession`, and lists available tools.
3.  **Query Processing**: The `process_query` method maintains conversation context, handles Claude's responses and tool calls, manages the message flow between Claude and tools, and combines results into a coherent response.
4.  **Interactive Interface**: The `chat_loop` provides a simple command-line interface, handles user input, displays responses, includes basic error handling, and allows graceful exit.
5.  **Resource Management**: The `cleanup` method ensures proper cleanup of resources, handles error conditions for connection issues, and facilitates graceful shutdown procedures.

### Running the Python Client

To run your client with any MCP server:

```bash
uv run client.py path/to/server.py # python server
uv run client.py path/to/build/index.js # node server
```

The client will:
1.  Connect to the specified server.
2.  List available tools.
3.  Start an interactive chat session where you can:
    *   Enter queries
    *   See tool executions
    *   Get responses from Claude

### How It Works (Python)

When you submit a query:
1.  The client gets the list of available tools from the server.
2.  Your query is sent to Claude along with tool descriptions.
3.  Claude decides which tools (if any) to use.
4.  The client executes any requested tool calls through the server.
5.  Results are sent back to Claude.
6.  Claude provides a natural language response.
7.  The response is displayed to you.

### Best Practices (Python)

1.  **Error Handling**: Always wrap tool calls in try-catch blocks, provide meaningful error messages, and gracefully handle connection issues.
2.  **Resource Management**: Use `AsyncExitStack` for proper cleanup, close connections when done, and handle server disconnections.
3.  **Security**: Store API keys securely in `.env`, validate server responses, and be cautious with tool permissions.

### Troubleshooting (Python)

*   **Server Path Issues**: Double-check the path to your server script is correct. Use the absolute path if the relative path isn't working. For Windows users, make sure to use forward slashes (/) or escaped backslashes (\\) in the path. Verify the server file has the correct extension (.py for Python or .js for Node.js).
*   **Response Timing**: The first response might take up to 30 seconds to return. This is normal and happens while the server initializes, Claude processes the query, and tools are being executed. Subsequent responses are typically faster. Don't interrupt the process during this initial waiting period.
*   **Common Error Messages**:
    *   `FileNotFoundError`: Check your server path.
    *   `Connection refused`: Ensure the server is running and the path is correct.
    *   `Tool execution failed`: Verify the tool's required environment variables are set.
    *   `Timeout error`: Consider increasing the timeout in your client configuration.

## Building an MCP Client in Node.js (TypeScript)

This section details how to build an LLM-powered chatbot client in Node.js using TypeScript that connects to MCP servers.

### System Requirements

Before starting, ensure your system meets these requirements:
*   Mac or Windows computer
*   Node.js 17 or higher installed
*   Latest version of `npm` installed
*   Anthropic API key (Claude)

### Setting Up Your Environment

First, let's create and set up our project:

<CodeGroup>
```bash MacOS/Linux
# Create project directory
mkdir mcp-client-typescript
cd mcp-client-typescript

# Initialize npm project
npm init -y

# Install dependencies
npm install @anthropic-ai/sdk @modelcontextprotocol/sdk dotenv

# Install dev dependencies
npm install -D @types/node typescript

# Create source file
touch index.ts
```

```powershell Windows
# Create project directory
md mcp-client-typescript
cd mcp-client-typescript

# Initialize npm project
npm init -y

# Install dependencies
npm install @anthropic-ai/sdk @modelcontextprotocol/sdk dotenv

# Install dev dependencies
npm install -D @types/node typescript

# Create source file
new-item index.ts
```
</CodeGroup>

Update your `package.json` to set `type: "module"` and a build script:

```json package.json
{
  "type": "module",
  "scripts": {
    "build": "tsc && chmod 755 build/index.js"
  }
}
```

Create a `tsconfig.json` in the root of your project:

```json tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./build",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["index.ts"],
  "exclude": ["node_modules"]
}
```

### Setting Up Your API Key

You'll need an Anthropic API key from the [Anthropic Console](https://console.anthropic.com/settings/keys).

Create a `.env` file to store it:

```bash
echo "ANTHROPIC_API_KEY=<your key here>" > .env
```

Add `.env` to your `.gitignore`:
```bash
echo ".env" >> .gitignore
```

<Warning>
Make sure you keep your `ANTHROPIC_API_KEY` secure!
</Warning>

### Basic Client Structure

First, let's set up our imports and create the basic client class in `index.ts`:

```typescript
import { Anthropic } from "@anthropic-ai/sdk";
import {
  MessageParam,
  Tool,
} from "@anthropic-ai/sdk/resources/messages/messages.mjs";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import readline from "readline/promises";
import dotenv from "dotenv";

dotenv.config();

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
if (!ANTHROPIC_API_KEY) {
  throw new Error("ANTHROPIC_API_KEY is not set");
}

class MCPClient {
  private mcp: Client;
  private anthropic: Anthropic;
  private transport: StdioClientTransport | null = null;
  private tools: Tool[] = [];

  constructor() {
    this.anthropic = new Anthropic({
      apiKey: ANTHROPIC_API_KEY,
    });
    this.mcp = new Client({ name: "mcp-client-cli", version: "1.0.0" });
  }
  // methods will go here
}
```

### Server Connection Management

Next, implement the method to connect to an MCP server:

```typescript
async connectToServer(serverScriptPath: string) {
  try {
    const isJs = serverScriptPath.endsWith(".js");
    const isPy = serverScriptPath.endsWith(".py");
    if (!isJs && !isPy) {
      throw new Error("Server script must be a .js or .py file");
    }
    const command = isPy
      ? process.platform === "win32"
        ? "python"
        : "python3"
      : process.execPath;
    
    this.transport = new StdioClientTransport({
      command,
      args: [serverScriptPath],
    });
    this.mcp.connect(this.transport);
    
    const toolsResult = await this.mcp.listTools();
    this.tools = toolsResult.tools.map((tool) => {
      return {
        name: tool.name,
        description: tool.description,
        input_schema: tool.inputSchema,
      };
    });
    console.log(
      "Connected to server with tools:",
      this.tools.map(({ name }) => name)
    );
  } catch (e) {
    console.log("Failed to connect to MCP server: ", e);
    throw e;
  }
}
```

### Query Processing Logic

Now add the core functionality for processing queries and handling tool calls:

```typescript
async processQuery(query: string) {
  const messages: MessageParam[] = [
    {
      role: "user",
      content: query,
    },
  ];

  const response = await this.anthropic.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 1000,
    messages,
    tools: this.tools,
  });

  const finalText = [];
  const toolResults = [];

  for (const content of response.content) {
    if (content.type === "text") {
      finalText.push(content.text);
    } else if (content.type === "tool_use") {
      const toolName = content.name;
      const toolArgs = content.input as { [x: string]: unknown } | undefined;

      const result = await this.mcp.callTool({
        name: toolName,
        arguments: toolArgs,
      });
      toolResults.push(result);
      finalText.push(
        `[Calling tool ${toolName} with args ${JSON.stringify(toolArgs)}]`
      );

      messages.push({
        role: "user",
        content: result.content as string,
      });

      const response = await this.anthropic.messages.create({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 1000,
        messages,
      });

      finalText.push(
        response.content[0].type === "text" ? response.content[0].text : ""
      );
    }
  }

  return finalText.join("\n");
}
```

### Interactive Chat Interface

Now add the chat loop and cleanup functionality:

```typescript
async chatLoop() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  try {
    console.log("\nMCP Client Started!");
    console.log("Type your queries or 'quit' to exit.");

    while (true) {
      const message = await rl.question("\nQuery: ");
      if (message.toLowerCase() === "quit") {
        break;
      }
      const response = await this.processQuery(message);
      console.log("\n" + response);
    }
  } finally {
    rl.close();
  }
}

async cleanup() {
  await this.mcp.close();
}
```

### Main Entry Point

Finally, add the main execution logic:

```typescript
async function main() {
  if (process.argv.length < 3) {
    console.log("Usage: node index.ts <path_to_server_script>");
    return;
  }
  const mcpClient = new MCPClient();
  try {
    await mcpClient.connectToServer(process.argv[2]);
    await mcpClient.chatLoop();
  } finally {
    await mcpClient.cleanup();
    process.exit(0);
  }
}

main();
```

### Key Components Explained (Node.js)

1.  **Client Initialization**: The `MCPClient` class initializes with the Anthropic SDK and the MCP `Client` instance, setting up the necessary API clients for interaction.
2.  **Server Connection**: The `connectToServer` method handles connecting to an MCP server, supporting both `.js` and `.py` server scripts. It uses `StdioClientTransport` to establish communication and then lists the available tools from the connected server.
3.  **Query Processing**: The `processQuery` method manages the conversation flow. It sends user queries to Claude along with available tools, processes Claude's responses (including `tool_use` directives), executes tool calls via the MCP server, and then sends the tool results back to Claude for a final natural language response.
4.  **Interactive Interface**: The `chatLoop` provides a command-line interface using Node.js's `readline` module, allowing users to input queries and view responses. It includes basic error handling and a mechanism to gracefully exit the chat.
5.  **Resource Management**: The `cleanup` method ensures that the MCP client connection is properly closed when the application exits, preventing resource leaks.

### Running the Node.js Client

To run your client with any MCP server:

```bash
# Build TypeScript
npm run build

# Run the client
node build/index.js path/to/server.py # python server
node build/index.js path/to/build/index.js # node server
```

The client will:
1.  Connect to the specified server.
2.  List available tools.
3.  Start an interactive chat session where you can:
    *   Enter queries
    *   See tool executions
    *   Get responses from Claude

### How It Works (Node.js)

When you submit a query:
1.  The client gets the list of available tools from the server.
2.  Your query is sent to Claude along with tool descriptions.
3.  Claude decides which tools (if any) to use.
4.  The client executes any requested tool calls through the server.
5.  Results are sent back to Claude.
6.  Claude provides a natural language response.
7.  The response is displayed to you.

### Best Practices (Node.js)

1.  **Error Handling**: Use TypeScript's type system for better error detection. Wrap tool calls in try-catch blocks, provide meaningful error messages, and gracefully handle connection issues.
2.  **Security**: Store API keys securely in `.env`, validate server responses, and be cautious with tool permissions.

### Troubleshooting (Node.js)

*   **Server Path Issues**: Double-check the path to your server script is correct. Use the absolute path if the relative path isn't working. For Windows users, make sure to use forward slashes (/) or escaped backslashes (\\) in the path. Verify the server file has the correct extension (.js for Node.js or .py for Python).
*   **Response Timing**: The first response might take up to 30 seconds to return. This is normal and happens while the server initializes, Claude processes the query, and tools are being executed. Subsequent responses are typically faster. Don't interrupt the process during this initial waiting period.
*   **Common Error Messages**:
    *   `Error: Cannot find module`: Check your build folder and ensure TypeScript compilation succeeded.
    *   `Connection refused`: Ensure the server is running and the path is correct.
    *   `Tool execution failed`: Verify the tool's required environment variables are set.
    *   `ANTHROPIC_API_KEY is not set`: Check your .env file and environment variables.
    *   `TypeError`: Ensure you're using the correct types for tool arguments.