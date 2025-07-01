# Building MCP Servers

This module provides practical guidance on developing your own Model Context Protocol (MCP) servers. You will learn how to set up a development environment, implement core MCP capabilities like exposing resources, defining and executing tools, and creating prompt templates. The module emphasizes best practices for server implementation, including error handling and security considerations, and guides you through connecting and testing your server with an MCP host like Claude for Desktop.

## Introduction to MCP Servers

The Model Context Protocol (MCP) is built on a flexible, extensible architecture that enables seamless communication between LLM applications and integrations. MCP follows a client-server architecture where **Hosts** (LLM applications like Claude Desktop) initiate connections, **Clients** maintain 1:1 connections with servers inside the host application, and **Servers** provide context, tools, and prompts to clients.

MCP servers can provide three main types of capabilities:
1.  **Resources**: File-like data that can be read by clients (e.g., API responses, file contents).
2.  **Tools**: Functions that can be called by the LLM (with user approval) to interact with external systems or perform computations.
3.  **Prompts**: Pre-written templates that help users accomplish specific tasks, often surfacing as UI elements.

## Core MCP Concepts

MCP servers communicate using JSON-RPC 2.0 over various transport layers. The communication lifecycle involves initialization, message exchange (requests, responses, notifications), and termination.

### Protocol Layer
The protocol layer handles message framing, request/response linking, and high-level communication patterns. Key classes in SDKs (e.g., `Protocol`, `Client`, `Server`) manage sending requests, notifications, and setting handlers for incoming messages.

### Transport Layer
The transport layer handles the actual communication. MCP supports:
*   **Stdio transport**: Uses standard input/output for communication, ideal for local processes.
*   **HTTP with SSE transport**: Uses Server-Sent Events for server-to-client messages and HTTP POST for client-to-server messages, suitable for remote communication.

### Message Types
MCP defines four main message types:
*   **Requests**: Expect a response from the other side.
*   **Results**: Successful responses to requests.
*   **Errors**: Indicate a failed request.
*   **Notifications**: One-way messages that do not expect a response.

### Connection Lifecycle
1.  **Initialization**: Client sends an `initialize` request, server responds with capabilities, and client sends an `initialized` notification.
2.  **Message Exchange**: Normal request-response and notification patterns begin.
3.  **Termination**: Either party can terminate the connection gracefully or due to errors.

### Error Handling
MCP defines standard JSON-RPC error codes (e.g., ParseError, InvalidRequest, MethodNotFound). SDKs and applications can define custom error codes. Errors are propagated via error responses, transport error events, or protocol-level error handlers.

## Exposing Capabilities: Resources, Tools, and Prompts

MCP servers expose data and functionality through Resources, Tools, and Prompts.

### Resources
Resources allow servers to expose data and content that clients can read and use as context for LLM interactions. They are **application-controlled**, meaning the client decides how and when to use them.

*   **Identification**: Each resource is identified by a unique URI (e.g., `file:///home/user/documents/report.pdf`).
*   **Content Types**: Can be text (UTF-8 encoded) or binary (base64 encoded).
*   **Discovery**: Clients can discover resources via `resources/list` (for concrete resources) or through URI templates (for dynamic resources).
*   **Reading**: Clients make a `resources/read` request to get content.
*   **Updates**: Servers can notify clients of list changes (`notifications/resources/list_changed`) or content changes (`notifications/resources/updated`) for subscribed resources.

