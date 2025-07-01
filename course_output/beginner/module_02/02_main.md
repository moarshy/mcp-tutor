# Core MCP Primitives: Context, Actions, and Interaction

This module explores the fundamental building blocks of the Model Context Protocol (MCP), detailing how servers expose data, enable LLMs to perform actions, define reusable interactions, manage operational boundaries, and facilitate secure LLM completions.

## Resources

Resources are a core primitive in MCP that allow servers to expose data and content that can be read by clients and used as context for LLM interactions. Resources are designed to be **application-controlled**, meaning the client application decides how and when they are used. Different MCP clients may handle resources differently, for example, requiring explicit user selection or automatically selecting based on heuristics.

### Overview of Resources

Resources represent any kind of data an MCP server wants to make available to clients, such as file contents, database records, API responses, live system data, screenshots, or log files. Each resource is identified by a unique URI and can contain either text or binary data.

### Resource URIs

Resources are identified using URIs following the format `[protocol]://[host]/[path]`. Examples include `file:///home/user/documents/report.pdf`, `postgres://database/customers/schema`, or `screen://localhost/display1`. The protocol and path structure are defined by the MCP server implementation, allowing for custom URI schemes.

### Resource Types

Resources can contain two types of content:

*   **Text resources**: Contain UTF-8 encoded text data, suitable for source code, configuration files, log files, JSON/XML data, or plain text.
*   **Binary resources**: Contain raw binary data encoded in base64, suitable for images, PDFs, audio files, video files, or other non-text formats.

### Resource Discovery

Clients can discover available resources through two main methods:

