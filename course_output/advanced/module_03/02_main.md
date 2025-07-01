# Core MCP Primitives: Enabling LLM Interactions

The Model Context Protocol (MCP) defines several core primitives that enable rich and dynamic interactions between servers, clients, and Large Language Models (LLMs). These primitives allow servers to expose data, functionality, and predefined interaction patterns, facilitating sophisticated LLM applications. This module will delve into five fundamental primitives: Resources, Tools, Prompts, Sampling, and Roots.

## 1. Resources: Exposing Data and Content

Resources are a fundamental MCP primitive that allows servers to expose various types of data and content to clients. These resources can then be used as context for LLM interactions. Resources are designed to be **application-controlled**, meaning the client application determines how and when they are used, often requiring explicit user selection.

### Overview of Resources

Resources represent any data an MCP server wishes to make available to clients. This can include diverse content such as file contents, database records, API responses, live system data, images, or log files. Each resource is uniquely identified by a URI and can contain either text or binary data.

### Resource URIs

Resources are identified using URIs following the format: `[protocol]://[host]/[path]`. Examples include `file:///home/user/documents/report.pdf` or `postgres://database/customers/schema`. The specific protocol and path structure are defined by the MCP server implementation, allowing for custom URI schemes.

### Resource Types

Resources can contain two primary types of content:
*   **Text Resources**: Contain UTF-8 encoded text data, suitable for source code, configuration files, log files, JSON/XML data, or plain text.
*   **Binary Resources**: Contain raw binary data, base64 encoded, suitable for images, PDFs, audio/video files, or other non-text formats.

### Resource Discovery

Clients can discover available resources through two main methods:
*   **Direct Resources**: Servers expose a list of concrete resources via the `resources/list` endpoint. Each resource includes a `uri`, `name`, optional `description`, and optional `mimeType`.
*   **Resource Templates**: For dynamic resources, servers can expose URI templates (following RFC 6570) that clients can use to construct valid resource URIs. These templates also include a `uriTemplate`, `name`, optional `description`, and optional `mimeType`.

### Reading Resources

To retrieve the content of a resource, clients send a `resources/read` request with the resource's URI. The server responds with a list of resource contents, which can include `text` for text resources or `blob` (base64 encoded) for binary resources, along with the `uri` and optional `mimeType`. Servers can return multiple resources in a single response, for example, when reading a directory.

### Resource Updates

MCP supports real-time updates for resources:
*   **List Changes**: Servers can notify clients when their list of available resources changes using the `notifications/resources/list_changed` notification.
*   **Content Changes**: Clients can subscribe to updates for specific resources via `resources/subscribe`. The server then sends `notifications/resources/updated` when the resource changes, prompting the client to fetch the latest content with `resources/read`. Clients can `resources/unsubscribe` when no longer needing updates.

### Best Practices for Resources

When implementing resource support, it's recommended to:
*   Use clear, descriptive names and URIs.
*   Include helpful descriptions and appropriate MIME types.
*   Implement resource templates for dynamic content.
*   Use subscriptions for frequently changing resources.
*   Handle errors gracefully and consider pagination for large lists.
*   Cache resource contents and validate URIs.
*   Document custom URI schemes.

### Security Considerations for Resources

Exposing resources requires careful security measures:
*   Validate all resource URIs and sanitize file paths to prevent directory traversal.
*   Implement appropriate access controls and be cautious with binary data.
*   Consider rate limiting for resource reads and audit resource access.
*   Encrypt sensitive data in transit and validate MIME types.
*   Implement timeouts for long-running reads and handle resource cleanup.

## 2. Tools: Enabling LLMs to Perform Actions

Tools are a powerful MCP primitive that allows servers to expose executable functionality to clients, enabling LLMs to interact with external systems, perform computations, and take actions in the real world. Tools are designed to be **model-controlled**, meaning they are exposed with the intention of the AI model automatically invoking them, typically with human approval.

### Overview of Tools

Tools represent executable functions that can be invoked by clients and utilized by LLMs. Key aspects include:
*   **Discovery**: Clients can list available tools via the `tools/list` endpoint.
*   **Invocation**: Tools are called using the `tools/call` endpoint, where the server performs the requested operation and returns results.
*   **Flexibility**: Tools can range from simple calculations to complex API interactions.

Unlike resources, tools represent dynamic operations that can modify state or interact with external systems.

### Tool Definition Structure