#### Example Resource Implementation
<Tabs>
  <Tab title="TypeScript">
    ```typescript
    const server = new Server({
      name: "example-server",
      version: "1.0.0"
    }, {
      capabilities: {
        resources: {}
      }
    });

    // List available resources
    server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [
          {
            uri: "file:///logs/app.log",
            name: "Application Logs",
            mimeType: "text/plain"
          }
        ]
      };
    });

    // Read resource contents
    server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const uri = request.params.uri;
      if (uri === "file:///logs/app.log") {
        const logContents = await readLogFile(); // Assume readLogFile() exists
        return {
          contents: [
            {
              uri,
              mimeType: "text/plain",
              text: logContents
            }
          ]
        };
      }
      throw new Error("Resource not found");
    });
    ```
  </Tab>
  <Tab title="Python">
    ```python
    app = Server("example-server")

    @app.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri="file:///logs/app.log",
                name="Application Logs",
                mimeType="text/plain"
            )
        ]

    @app.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        if str(uri) == "file:///logs/app.log":
            log_contents = await read_log_file() # Assume read_log_file() exists
            return log_contents
        raise ValueError("Resource not found")
    ```
  </Tab>
</Tabs>

### Tools
Tools enable servers to expose executable functionality to clients, allowing LLMs to interact with external systems, perform computations, and take actions. Tools are **model-controlled**, meaning the AI model can automatically invoke them (with human approval).

*   **Definition**: Each tool has a `name`, `description`, and `inputSchema` (JSON Schema for parameters).
*   **Discovery**: Clients list available tools via the `tools/list` endpoint.
*   **Invocation**: Tools are called using the `tools/call` endpoint.
*   **Error Handling**: Tool errors should be reported within the result object (with `isError: true`) rather than as protocol-level errors, allowing the LLM to handle them.

### Prompts
Prompts allow servers to define reusable prompt templates and workflows that clients can surface to users and LLMs. They are **user-controlled**, meaning the user explicitly selects them for use.

*   **Structure**: Defined with a `name`, `description`, and optional `arguments`.
*   **Discovery**: Clients discover prompts via the `prompts/list` endpoint.
*   **Usage**: Clients make a `prompts/get` request with arguments to retrieve the formatted prompt messages.
*   **Dynamic Prompts**: Can include embedded resource context or define multi-step workflows.
*   **UI Integration**: Can be surfaced as slash commands, quick actions, or other UI elements.
*   **Updates**: Servers can notify clients of prompt list changes via `notifications/prompts/list_changed`.

#### Example Prompt Implementation
<Tabs>
  <Tab title="TypeScript">
    ```typescript
    import { Server } from "@modelcontextprotocol/sdk/server";
    import { ListPromptsRequestSchema, GetPromptRequestSchema } from "@modelcontextprotocol/sdk/types";

    const PROMPTS = {
      "git-commit": { /* ... definition ... */ },
      "explain-code": { /* ... definition ... */ }
    };

    const server = new Server({
      name: "example-prompts-server",
      version: "1.0.0"
    }, {
      capabilities: { prompts: {} }
    });

    server.setRequestHandler(ListPromptsRequestSchema, async () => {
      return { prompts: Object.values(PROMPTS) };
    });

    server.setRequestHandler(GetPromptRequestSchema, async (request) => {
      const prompt = PROMPTS[request.params.name];
      if (!prompt) throw new Error(`Prompt not found: ${request.params.name}`);

      if (request.params.name === "git-commit") {
        return {
          messages: [{ role: "user", content: { type: "text", text: `Generate a concise but descriptive commit message for these changes:\n\n${request.params.arguments?.changes}` } }]
        };
      }
      // ... other prompt implementations
      throw new Error("Prompt implementation not found");
    });
    ```
  </Tab>
  <Tab title="Python">
    ```python
    from mcp.server import Server
    import mcp.types as types

    PROMPTS = {
        "git-commit": types.Prompt(name="git-commit", description="Generate a Git commit message", arguments=[types.PromptArgument(name="changes", description="Git diff or description of changes", required=True)]),
        "explain-code": types.Prompt(name="explain-code", description="Explain how code works", arguments=[types.PromptArgument(name="code", description="Code to explain", required=True), types.PromptArgument(name="language", description="Programming language", required=False)])
    }

    app = Server("example-prompts-server")

    @app.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return list(PROMPTS.values())

    @app.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> types.GetPromptResult:
        if name not in PROMPTS: raise ValueError(f"Prompt not found: {name}")
        if name == "git-commit":
            changes = arguments.get("changes") if arguments else ""
            return types.GetPromptResult(messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=f"Generate a concise but descriptive commit message for these changes:\n\n{changes}"))])
        # ... other prompt implementations
        raise ValueError("Prompt implementation not found")
    ```
  </Tab>