*   **Direct resources**: Servers expose a list of concrete resources via the `resources/list` endpoint. Each resource includes a `uri`, `name`, optional `description`, and optional `mimeType`.
*   **Resource templates**: For dynamic resources, servers can expose [URI templates](https://datatracker.ietf.org/doc/html/rfc6570) that clients can use to construct valid resource URIs. These templates include `uriTemplate`, `name`, optional `description`, and optional `mimeType`.

### Reading Resources

To read a resource, clients make a `resources/read` request with the resource URI. The server responds with a list of resource contents, where each content item includes its `uri`, optional `mimeType`, and either `text` (for text resources) or `blob` (for binary resources, base64 encoded). Servers may return multiple resources in response to one `resources/read` request, for example, to return a list of files inside a directory.

### Resource Updates

MCP supports real-time updates for resources:

*   **List changes**: Servers can notify clients when their list of available resources changes via the `notifications/resources/list_changed` notification.
*   **Content changes**: Clients can subscribe to updates for specific resources by sending `resources/subscribe` with the resource URI. The server then sends `notifications/resources/updated` when the resource changes, prompting the client to fetch the latest content with `resources/read`. Clients can unsubscribe with `resources/unsubscribe`.

### Best Practices for Resources

When implementing resource support, it is recommended to use clear, descriptive names and URIs, include helpful descriptions, set appropriate MIME types, implement resource templates for dynamic content, use subscriptions for frequently changing resources, handle errors gracefully, consider pagination for large lists, cache contents, validate URIs, and document custom URI schemes.

### Security Considerations for Resources

When exposing resources, it is crucial to validate all resource URIs, implement appropriate access controls, sanitize file paths to prevent directory traversal, be cautious with binary data handling, consider rate limiting for reads, audit resource access, encrypt sensitive data in transit, validate MIME types, implement timeouts for long-running reads, and handle resource cleanup appropriately.

## Tools

Tools are a powerful primitive in MCP that enable servers to expose executable functionality to clients. Through tools, LLMs can interact with external systems, perform computations, and take actions in the real world. Tools are designed to be **model-controlled**, meaning they are exposed from servers to clients with the intention of the AI model being able to automatically invoke them, typically with human approval.

### Overview of Tools

Tools allow servers to expose executable functions that can be invoked by clients and used by LLMs. Key aspects include:

*   **Discovery**: Clients can list available tools through the `tools/list` endpoint.
*   **Invocation**: Tools are called using the `tools/call` endpoint, where servers perform the requested operation and return results.
*   **Flexibility**: Tools can range from simple calculations to complex API interactions.

Tools are identified by unique names and can include descriptions to guide their usage. Unlike resources, tools represent dynamic operations that can modify state or interact with external systems.

### Tool Definition Structure

Each tool is defined with a `name` (unique identifier), an optional `description` (human-readable), and an `inputSchema` (JSON Schema for the tool's parameters).

### Example Tool Patterns

Servers can provide various types of tools:

*   **System operations**: Tools that interact with the local system, e.g., `execute_command`.
*   **API integrations**: Tools that wrap external APIs, e.g., `github_create_issue`.
*   **Data processing**: Tools that transform or analyze data, e.g., `analyze_csv`.

### Best Practices for Tools

When implementing tools, it is best to provide clear, descriptive names and descriptions, use detailed JSON Schema definitions for parameters, include examples in descriptions, implement proper error handling and validation, use progress reporting for long operations, keep operations focused and atomic, document return value structures, implement timeouts, consider rate limiting, and log tool usage.

### Security Considerations for Tools

When exposing tools, robust security measures are essential:

*   **Input validation**: Validate all parameters against the schema, sanitize file paths and system commands, validate URLs, check parameter sizes and ranges, and prevent command injection.
*   **Access control**: Implement authentication and authorization checks, audit tool usage, rate limit requests, and monitor for abuse.
*   **Error handling**: Avoid exposing internal errors to clients, log security-relevant errors, handle timeouts appropriately, clean up resources after errors, and validate return values.

### Tool Discovery and Updates

MCP supports dynamic tool discovery. Clients can list available tools at any time, and servers can notify clients when tools change using `notifications/tools/list_changed`. Tools can be added, removed, or updated during runtime.

### Error Handling for Tools

Tool errors should be reported within the result object of the `tools/call` response, not as MCP protocol-level errors. This allows the LLM to see and potentially handle the error. When a tool encounters an error, `isError` should be set to `true` in the result, and error details should be included in the `content` array.

## Prompts

Prompts enable servers to define reusable prompt templates and workflows that clients can easily surface to users and LLMs. They provide a powerful way to standardize and share common LLM interactions. Prompts are designed to be **user-controlled**, meaning they are exposed from servers to clients with the intention of the user being able to explicitly select them for use.

### Overview of Prompts

Prompts in MCP are predefined templates that can accept dynamic arguments, include context from resources, chain multiple interactions, guide specific workflows, and surface as UI elements (e.g., slash commands).

### Prompt Structure

Each prompt is defined with a `name` (unique identifier), an optional `description` (human-readable), and an optional `arguments` list. Each argument has a `name`, optional `description`, and a `required` boolean.

### Discovering Prompts

Clients can discover available prompts through the `prompts/list` endpoint, which returns a list of prompt definitions.

### Using Prompts

To use a prompt, clients make a `prompts/get` request, providing the prompt `name` and any necessary `arguments`. The server responds with a `description` and a `messages` array, which contains the structured conversation history for the LLM.

### Dynamic Prompts

Prompts can be dynamic and include:

*   **Embedded resource context**: Prompts can include references to resources, allowing the server to fetch and embed resource content (e.g., logs, code files) directly into the prompt messages sent to the LLM.
*   **Multi-step workflows**: Prompts can define sequences of interactions, guiding the LLM through a workflow by providing initial messages and potentially anticipating subsequent user or assistant turns.

### Best Practices for Prompts

When implementing prompts, it is advisable to use clear, descriptive names, provide detailed descriptions for prompts and arguments, validate all required arguments, handle missing arguments gracefully, consider versioning for templates, cache dynamic content, implement error handling, document expected argument formats, consider prompt composability, and test with various inputs.

### UI Integration for Prompts

Prompts can be surfaced in client UIs as slash commands, quick actions, context menu items, command palette entries, guided workflows, or interactive forms.

### Updates and Changes for Prompts

Servers can notify clients about prompt changes via the `notifications/prompts/list_changed` notification, prompting the client to re-fetch the prompt list.

### Security Considerations for Prompts

When implementing prompts, it is important to validate all arguments, sanitize user input, consider rate limiting, implement access controls, audit prompt usage, handle sensitive data appropriately, validate generated content, implement timeouts, and consider prompt injection risks.

## Roots

Roots are a concept in MCP that define the boundaries where servers can operate. They provide a way for clients to inform servers about relevant resources and their locations.

### What are Roots?

A root is a URI that a client suggests a server should focus on. While primarily used for filesystem paths, roots can be any valid URI, including HTTP URLs. Examples include `file:///home/user/projects/myapp` or `https://api.example.com/v1`.

### Why Use Roots?

Roots serve several important purposes:

1.  **Guidance**: They inform servers about relevant resources and locations.
2.  **Clarity**: Roots make it clear which resources are part of your workspace.
3.  **Organization**: Multiple roots allow working with different resources simultaneously.

### How Roots Work

When a client supports roots, it declares the `roots` capability during connection, provides a list of suggested roots to the server, and notifies the server when roots change (if supported). While roots are informational and not strictly enforcing, servers should respect the provided roots, use root URIs to locate and access resources, and prioritize operations within root boundaries.

### Common Use Cases for Roots

Roots are commonly used to define project directories, repository locations, API endpoints, configuration locations, and general resource boundaries.

### Best Practices for Roots

When working with roots, it is recommended to only suggest necessary resources, use clear and descriptive names for roots, monitor root accessibility, and handle root changes gracefully.

## Sampling

Sampling is an MCP feature that allows servers to request LLM completions through the client, enabling sophisticated agentic behaviors while maintaining security and privacy. This feature is not yet supported in the Claude Desktop client.

### How Sampling Works

The sampling flow involves several steps designed with a human-in-the-loop approach:

1.  Server sends a `sampling/createMessage` request to the client.
2.  Client reviews the request and can modify it.
3.  Client samples from an LLM.
4.  Client reviews the completion.
5.  Client returns the result to the server.

This design ensures users maintain control over what the LLM sees and generates.

### Message Format for Sampling Requests

Sampling requests use a standardized message format that includes:

*   `messages`: An array containing the conversation history, with each message having a `role` (user/assistant) and `content` (text or image).
*   `modelPreferences`: An optional object allowing servers to specify model selection preferences, including `hints` (suggested model names/families) and priority values for `costPriority`, `speedPriority`, and `intelligencePriority` (0-1 normalized).
*   `systemPrompt`: An optional field for requesting a specific system prompt, which the client may modify or ignore.
*   `includeContext`: Specifies what MCP context to include: `"none"`, `"thisServer"`, or `"allServers"`. The client controls what context is actually included.
*   Sampling parameters: `temperature` (randomness), `maxTokens` (maximum tokens to generate), `stopSequences` (sequences that stop generation), and `metadata` (additional provider-specific parameters).

### Response Format for Sampling

The client returns a completion result that includes the `model` name used, an optional `stopReason`, the `role` of the completion (user/assistant), and the `content` (text or image).

### Best Practices for Sampling

When implementing sampling, it is important to provide clear, well-structured prompts, handle both text and image content appropriately, set reasonable token limits, include relevant context, validate responses, handle errors gracefully, consider rate limiting, document expected behavior, test with various model parameters, and monitor sampling costs.

### Human in the Loop Controls for Sampling

Sampling is designed with human oversight:

*   **For prompts**: Clients should show users the proposed prompt, allow modification or rejection, filter or modify system prompts, and control context inclusion.
*   **For completions**: Clients should show users the completion, allow modification or rejection, filter or modify completions, and allow users to control which model is used.

### Security Considerations for Sampling

When implementing sampling, it is crucial to validate all message content, sanitize sensitive information, implement appropriate rate limits, monitor sampling usage, encrypt data in transit, handle user data privacy, audit sampling requests, control cost exposure, implement timeouts, and handle model errors gracefully.

### Common Patterns with Sampling

Sampling enables various agentic patterns, such as reading and analyzing resources, making decisions based on context, generating structured data, handling multi-step tasks, and providing interactive assistance. Best practices for context management include requesting minimal necessary context, structuring context clearly, handling size limits, updating context as needed, and cleaning up stale context. Robust error handling should catch sampling failures, handle timeout errors, manage rate limits, validate responses, provide fallback behaviors, and log errors appropriately.

### Limitations of Sampling

It is important to be aware that sampling depends on client capabilities, users control sampling behavior, context size has limits, rate limits may apply, costs should be considered, model availability varies, response times vary, and not all content types are supported.