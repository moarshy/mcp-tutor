# Core MCP Capabilities: Context and Actions

The Model Context Protocol (MCP) enables servers to expose various capabilities to clients and Large Language Models (LLMs), facilitating rich interactions and real-world actions. This module details four primary capabilities: Resources, Tools, Prompts, and Sampling.

## Resources

Resources are a fundamental primitive in MCP that allow servers to expose data and content for clients and LLMs to read and use as context. They are designed to be **application-controlled**, meaning the client application determines how and when they are utilized.

### Overview of Resources

Resources represent any type of data an MCP server wishes to make available. This can include:
*   File contents
*   Database records
*   API responses
*   Live system data
*   Images or PDFs
*   Log files

Each resource is uniquely identified by a URI and can contain either text or binary data.

### Resource URIs

Resources are identified using URIs that follow the format: `[protocol]://[host]/[path]`.
Examples include:
*   `file:///home/user/documents/report.pdf`
*   `postgres://database/customers/schema`
*   `screen://localhost/display1`

The specific protocol and path structure are defined by the MCP server implementation, allowing for custom URI schemes.

### Resource Types

Resources can contain two main types of content:

*   **Text resources**: Contain UTF-8 encoded text data, suitable for source code, configuration files, log files, JSON/XML data, or plain text.
*   **Binary resources**: Contain raw binary data encoded in base64, suitable for images, PDFs, audio/video files, or other non-text formats.

### Resource Discovery

Clients can discover available resources through two methods:

1.  **Direct resources**: Servers expose a list of concrete resources via the `resources/list` endpoint. Each resource includes:
    ```typescript
    {
      uri: string;           // Unique identifier for the resource
      name: string;          // Human-readable name
      description?: string;  // Optional description
      mimeType?: string;     // Optional MIME type
    }
    ```