</Tabs>

## Building a Weather Server: A Practical Example

This section walks through building a simple MCP weather server that exposes `get-alerts` and `get-forecast` tools.

### Prerequisite Knowledge
*   Familiarity with your chosen programming language (Python, Node.js, Java, C#).
*   Basic understanding of LLMs.

### System Requirements
*   **Python**: Python 3.10+ and MCP SDK 1.2.0+
*   **Node.js**: Node.js 16+
*   **Java**: Java 17+ and Spring Boot 3.3.x+ (for Spring AI starter)
*   **C#**: .NET 8 SDK+

### Set Up Your Environment

#### Python
1.  Install `uv`:
    <CodeGroup>
    ```bash MacOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    ```powershell Windows
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
    </CodeGroup>
    Restart your terminal.
2.  Create and set up project:
    <CodeGroup>
    ```bash MacOS/Linux
    uv init weather
    cd weather
    uv venv
    source .venv/bin/activate
    uv add "mcp[cli]" httpx
    touch weather.py
    ```
    ```powershell Windows
    uv init weather
    cd weather
    uv venv
    .venv\Scripts\activate
    uv add mcp[cli] httpx
    new-item weather.py
    ```
    </CodeGroup>

#### Node.js
1.  Install Node.js and npm from [nodejs.org](https://nodejs.org/).
2.  Create and set up project:
    <CodeGroup>
    ```bash MacOS/Linux
    mkdir weather
    cd weather
    npm init -y
    npm install @modelcontextprotocol/sdk zod
    npm install -D @types/node typescript
    mkdir src
    touch src/index.ts
    ```
    ```powershell Windows
    md weather
    cd weather
    npm init -y
    npm install @modelcontextprotocol/sdk zod
    npm install -D @types/node typescript
    md src
    new-item src\index.ts
    ```
    </CodeGroup>
3.  Update `package.json` (add `"type": "module"`, `"bin"`, `"scripts"`).
4.  Create `tsconfig.json` in the root.

#### Java
1.  Install Java 17+ and Spring Boot 3.3.x+.
2.  Use [Spring Initializer](https://start.spring.io/) to bootstrap the project.
3.  Add dependencies (Maven or Gradle):
    <Tabs>
      <Tab title="Maven">
      ```xml
      <dependencies>
            <dependency>
                <groupId>org.springframework.ai</groupId>
                <artifactId>spring-ai-starter-mcp-server</artifactId>
            </dependency>
            <dependency>
                <groupId>org.springframework</groupId>
                <artifactId>spring-web</artifactId>
            </dependency>
      </dependencies>
      ```
      </Tab>
      <Tab title="Gradle">
      ```groovy
      dependencies {
        implementation platform("org.springframework.ai:spring-ai-starter-mcp-server")
        implementation platform("org.springframework:spring-web")   
      }
      ```
      </Tab>
    </Tabs>
4.  Configure `application.properties` or `application.yml`.

#### C#
1.  Install .NET 8 SDK+.
2.  Create and set up project:
    <CodeGroup>
    ```bash MacOS/Linux
    mkdir weather
    cd weather
    dotnet new console
    ```
    ```powershell Windows
    mkdir weather
    cd weather
    dotnet new console
    ```
    </CodeGroup>
3.  Add NuGet packages:
    ```bash
    dotnet add package ModelContextProtocol --prerelease
    dotnet add package Microsoft.Extensions.Hosting
    ```

### Implementing Tool Execution (Weather Server)

The weather server will implement two tools: `get-alerts` and `get-forecast` using the National Weather Service (NWS) API.

#### Python Implementation
Add the following to `weather.py`:
```python
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import mcp.types as types # For call_tool example

mcp = FastMCP("weather")
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state. Args: state: Two-letter US state code (e.g. CA, NY)"""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    if not data or "features" not in data or not data["features"]:
        return "Unable to fetch alerts or no alerts found."
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location. Args: latitude: Latitude, longitude: Longitude"""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    if not points_data: return "Unable to fetch forecast data for this location."
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data: return "Unable to fetch detailed forecast."
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecasts.append(f"""
{period['name']}: Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
""")
    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

#### Node.js Implementation
Add the following to `src/index.ts`:
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const NWS_API_BASE = "https://api.weather.gov";
const USER_AGENT = "weather-app/1.0";

const server = new McpServer({
  name: "weather",
  version: "1.0.0",
  capabilities: { resources: {}, tools: {} },
});

async function makeNWSRequest<T>(url: string): Promise<T | null> {
  const headers = { "User-Agent": USER_AGENT, Accept: "application/geo+json" };
  try {
    const response = await fetch(url, { headers });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return (await response.json()) as T;
  } catch (error) {
    console.error("Error making NWS request:", error);
    return null;
  }
}

interface AlertFeature { properties: { event?: string; areaDesc?: string; severity?: string; status?: string; headline?: string; }; }
function formatAlert(feature: AlertFeature): string {
  const props = feature.properties;
  return [`Event: ${props.event || "Unknown"}`, `Area: ${props.areaDesc || "Unknown"}`, `Severity: ${props.severity || "Unknown"}`, `Status: ${props.status || "Unknown"}`, `Headline: ${props.headline || "No headline"}`, "---",].join("\n");
}

server.tool(
  "get-alerts", "Get weather alerts for a state",
  { state: z.string().length(2).describe("Two-letter state code (e.g. CA, NY)") },
  async ({ state }) => {
    const alertsData = await makeNWSRequest<any>(`${NWS_API_BASE}/alerts?area=${state.toUpperCase()}`);
    if (!alertsData || !alertsData.features || alertsData.features.length === 0) return { content: [{ type: "text", text: "No active alerts for this state." }] };
    const formattedAlerts = alertsData.features.map(formatAlert);
    return { content: [{ type: "text", text: `Active alerts for ${state.toUpperCase()}:\n\n${formattedAlerts.join("\n")}` }] };
  },
);

server.tool(
  "get-forecast", "Get weather forecast for a location",
  { latitude: z.number().min(-90).max(90).describe("Latitude"), longitude: z.number().min(-180).max(180).describe("Longitude") },
  async ({ latitude, longitude }) => {
    const pointsData = await makeNWSRequest<any>(`${NWS_API_BASE}/points/${latitude.toFixed(4)},${longitude.toFixed(4)}`);
    if (!pointsData || !pointsData.properties?.forecast) return { content: [{ type: "text", text: "Failed to retrieve forecast URL." }] };
    const forecastData = await makeNWSRequest<any>(pointsData.properties.forecast);
    if (!forecastData || !forecastData.properties?.periods || forecastData.properties.periods.length === 0) return { content: [{ type: "text", text: "No forecast periods available." }] };
    const formattedForecast = forecastData.properties.periods.map((period: any) =>
      [`${period.name || "Unknown"}:`, `Temperature: ${period.temperature || "Unknown"}°${period.temperatureUnit || "F"}`, `Wind: ${period.windSpeed || "Unknown"} ${period.windDirection || ""}`, `${period.shortForecast || "No forecast available"}`, "---",].join("\n"),
    );
    return { content: [{ type: "text", text: `Forecast for ${latitude}, ${longitude}:\n\n${formattedForecast.join("\n")}` }] };
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Weather MCP Server running on stdio");
}
main().catch((error) => { console.error("Fatal error in main():", error); process.exit(1); });
```
Run `npm run build` after implementing.

#### Java Implementation (Spring AI Starter)
Create `WeatherService.java` and your Spring Boot application:
```java
// WeatherService.java
@Service
public class WeatherService {
    private final RestClient restClient;
    public WeatherService() {
        this.restClient = RestClient.builder()
            .baseUrl("https://api.weather.gov")
            .defaultHeader("Accept", "application/geo+json")
            .defaultHeader("User-Agent", "WeatherApiClient/1.0 (your@email.com)")
            .build();
    }

    @Tool(description = "Get weather forecast for a specific latitude/longitude")
    public String getWeatherForecastByLocation(double latitude, double longitude) { /* ... implementation ... */ }
    
    @Tool(description = "Get weather alerts for a US state")
    public String getAlerts(@ToolParam(description = "Two-letter US state code (e.g. CA, NY)") String state) { /* ... implementation ... */ }
}

// McpServerApplication.java
@SpringBootApplication
public class McpServerApplication {
    public static void main(String[] args) { SpringApplication.run(McpServerApplication.class, args); }
    @Bean
    public ToolCallbackProvider weatherTools(WeatherService weatherService) {
        return MethodToolCallbackProvider.builder().toolObjects(weatherService).build();
    }
}
```
Build the server: `./mvnw clean install` (Maven) or `./gradlew build` (Gradle).

#### C# Implementation
Open `Program.cs` and add the following:
```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using ModelContextProtocol;
using System.Net.Http.Headers;
using System.ComponentModel;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading.Tasks;

var builder = Host.CreateEmptyApplicationBuilder(settings: null);

builder.Services.AddMcpServer()
    .WithStdioServerTransport()
    .WithToolsFromAssembly();

builder.Services.AddSingleton(_ =>
{
    var client = new HttpClient() { BaseAddress = new Uri("https://api.weather.gov") };
    client.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("weather-tool", "1.0"));
    return client;
});

var app = builder.Build();

await app.RunAsync();

namespace QuickstartWeatherServer.Tools;

[McpServerToolType]
public static class WeatherTools
{
    [McpServerTool, Description("Get weather alerts for a US state.")]
    public static async Task<string> GetAlerts(
        HttpClient client,
        [Description("The US state to get alerts for.")] string state)
    {
        var jsonElement = await client.GetFromJsonAsync<JsonElement>($"/alerts/active/area/{state}");
        var alerts = jsonElement.GetProperty("features").EnumerateArray();
        if (!alerts.Any()) return "No active alerts for this state.";
        return string.Join("\n--\n", alerts.Select(alert =>
        {
            JsonElement properties = alert.GetProperty("properties");
            return $"""
                    Event: {properties.GetProperty("event").GetString()}
                    Area: {properties.GetProperty("areaDesc").GetString()}
                    Severity: {properties.GetProperty("severity").GetString()}
                    Description: {properties.GetProperty("description").GetString()}
                    Instruction: {properties.GetProperty("instruction").GetString()}
                    """;
        }));
    }

    [McpServerTool, Description("Get weather forecast for a location.")]
    public static async Task<string> GetForecast(
        HttpClient client,
        [Description("Latitude of the location.")] double latitude,
        [Description("Longitude of the location.")] double longitude)
    {
        var jsonElement = await client.GetFromJsonAsync<JsonElement>($"/points/{latitude},{longitude}");
        var periods = jsonElement.GetProperty("properties").GetProperty("periods").EnumerateArray();
        return string.Join("\n---\n", periods.Select(period => $"""
                {period.GetProperty("name").GetString()}
                Temperature: {period.GetProperty("temperature").GetInt32()}°F
                Wind: {period.GetProperty("windSpeed").GetString()} {period.GetProperty("windDirection").GetString()}
                Forecast: {period.GetProperty("detailedForecast").GetString()}
                """));
    }
}
```
Run the server: `dotnet run`.

## Integrating Sampling

Sampling is an MCP feature that allows servers to request LLM completions through the client, enabling sophisticated agentic behaviors. This feature is not yet supported in Claude Desktop.

The sampling flow:
1.  Server sends `sampling/createMessage` request to the client.
2.  Client reviews and can modify the request.
3.  Client samples from an LLM.
4.  Client reviews the completion.
5.  Client returns the result to the server.

This "human-in-the-loop" design ensures user control.

### Message Format
Sampling requests use a standardized message format including `messages` (conversation history), `modelPreferences` (hints, cost/speed/intelligence priority), `systemPrompt`, `includeContext` (none, thisServer, allServers), `temperature`, `maxTokens`, `stopSequences`, and `metadata`.

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

## Connecting and Testing with Claude for Desktop

To test your MCP server, you'll configure Claude for Desktop to launch it.

1.  **Install/Update Claude for Desktop**: Download the latest version from [claude.ai/download](https://claude.ai/download).
2.  **Configure `claude_desktop_config.json`**: Open this file in a text editor.
    *   **MacOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
    *   **Windows**: `$env:AppData\Claude\claude_desktop_config.json`
    Create the file if it doesn't exist.
3.  **Add your server configuration**: Add your server under the `mcpServers` key. **Ensure you use the absolute path to your project/executable.**

<Tabs>
<Tab title="Python">
```json
{
    "mcpServers": {
        "weather": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/weather",
                "run",
                "weather.py"
            ]
        }
    }
}
```
</Tab>
<Tab title="Node">
```json
{
    "mcpServers": {
        "weather": {
            "command": "node",
            "args": [
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/weather/build/index.js"
            ]
        }
    }
}
```
</Tab>
<Tab title="Java">
```json
{
    "mcpServers": {
      "spring-ai-mcp-weather": {
        "command": "java",
        "args": [
          "-Dspring.ai.mcp.server.stdio=true",
          "-jar",
          "/ABSOLUTE/PATH/TO/PARENT/FOLDER/mcp-weather-stdio-server-0.0.1-SNAPSHOT.jar"
        ]
      }
    }
}
```
</Tab>
<Tab title="C#">
```json
{
    "mcpServers": {
        "weather": {
            "command": "dotnet",
            "args": [
                "run",
                "--project",
                "/ABSOLUTE/PATH/TO/PROJECT",
                "--no-build"
            ]
        }
    }
}
```
</Tab>
</Tabs>

4.  **Save and Restart Claude for Desktop**.

### Test with Commands
Look for the hammer icon <img src="/images/claude-desktop-mcp-hammer-icon.svg" style={{display: 'inline', margin: 0, height: '1.3em'}} /> in Claude for Desktop, which indicates MCP tools are available. Click it to see your exposed tools.

Then, test your weather server with commands like:
*   "What's the weather in Sacramento?"
*   "What are the active weather alerts in Texas?"

## What's Happening Under the Hood
When you ask a question:
1.  The client sends your question to Claude.
2.  Claude analyzes available tools and decides which to use.
3.  The client executes the chosen tool(s) through your MCP server.
4.  The results are sent back to Claude.
5.  Claude formulates a natural language response.
6.  The response is displayed to you.

## Troubleshooting

### Claude for Desktop Integration Issues
*   **Getting logs**: Claude.app logs related to MCP are in `~/Library/Logs/Claude/mcp.log` and `mcp-server-SERVERNAME.log`. Use `tail -n 20 -f ~/Library/Logs/Claude/mcp*.log` to monitor.
*   **Server not showing up**: Check `claude_desktop_config.json` syntax, ensure absolute paths, and restart Claude for Desktop completely.
*   **Tool calls failing silently**: Check Claude's logs, verify your server builds and runs without errors, and restart Claude for Desktop.
*   For more advanced debugging, refer to the [Debugging MCP guide](/docs/tools/debugging).

### Weather API Issues
*   **Error: Failed to retrieve grid point data**: Usually means coordinates are outside the US, NWS API issues, or rate limiting. Verify US coordinates, add delays, or check NWS API status.
*   **Error: No active alerts for [STATE]**: This is not an error; it means no current alerts for that state.

## Best Practices for MCP Server Development

### Transport Selection
*   **Local communication**: Use stdio transport for efficiency and simple process management.
*   **Remote communication**: Use SSE for HTTP compatibility, but consider security implications (authentication, authorization).

### Message Handling
*   **Request processing**: Validate inputs, use type-safe schemas, handle errors gracefully, implement timeouts.
*   **Progress reporting**: Use progress tokens for long operations, report incrementally.
*   **Error management**: Use appropriate error codes, include helpful messages, clean up resources.

### Security Considerations
*   **Transport security**: Use TLS for remote connections, validate origins, implement authentication.
*   **Message validation**: Validate all incoming messages, sanitize inputs, check size limits, verify JSON-RPC format.
*   **Resource protection**: Implement access controls, validate resource paths, monitor usage, rate limit requests.
*   **Tool security**: Validate all parameters, sanitize commands/paths, implement authentication/authorization, rate limit, don't expose internal errors.
*   **Prompt security**: Validate arguments, sanitize user input, consider rate limiting, implement access controls, audit usage, handle sensitive data appropriately, consider prompt injection risks.
*   **Sampling security**: Validate message content, sanitize sensitive info, implement rate limits, monitor usage, encrypt data in transit, handle user data privacy, audit requests, control cost exposure.
*   **Error handling**: Don't leak sensitive information, log security-relevant errors, implement proper cleanup, handle DoS scenarios.

### Debugging and Monitoring
*   **Logging**: Log protocol events, track message flow, monitor performance, record errors.
*   **Diagnostics**: Implement health checks, monitor connection state, track resource usage, profile performance.
*   **Testing**: Test different transports, verify error handling, check edge cases, load test servers.

## Transports in Detail

Transports are the foundation for communication, converting MCP protocol messages to and from JSON-RPC 2.0.

### Standard Input/Output (stdio)
*   **Use cases**: Command-line tools, local integrations, simple process communication.
*   **Mechanism**: Communicates via standard input and output streams.

<Tabs>
  <Tab title="TypeScript (Server)">
    ```typescript
    import { Server } from "@modelcontextprotocol/sdk/server/index.js";
    import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

    const server = new Server({ name: "example-server", version: "1.0.0" }, { capabilities: {} });
    const transport = new StdioServerTransport();
    await server.connect(transport);
    ```
  </Tab>
  <Tab title="Python (Server)">
    ```python
    from mcp.server import Server
    from mcp.server.stdio import stdio_server

    app = Server("example-server")
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
    ```
  </Tab>
</Tabs>

### Server-Sent Events (SSE)
*   **Use cases**: Server-to-client streaming, restricted networks, simple updates.
*   **Mechanism**: HTTP GET for server-to-client streaming, HTTP POST for client-to-server messages.

<Tabs>
  <Tab title="TypeScript (Server)">
    ```typescript
    import express from "express";
    import { Server } from "@modelcontextprotocol/sdk/server/index.js";
    import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

    const app = express();
    const server = new Server({ name: "example-server", version: "1.0.0" }, { capabilities: {} });
    let transport: SSEServerTransport | null = null;

    app.get("/sse", (req, res) => {
      transport = new SSEServerTransport("/messages", res);
      server.connect(transport);
    });
    app.post("/messages", (req, res) => {
      if (transport) { transport.handlePostMessage(req, res); }
    });
    app.listen(3000);
    ```
  </Tab>
  <Tab title="Python (Server)">
    ```python
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route

    app = Server("example-server")
    sse = SseServerTransport("/messages")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(scope, receive, send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    async def handle_messages(scope, receive, send):
        await sse.handle_post_message(scope, receive, send)

    starlette_app = Starlette(routes=[Route("/sse", endpoint=handle_sse), Route("/messages", endpoint=handle_messages, methods=["POST"])])
    ```
  </Tab>
</Tabs>

### Custom Transports
You can implement custom transports by conforming to the `Transport` interface, allowing for specialized communication channels or integration with existing systems.