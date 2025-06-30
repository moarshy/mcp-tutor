# Roots

Roots are a fundamental concept within the Model Context Protocol (MCP) that establish the operational boundaries for servers. They serve as a mechanism for clients to communicate to servers which resources and locations are relevant for their operations.

## What are Roots?

A root is defined as a Uniform Resource Identifier (URI) that a client suggests a server should concentrate its operations on. When a client establishes a connection with a server, it explicitly declares the roots that the server is expected to work with. While roots are frequently utilized for specifying filesystem paths, their definition is flexible enough to encompass any valid URI, including HTTP URLs.

Examples of roots include:

*   `file:///home/user/projects/myapp` (a local filesystem path)
*   `https://api.example.com/v1` (an HTTP API endpoint)

## Why Use Roots?

Roots fulfill several critical functions within the MCP framework, enhancing the interaction between clients and servers:

1.  **Guidance**: They provide clear direction to servers regarding the pertinent resources and their locations that are part of the client's current context.
2.  **Clarity**: Roots explicitly delineate which resources are considered part of a client's workspace, reducing ambiguity for the server.
3.  **Organization**: The ability to define multiple roots allows clients to manage and work with diverse sets of resources concurrently, maintaining logical separation.

## How Roots Work

The interaction with roots involves specific behaviors from both clients and servers:

When a client is designed to support the concept of roots, it performs the following actions:

1.  **Capability Declaration**: During the initial connection phase, the client declares its `roots` capability to the server.
2.  **Root Provision**: The client then furnishes the server with a list of suggested roots.
3.  **Change Notification**: If the client supports dynamic root management, it will notify the server when the list of roots changes.

Although roots are primarily informational and do not enforce strict operational boundaries, servers are expected to:

1.  **Respect Boundaries**: Servers should acknowledge and respect the roots provided by the client.
2.  **Resource Location**: Servers should utilize the provided root URIs to accurately locate and access necessary resources.
3.  **Operational Prioritization**: Servers should prioritize their operations within the boundaries defined by the declared roots.

## Common Use Cases

Roots are versatile and are commonly employed to define various types of operational contexts or resource boundaries, such as:

*   **Project Directories**: Specifying the main directory of a software project.
*   **Repository Locations**: Indicating the local path of a code repository.
*   **API Endpoints**: Defining the base URL for an external API.
*   **Configuration Locations**: Pointing to directories or files containing application configurations.
*   **Resource Boundaries**: Generally outlining the scope of resources a server should consider.

## Best Practices

To ensure effective and efficient use of roots, consider the following best practices:

1.  **Suggest Only Necessary Resources**: Limit the roots provided to only those resources that are genuinely required for the server's current operations.
2.  **Use Clear, Descriptive Names**: Assign meaningful and easily understandable names to roots to improve clarity and organization.
3.  **Monitor Root Accessibility**: Clients should ensure that the resources pointed to by roots remain accessible to the server.
4.  **Handle Root Changes Gracefully**: Implement mechanisms to properly manage and communicate changes to the root list, allowing the server to adapt smoothly.

## Example

The following JSON structure illustrates how a typical MCP client might expose its roots to a server:

```json
{
  "roots": [
    {
      "uri": "file:///home/user/projects/frontend",
      "name": "Frontend Repository"
    },
    {
      "uri": "https://api.example.com/v1",
      "name": "API Endpoint"
    }
  ]
}
```

This example demonstrates how a client can suggest that a server should focus its attention on both a local filesystem path representing a frontend repository and an external API endpoint, while maintaining a clear logical separation between these distinct resource sets.