Each tool is defined with a `name` (unique identifier), an optional `description` (human-readable), and an `inputSchema` (a JSON Schema defining the tool's parameters).

### Implementing Tools

Servers define available tools and handle their execution. For example, a `calculate_sum` tool would define `a` and `b` as number inputs in its `inputSchema` and then perform the addition when called.

### Example Tool Patterns

Servers can provide various types of tools:
*   **System Operations**: Tools that interact with the local system, e.g., `execute_command` to run a shell command.
*   **API Integrations**: Tools that wrap external APIs, e.g., `github_create_issue` to create a GitHub issue.
*   **Data Processing**: Tools that transform or analyze data, e.g., `analyze_csv` to perform operations like sum or average on a CSV file.

### Best Practices for Tools

When implementing tools, it's important to:
*   Provide clear, descriptive names and descriptions, including examples in descriptions.
*   Use detailed JSON Schema definitions for parameters.
*   Implement proper error handling, validation, and timeouts.
*   Use progress reporting for long operations and keep tool operations focused and atomic.
*   Document expected return value structures and consider rate limiting.
*   Log tool usage for debugging and monitoring.

### Security Considerations for Tools

Exposing tools requires robust security measures:
*   **Input Validation**: Validate all parameters against the schema, sanitize file paths and system commands, validate URLs, check parameter sizes, and prevent command injection.
*   **Access Control**: Implement authentication and authorization checks, audit tool usage, rate limit requests, and monitor for abuse.
*   **Error Handling**: Avoid exposing internal errors, log security-relevant errors, handle timeouts, and clean up resources after errors.

### Tool Discovery and Updates

MCP supports dynamic tool discovery. Clients can list available tools at any time, and servers can notify clients of changes using `notifications/tools/list_changed`. Tools can be added, removed, or updated during runtime.

### Error Handling for Tools

Tool errors should be reported within the result object of the `tools/call` response, not as MCP protocol-level errors. This allows the LLM to see and potentially handle the error. When an error occurs, the `isError` field in the result should be set to `true`, and error details included in the `content` array.

### Testing Tools

A comprehensive testing strategy for MCP tools should cover functional testing, integration testing, security testing, performance testing, and error handling.

## 3. Prompts: Creating Reusable Templates

Prompts enable servers to define reusable prompt templates and workflows that clients can easily surface to users and LLMs. They provide a powerful way to standardize and share common LLM interactions. Prompts are designed to be **user-controlled**, meaning they are exposed with the intention of the user explicitly selecting them for use.

### Overview of Prompts

Prompts in MCP are predefined templates that can:
*   Accept dynamic arguments.
*   Include context from resources.
*   Chain multiple interactions.
*   Guide specific workflows.
*   Be surfaced as UI elements (e.g., slash commands).

### Prompt Structure

Each prompt is defined with a `name` (unique identifier), an optional `description`, and an optional `arguments` list. Each argument has a `name`, optional `description`, and a `required` flag.

### Discovering and Using Prompts

Clients discover available prompts through the `prompts/list` endpoint, which returns a list of prompt definitions. To use a prompt, clients make a `prompts/get` request, providing the prompt's `name` and any required `arguments`. The server then responds with a `description` and a `messages` array, which represents the pre-filled conversation history for the LLM.

### Dynamic Prompts

Prompts can be dynamic and include:
*   **Embedded Resource Context**: Prompts can dynamically fetch and embed content from resources into the LLM's message history. For example, a prompt to "analyze-project" might take `timeframe` and `fileUri` arguments, then embed relevant log files and code content as resources in the messages.
*   **Multi-step Workflows**: Prompts can define multi-turn conversations or workflows, providing initial user and assistant messages to guide the interaction.

### Best Practices for Prompts

When implementing prompts, it's advisable to:
*   Use clear, descriptive names and provide detailed descriptions for prompts and arguments.
*   Validate all required arguments and handle missing ones gracefully.
*   Consider versioning for prompt templates and cache dynamic content.
*   Implement error handling and document expected argument formats.
*   Consider prompt composability and test prompts with various inputs.

### UI Integration for Prompts

Prompts can be surfaced in client UIs in various ways, such as slash commands, quick actions, context menu items, command palette entries, guided workflows, or interactive forms.

### Updates and Changes for Prompts

Servers can notify clients about prompt changes using the `notifications/prompts/list_changed` notification, prompting the client to re-fetch the updated prompt list.

### Security Considerations for Prompts

Implementing prompts requires security awareness:
*   Validate all arguments and sanitize user input.
*   Consider rate limiting and implement access controls.
*   Audit prompt usage and handle sensitive data appropriately.
*   Validate generated content and implement timeouts.
*   Consider prompt injection risks and document security requirements.

## 4. Sampling: Requesting LLM Completions

Sampling is an MCP feature that allows servers to request LLM completions through the client. This enables sophisticated agentic behaviors while maintaining security and privacy through a human-in-the-loop design.

### How Sampling Works

The sampling flow involves several steps, emphasizing human oversight:
1.  **Server Request**: The server sends a `sampling/createMessage` request to the client.
2.  **Client Review & Modification**: The client reviews the request and can modify it.
3.  **LLM Sampling**: The client samples from an LLM.
4.  **Client Review & Modification**: The client reviews the completion.
5.  **Result Return**: The client returns the result to the server.

This design ensures users maintain control over what the LLM sees and generates.

### Message Format for Sampling Requests

Sampling requests use a standardized message format, including:
*   **`messages`**: An array of conversation history, with each message having a `role` ("user" or "assistant") and `content` (text or image).
*   **`modelPreferences`**: An optional object allowing servers to specify model selection preferences, including `hints` (suggested model names/families) and priority values (0-1 normalized) for `costPriority`, `speedPriority`, and `intelligencePriority`. Clients make the final model selection.
*   **`systemPrompt`**: An optional field for a specific system prompt, which the client may modify or ignore.
*   **`includeContext`**: Specifies what MCP context to include: `"none"`, `"thisServer"`, or `"allServers"`. The client ultimately controls context inclusion.
*   **Sampling Parameters**: `temperature` (randomness), `maxTokens` (maximum tokens to generate), `stopSequences` (sequences that stop generation), and `metadata` (additional provider-specific parameters).

### Response Format for Sampling

The client returns a completion result including the `model` used, `stopReason`, `role` ("user" or "assistant"), and the `content` (text or image) of the completion.

### Best Practices for Sampling

When implementing sampling, it's recommended to:
*   Always provide clear, well-structured prompts.
*   Handle both text and image content appropriately.
*   Set reasonable token limits and include relevant context.
*   Validate responses and handle errors gracefully.
*   Consider rate limiting sampling requests and document expected behavior.
*   Test with various model parameters and monitor sampling costs.

### Human-in-the-Loop Controls

Sampling is designed with human oversight:
*   **For Prompts**: Clients should show users the proposed prompt, allow modification or rejection, and control system prompt filtering/modification and context inclusion.
*   **For Completions**: Clients should show users the completion, allow modification or rejection, filter/modify completions, and allow users to control which model is used.

### Security Considerations for Sampling

Implementing sampling requires robust security:
*   Validate all message content and sanitize sensitive information.
*   Implement appropriate rate limits and monitor sampling usage.
*   Encrypt data in transit and handle user data privacy.
*   Audit sampling requests, control cost exposure, and implement timeouts.
*   Handle model errors gracefully.

### Common Patterns and Limitations

Sampling enables agentic workflows (e.g., reading resources, making decisions, handling multi-step tasks). Best practices for context management include requesting minimal context, structuring it clearly, and handling size limits. Robust error handling involves catching failures, managing rate limits, validating responses, and providing fallbacks.

Limitations include dependence on client capabilities, user control over behavior, context size limits, potential rate limits, cost considerations, and variations in model availability and response times.

## 5. Roots: Defining Operational Boundaries

Roots are a concept in MCP that define the operational boundaries for servers. They provide a way for clients to inform servers about relevant resources and their locations, guiding the server's focus.

### What are Roots?

A root is a URI that a client suggests a server should focus on. While primarily used for filesystem paths, roots can be any valid URI, such as `file:///home/user/projects/myapp` or `https://api.example.com/v1`.

### Why Use Roots?

Roots serve several important purposes:
*   **Guidance**: They inform servers about relevant resources and locations.
*   **Clarity**: Roots make it clear which resources are part of your workspace.
*   **Organization**: Multiple roots allow working with different resources simultaneously.

### How Roots Work

When a client supports roots, it:
1.  Declares the `roots` capability during connection.
2.  Provides a list of suggested roots to the server.
3.  Notifies the server when roots change (if supported).

While roots are informational and not strictly enforcing, servers should respect the provided roots, use root URIs to locate and access resources, and prioritize operations within these boundaries.

### Common Use Cases for Roots

Roots are commonly used to define:
*   Project directories
*   Repository locations
*   API endpoints
*   Configuration locations
*   Resource boundaries

### Best Practices for Roots

When working with roots, it's recommended to:
*   Only suggest necessary resources.
*   Use clear, descriptive names for roots.
*   Monitor root accessibility.
*   Handle root changes gracefully.

An example configuration might include a local frontend repository and an API endpoint, keeping them logically separated for the server.