2.  **Resource templates**: For dynamic resources, servers can expose [URI templates](https://datatracker.ietf.org/doc/html/rfc6570) that clients use to construct valid resource URIs.
    ```typescript
    {
      uriTemplate: string;   // URI template following RFC 6570
      name: string;          // Human-readable name for this type
      description?: string;  // Optional description
      mimeType?: string;     // Optional MIME type for all matching resources
    }
    ```

### Reading Resources

To read a resource, clients send a `resources/read` request with the resource URI. The server responds with a list of resource contents:

```typescript
{
  contents: [
    {
      uri: string;        // The URI of the resource
      mimeType?: string;  // Optional MIME type

      // One of:
      text?: string;      // For text resources
      blob?: string;      // For binary resources (base64 encoded)
    }
  ]
}
```
Servers may return multiple resources in response to a single `resources/read` request, for example, to list files within a directory.

### Resource Updates

MCP supports real-time updates for resources:

*   **List changes**: Servers can notify clients when the list of available resources changes using the `notifications/resources/list_changed` notification.
*   **Content changes**: Clients can subscribe to updates for specific resources by sending `resources/subscribe` with the resource URI. The server then sends `notifications/resources/updated` when the resource changes, prompting the client to fetch the latest content with `resources/read`. Clients can unsubscribe with `resources/unsubscribe`.

### Best Practices for Resources

When implementing resource support, it is recommended to:
*   Use clear, descriptive names and URIs.
*   Include helpful descriptions for LLM understanding.
*   Set appropriate MIME types.
*   Implement resource templates for dynamic content.
*   Use subscriptions for frequently changing resources.
*   Handle errors gracefully with clear messages.
*   Consider pagination for large resource lists.
*   Cache resource contents when appropriate.
*   Validate URIs before processing.
*   Document custom URI schemes.

### Security Considerations for Resources

When exposing resources, it is crucial to:
*   Validate all resource URIs.
*   Implement appropriate access controls.
*   Sanitize file paths to prevent directory traversal.
*   Be cautious with binary data handling.
*   Consider rate limiting for resource reads.
*   Audit resource access.
*   Encrypt sensitive data in transit.
*   Validate MIME types.
*   Implement timeouts for long-running reads.
*   Handle resource cleanup appropriately.

## Tools

Tools are a powerful primitive in MCP that enable servers to expose executable functionality to clients, allowing LLMs to interact with external systems, perform computations, and take actions in the real world. Tools are designed to be **model-controlled**, meaning they are exposed with the intention of the AI model automatically invoking them (with human approval).

### Overview of Tools

Tools allow servers to expose functions that can be invoked by clients and used by LLMs. Key aspects include:
*   **Discovery**: Clients can list available tools via the `tools/list` endpoint.
*   **Invocation**: Tools are called using the `tools/call` endpoint, where servers perform the requested operation and return results.
*   **Flexibility**: Tools can range from simple calculations to complex API interactions.

Unlike resources, tools represent dynamic operations that can modify state or interact with external systems.

### Tool Definition Structure

Each tool is defined with the following structure:

```typescript
{
  name: string;          // Unique identifier for the tool
  description?: string;  // Human-readable description
  inputSchema: {         // JSON Schema for the tool's parameters
    type: "object",
    properties: { ... }  // Tool-specific parameters
  }
}
```

### Implementing Tools

An example of a `calculate_sum` tool:

```typescript
// Define available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [{
      name: "calculate_sum",
      description: "Add two numbers together",
      inputSchema: {
        type: "object",
        properties: {
          a: { type: "number" },
          b: { type: "number" }
        },
        required: ["a", "b"]
      }
    }]
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "calculate_sum") {
    const { a, b } = request.params.arguments;
    return {
      content: [
        {
          type: "text",
          text: String(a + b)
        }
      ]
    };
  }
  throw new Error("Tool not found");
});
```

### Example Tool Patterns

Servers can provide various types of tools:

*   **System operations**: E.g., `execute_command` to run a shell command.
*   **API integrations**: E.g., `github_create_issue` to interact with external APIs.
*   **Data processing**: E.g., `analyze_csv` to transform or analyze data.

### Best Practices for Tools

When implementing tools, it is recommended to:
*   Provide clear, descriptive names and descriptions.
*   Use detailed JSON Schema definitions for parameters.
*   Include examples in tool descriptions to guide model usage.
*   Implement proper error handling and validation.
*   Use progress reporting for long operations.
*   Keep tool operations focused and atomic.
*   Document expected return value structures.
*   Implement proper timeouts.
*   Consider rate limiting for resource-intensive operations.
*   Log tool usage for debugging and monitoring.

### Security Considerations for Tools

When exposing tools, it is crucial to:
*   **Input validation**: Validate all parameters against the schema, sanitize file paths and system commands, validate URLs, check parameter sizes, and prevent command injection.
*   **Access control**: Implement authentication and authorization, audit tool usage, rate limit requests, and monitor for abuse.
*   **Error handling**: Avoid exposing internal errors, log security-relevant errors, handle timeouts, clean up resources, and validate return values.

### Tool Discovery and Updates

MCP supports dynamic tool discovery:
*   Clients can list available tools at any time.
*   Servers can notify clients of tool changes using `notifications/tools/list_changed`.
*   Tools can be added, removed, or updated during runtime.

### Error Handling for Tools

Tool errors should be reported within the result object, not as MCP protocol-level errors. This allows the LLM to see and potentially handle the error. When a tool encounters an error:
1.  Set `isError` to `true` in the result.
2.  Include error details in the `content` array.

Example of error handling:

```typescript
try {
  // Tool operation
  const result = performOperation();
  return {
    content: [
      {
        type: "text",
        text: `Operation successful: ${result}`
      }
    ]
  };
} catch (error) {
  return {
    isError: true,
    content: [
      {
        type: "text",
        text: `Error: ${error.message}`
      }
    ]
  };
}
```

## Prompts

Prompts enable servers to define reusable prompt templates and workflows that clients can easily surface to users and LLMs. They provide a powerful way to standardize and share common LLM interactions. Prompts are designed to be **user-controlled**, meaning they are exposed with the intention of the user explicitly selecting them for use.

### Overview of Prompts

Prompts in MCP are predefined templates that can:
*   Accept dynamic arguments.
*   Include context from resources.
*   Chain multiple interactions.
*   Guide specific workflows.
*   Surface as UI elements (e.g., slash commands).

### Prompt Structure

Each prompt is defined with:

```typescript
{
  name: string;              // Unique identifier for the prompt
  description?: string;      // Human-readable description
  arguments?: [              // Optional list of arguments
    {
      name: string;          // Argument identifier
      description?: string;  // Argument description
      required?: boolean;    // Whether argument is required
    }
  ]
}
```

### Discovering Prompts

Clients can discover available prompts through the `prompts/list` endpoint.

**Request:**
```json
{
  "method": "prompts/list"
}
```

**Response Example:**
```json
{
  "prompts": [
    {
      "name": "analyze-code",
      "description": "Analyze code for potential improvements",
      "arguments": [
        {
          "name": "language",
          "description": "Programming language",
          "required": true
        }
      ]
    }
  ]
}
```

### Using Prompts

To use a prompt, clients make a `prompts/get` request.

**Request Example:**
```json
{
  "method": "prompts/get",
  "params": {
    "name": "analyze-code",
    "arguments": {
      "language": "python"
    }
  }
}
```

**Response Example:**
```json
{
  "description": "Analyze Python code for potential improvements",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Please analyze the following Python code for potential improvements:\n\n```python\ndef calculate_sum(numbers):\n    total = 0\n    for num in numbers:\n        total = total + num\n    return total\n\nresult = calculate_sum([1, 2, 3, 4, 5])\nprint(result)\n```"
      }
    }
  ]
}
```

### Dynamic Prompts

Prompts can be dynamic and include:

*   **Embedded resource context**: Prompts can incorporate content from resources directly into the messages. For example, a prompt to "analyze-project" might take `timeframe` and `fileUri` arguments and embed logs and code file content.
*   **Multi-step workflows**: Prompts can define a sequence of messages, simulating a multi-turn conversation or a guided workflow.

### Best Practices for Prompts

When implementing prompts, it is recommended to:
*   Use clear, descriptive prompt names.
*   Provide detailed descriptions for prompts and arguments.
*   Validate all required arguments.
*   Handle missing arguments gracefully.
*   Consider versioning for prompt templates.
*   Cache dynamic content when appropriate.
*   Implement error handling.
*   Document expected argument formats.
*   Consider prompt composability.
*   Test prompts with various inputs.

### UI Integration for Prompts

Prompts can be surfaced in client UIs as:
*   Slash commands
*   Quick actions
*   Context menu items
*   Command palette entries
*   Guided workflows
*   Interactive forms

### Updates and Changes for Prompts

Servers can notify clients about prompt changes via the `notifications/prompts/list_changed` notification, prompting the client to re-fetch the prompt list.

### Security Considerations for Prompts

When implementing prompts, it is crucial to:
*   Validate all arguments.
*   Sanitize user input.
*   Consider rate limiting.
*   Implement access controls.
*   Audit prompt usage.
*   Handle sensitive data appropriately.
*   Validate generated content.
*   Implement timeouts.
*   Consider prompt injection risks.
*   Document security requirements.

## Sampling

Sampling is an MCP feature that allows servers to request LLM completions through the client, enabling sophisticated agentic behaviors while maintaining security and privacy. This feature is designed with a **human-in-the-loop** approach.

### How Sampling Works

The sampling workflow involves five steps:
1.  **Server sends request**: The server sends a `sampling/createMessage` request to the client.
2.  **Client reviews request**: The client reviews the request and can modify it.
3.  **Client samples from LLM**: The client samples from an LLM based on the (potentially modified) request.
4.  **Client reviews completion**: The client reviews the LLM's completion.
5.  **Client returns result**: The client returns the result to the server.

This design ensures users maintain control over what the LLM sees and generates.

### Message Format for Sampling Requests

Sampling requests use a standardized message format:

```typescript
{
  messages: [
    {
      role: "user" | "assistant",
      content: {
        type: "text" | "image",

        // For text:
        text?: string,

        // For images:
        data?: string,             // base64 encoded
        mimeType?: string
      }
    }
  ],
  modelPreferences?: {
    hints?: [{
      name?: string                // Suggested model name/family
    }],
    costPriority?: number,         // 0-1, importance of minimizing cost
    speedPriority?: number,        // 0-1, importance of low latency
    intelligencePriority?: number  // 0-1, importance of capabilities
  },
  systemPrompt?: string,
  includeContext?: "none" | "thisServer" | "allServers",
  temperature?: number,
  maxTokens: number,
  stopSequences?: string[],
  metadata?: Record<string, unknown>
}
```

### Request Parameters

*   **`messages`**: An array containing the conversation history (`role` and `content`). Content can be `text` or `image` (base64 encoded `data` with `mimeType`).
*   **`modelPreferences`**: Allows servers to specify model selection preferences:
    *   `hints`: Suggested model names (e.g., "claude-3", "sonnet"). Clients may map hints to equivalent models.
    *   `costPriority`, `speedPriority`, `intelligencePriority`: Normalized values (0-1) indicating the importance of minimizing cost, low latency, or advanced capabilities, respectively. Clients make the final model selection.
*   **`systemPrompt`**: An optional field for a specific system prompt. The client may modify or ignore this.
*   **`includeContext`**: Specifies what MCP context to include:
    *   `"none"`: No additional context.
    *   `"thisServer"`: Context from the requesting server.
    *   `"allServers"`: Context from all connected MCP servers.
    The client controls what context is actually included.
*   **Sampling parameters**:
    *   `temperature`: Controls randomness (0.0 to 1.0).
    *   `maxTokens`: Maximum tokens to generate.
    *   `stopSequences`: Array of sequences that stop generation.
    *   `metadata`: Additional provider-specific parameters.

### Response Format

The client returns a completion result:

```typescript
{
  model: string,  // Name of the model used
  stopReason?: "endTurn" | "stopSequence" | "maxTokens" | string,
  role: "user" | "assistant",
  content: {
    type: "text" | "image",
    text?: string,
    data?: string,
    mimeType?: string
  }
}
```

### Example Sampling Request

```json
{
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "What files are in the current directory?"
        }
      }
    ],
    "systemPrompt": "You are a helpful file system assistant.",
    "includeContext": "thisServer",
    "maxTokens": 100
  }
}
```

### Best Practices for Sampling

When implementing sampling, it is recommended to:
*   Always provide clear, well-structured prompts.
*   Handle both text and image content appropriately.
*   Set reasonable token limits.
*   Include relevant context through `includeContext`.
*   Validate responses before using them.
*   Handle errors gracefully.
*   Consider rate limiting sampling requests.
*   Document expected sampling behavior.
*   Test with various model parameters.
*   Monitor sampling costs.

### Human-in-the-Loop Controls for Sampling

Sampling is designed with human oversight:
*   **For prompts**: Clients should show users the proposed prompt, allow modification or rejection, filter/modify system prompts, and control context inclusion.
*   **For completions**: Clients should show users the completion, allow modification or rejection, filter/modify completions, and allow users to control which model is used.

### Security Considerations for Sampling

When implementing sampling, it is crucial to:
*   Validate all message content.
*   Sanitize sensitive information.
*   Implement appropriate rate limits.
*   Monitor sampling usage.
*   Encrypt data in transit.
*   Handle user data privacy.
*   Audit sampling requests.
*   Control cost exposure.
*   Implement timeouts.
*   Handle model errors gracefully.

### Common Patterns and Limitations for Sampling

*   **Agentic workflows**: Sampling enables patterns like reading/analyzing resources, decision-making, structured data generation, multi-step tasks, and interactive assistance.
*   **Context management**: Best practices include requesting minimal necessary context, structuring it clearly, handling size limits, updating as needed, and cleaning up stale context.
*   **Error handling**: Robust error handling should catch sampling failures, handle timeouts, manage rate limits, validate responses, provide fallback behaviors, and log errors.
*   **Limitations**: Sampling depends on client capabilities, users control behavior, context size has limits, rate limits may apply, costs should be considered, model availability varies, response times vary, and not all content types are supported.