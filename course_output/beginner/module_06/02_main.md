# Debugging and Development Tools for MCP

Effective debugging is essential when developing Model Context Protocol (MCP) servers or integrating them with applications. This guide covers the debugging tools and approaches available in the MCP ecosystem.

## Debugging Tools Overview

MCP provides several tools for debugging at different levels:

1.  **MCP Inspector**: An interactive debugging interface for direct server testing. It allows you to inspect resources, prompts, tools, and notifications.
2.  **Claude Desktop Developer Tools**: Used for integration testing, log collection, and leveraging Chrome DevTools for client-side debugging.
3.  **Server Logging**: Involves custom logging implementations within your server code for error tracking and performance monitoring.

## Debugging in Claude Desktop

### Checking Server Status

The Claude.app interface provides basic server status information:

*   Click the MCP plug icon (a plug symbol) to view connected servers and available prompts and resources.
*   Click the MCP hammer icon (a hammer symbol) to view tools made available to the model.

### Viewing Logs

Detailed MCP logs from Claude Desktop can be reviewed using the following command:

```bash
tail -n 20 -F ~/Library/Logs/Claude/mcp*.log
```

These logs capture server connection events, configuration issues, runtime errors, and message exchanges.

### Using Chrome DevTools

To access Chrome's developer tools inside Claude Desktop for client-side error investigation:

1.  Create a `developer_settings.json` file with `allowDevTools` set to `true`:

    ```bash
echo '{"allowDevTools": true}' > ~/Library/Application\ Support/Claude/developer_settings.json
    ```

2.  Open DevTools using `Command-Option-Shift-i`.

Note that you will typically see two DevTools windows: one for the main content and one for the app title bar. Use the Console panel to inspect client-side errors and the Network panel to inspect message payloads and connection timing.

## Common Issues

### Working Directory

When using MCP servers with Claude Desktop, the working directory for servers launched via `claude_desktop_config.json` may be undefined (e.g., `/` on macOS). Always use absolute paths in your configuration and `.env` files to ensure reliable operation. For example, in `claude_desktop_config.json`, use:

```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/username/data"]
}
```

Instead of relative paths like `./data`.

### Environment Variables

MCP servers inherit only a subset of environment variables automatically (e.g., `USER`, `HOME`, `PATH`). To override or provide additional variables, specify an `env` key in `claude_desktop_config.json`:

```json
{
  "myserver": {
    "command": "mcp-server-myapp",
    "env": {
      "MYAPP_API_KEY": "some_key"
    }
  }
}
```

### Server Initialization

Common initialization problems include:

*   **Path Issues**: Incorrect server executable path, missing required files, or permission problems. Try using an absolute path for the `command`.
*   **Configuration Errors**: Invalid JSON syntax, missing required fields, or type mismatches.
*   **Environment Problems**: Missing environment variables, incorrect variable values, or permission restrictions.

### Connection Problems

When servers fail to connect:

1.  Check Claude Desktop logs.
2.  Verify the server process is running.
3.  Test standalone with the MCP Inspector.
4.  Verify protocol compatibility.

## Implementing Logging

### Server-Side Logging

For servers using the local stdio transport, all messages logged to `stderr` (standard error) will be captured by the host application (e.g., Claude Desktop) automatically. Local MCP servers should **not** log messages to `stdout` (standard out), as this will interfere with protocol operation.

For all transports, you can also provide logging to the client by sending a log message notification:

**Python:**

```python
server.request_context.session.send_log_message(
  level="info",
  data="Server started successfully",
)
```

**TypeScript:**

```typescript
server.sendLoggingMessage({
  level: "info",
  data: "Server started successfully",
});
```

Important events to log include initialization steps, resource access, tool execution, error conditions, and performance metrics.

### Client-Side Logging

In client applications, enable debug logging, monitor network traffic, track message exchanges, and record error states.

## Debugging Workflow

### Development Cycle

1.  **Initial Development**: Use the MCP Inspector for basic testing, implement core functionality, and add logging points.
2.  **Integration Testing**: Test in Claude Desktop, monitor logs, and check error handling.

### Testing Changes

To test changes efficiently:

*   **Configuration changes**: Restart Claude Desktop.
*   **Server code changes**: Use `Command-R` to reload.
*   **Quick iteration**: Use the MCP Inspector during development.

## Best Practices

### Logging Strategy

1.  **Structured Logging**: Use consistent formats, include context, add timestamps, and track request IDs.
2.  **Error Handling**: Log stack traces, include error context, track error patterns, and monitor recovery.
3.  **Performance Tracking**: Log operation timing, monitor resource usage, track message sizes, and measure latency.

### Security Considerations

When debugging:

1.  **Sensitive Data**: Sanitize logs, protect credentials, and mask personal information.
2.  **Access Control**: Verify permissions, check authentication, and monitor access patterns.

## MCP Inspector

The MCP Inspector is an interactive developer tool for testing and debugging MCP servers. It runs directly through `npx` without requiring installation.

### Installation and Basic Usage

To run the Inspector:

```bash
npx @modelcontextprotocol/inspector <command>
```

#### Inspecting Servers from NPM or PyPi

**NPM package:**

```bash
npx -y @modelcontextprotocol/inspector npx <package-name> <args>
# For example
npx -y @modelcontextprotocol/inspector npx server-postgres postgres://127.0.0.1/testdb
```

**PyPi package:**

```bash
npx @modelcontextprotocol/inspector uvx <package-name> <args>
# For example
npx @modelcontextprotocol/inspector uvx mcp-server-git --repository ~/code/mcp/servers.git
```

#### Inspecting Locally Developed Servers

**TypeScript:**

```bash
npx @modelcontextprotocol/inspector node path/to/server/index.js args...
```

**Python:**

```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory path/to/server \
  run \
  package-name \
  args...
```

### Feature Overview

The Inspector provides several features for interacting with your MCP server:

*   **Server connection pane**: Allows selecting the transport and customizing command-line arguments and environment for local servers.
*   **Resources tab**: Lists available resources, shows metadata, allows content inspection, and supports subscription testing.
*   **Prompts tab**: Displays available prompt templates, shows arguments and descriptions, enables testing with custom arguments, and previews generated messages.
*   **Tools tab**: Lists available tools, shows schemas and descriptions, enables testing with custom inputs, and displays execution results.
*   **Notifications pane**: Presents all logs recorded from the server and shows notifications received from the server.

### Best Practices for Development Workflow with Inspector

1.  **Start Development**: Launch Inspector with your server, verify basic connectivity, and check capability negotiation.
2.  **Iterative Testing**: Make server changes, rebuild the server, reconnect the Inspector, test affected features, and monitor messages.
3.  **Test Edge Cases**: Test with invalid inputs, missing prompt arguments, and concurrent operations. Verify error handling and error responses.