# Advanced Development & Deployment Considerations

This module explores advanced topics in Model Context Protocol (MCP) development, focusing on how Large Language Models (LLMs) can accelerate the creation of MCP servers and clients, and how end-users interact with MCP servers within applications like Claude Desktop.

## Building MCP with Large Language Models (LLMs)

Large Language Models (LLMs) such as Claude can significantly accelerate the development of custom Model Context Protocol (MCP) servers and clients. This section outlines the process and best practices for leveraging LLMs in your MCP development workflow.

### Preparing Documentation for an LLM

Before an LLM can effectively assist in MCP development, it needs to understand the Model Context Protocol and its associated SDKs. The following steps detail how to provide the necessary documentation:

1.  **Full Protocol Documentation**: Access and copy the comprehensive MCP documentation text from `https://modelcontextprotocol.io/llms-full.txt`. This provides the LLM with a deep understanding of the protocol's specifications.
2.  **SDK Documentation**: Navigate to the official MCP SDK repositories (e.g., [TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) or [Python SDK](https://github.com/modelcontextprotocol/python-sdk)). Copy the contents of their README files and any other relevant documentation.
3.  **Provide to LLM**: Paste all collected documentation into your conversation or context window with the LLM. This ensures the LLM has the necessary background information to generate accurate and functional MCP code.

### Describing Server Requirements to an LLM

Once the LLM is equipped with the MCP documentation, clearly articulate the specifications for the server you intend to build. Be precise and detailed about the server's intended functionality:

*   **Resources**: Specify what data or entities your server will expose.
*   **Tools**: Define the actions or operations the server will enable.
*   **Prompts**: Describe any predefined prompt templates or handlers the server should offer.
*   **External Systems**: Detail any external databases, APIs, or services the server needs to interact with.

**Example Description:**
```
Build an MCP server that:
- Connects to my company's PostgreSQL database
- Exposes table schemas as resources
- Provides tools for running read-only SQL queries
- Includes prompts for common data analysis tasks
```

### Collaborating with an LLM for Development and Testing

Working with an LLM like Claude for MCP development is an iterative process. Follow these steps for effective collaboration:

1.  **Start with Core Functionality**: Begin by requesting the LLM to implement the essential features of your server.
2.  **Iterate and Add Features**: Once the core is established, progressively add more features and complexity.
3.  **Seek Explanations**: If any part of the generated code is unclear, ask the LLM for explanations.
4.  **Request Modifications**: Don't hesitate to ask for changes, improvements, or refactoring of the code.
5.  **Leverage for Testing**: Have the LLM assist in generating test cases, identifying edge cases, and debugging issues.

LLMs can help implement all key MCP features, including:
*   Resource management and exposure
*   Tool definitions and implementations
*   Prompt templates and handlers
*   Error handling and logging
*   Connection and transport setup

### Best Practices for LLM Collaboration

To maximize the effectiveness of LLM-assisted MCP development, adhere to these best practices:

*   **Break Down Complexity**: Divide large, complex server functionalities into smaller, manageable components.
*   **Thorough Testing**: Test each component individually before integrating them.
*   **Security First**: Always keep security in mind. Validate all inputs and implement appropriate access controls.
*   **Document Code**: Ensure the generated code is well-documented for future maintenance and understanding.
*   **Follow Protocol Specifications**: Verify that the generated code strictly adheres to the MCP protocol specifications.

### Next Steps After LLM Assistance

After the LLM has helped you build your server, take these crucial next steps:

1.  **Code Review**: Carefully review the generated code for correctness, efficiency, and security.
2.  **Testing with MCP Inspector**: Utilize the MCP Inspector tool to thoroughly test your server's functionality.
3.  **Client Connection**: Connect your newly built server to MCP clients, such as Claude.app or other compatible applications.
4.  **Iterate Based on Feedback**: Gather real-world usage feedback and iterate on your server's design and implementation as requirements evolve.

Remember that LLMs can continue to assist in modifying and improving your server as needs change or new issues arise.

## For Claude Desktop Users: Consuming MCP Servers

Claude for Desktop extends its capabilities by integrating with MCP servers, allowing it to interact with your local environment, such as your computer's file system. This section guides you through the process of setting up and using pre-built MCP servers within Claude for Desktop from an end-user perspective.

### Purpose of MCP Servers in Claude Desktop

MCP servers enable Claude Desktop to perform actions and access information beyond its inherent LLM capabilities. For instance, a Filesystem MCP Server allows Claude to read, write, move, and search files on your computer. This functionality is currently supported for desktop hosts because servers are run locally, with remote host support under active development. Claude Desktop will always ask for your permission before executing any actions that modify your system.

### Downloading and Updating Claude for Desktop

To begin, ensure you have Claude for Desktop installed and updated:

1.  **Download**: Download Claude for Desktop from [claude.ai/download](https://claude.ai/download) for macOS or Windows. Linux is not currently supported.
2.  **Installation**: Follow the provided installation instructions.
3.  **Update**: If you already have Claude for Desktop, ensure it's on the latest version by clicking on the Claude menu on your computer and selecting "Check for Updates...".

### Locating and Editing the Claude Desktop Configuration File

To add MCP servers, you need to modify Claude Desktop's configuration file:

1.  **Open Settings**: Open the Claude menu on your computer and select "Settings...". Note that these are distinct from the Claude Account Settings within the app window.
2.  **Navigate to Developer Settings**: In the Settings pane, click on "Developer" in the left-hand bar.
3.  **Edit Config**: Click on "Edit Config". This action will either create a new configuration file or open an existing one in your file system.

The configuration file is located at:
*   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
*   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Open this `claude_desktop_config.json` file using any text editor.

### Configuring a Pre-built Filesystem MCP Server

To enable file system access, you will install a pre-built [Filesystem MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem). Replace the entire content of your `claude_desktop_config.json` file with the following, making sure to replace `username` with your actual computer username and adjusting paths as needed:

<Tabs>
<Tab title="MacOS/Linux">
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/Desktop",
        "/Users/username/Downloads"
      ]
    }
  }
}
```
</Tab>
<Tab title="Windows">
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\username\\Desktop",
        "C:\\Users\\username\\Downloads"
      ]
    }
  }
}
```
</Tab>
</Tabs>

**Explanation of the Configuration File:**
This JSON configuration tells Claude for Desktop which MCP servers to launch upon application startup.
*   `"mcpServers"`: This object contains definitions for all MCP servers.
*   `"filesystem"`: This is the name given to this specific server instance.
*   `"command"`: Specifies the executable command to run the server, in this case, `npx`.
*   `"args"`: An array of arguments passed to the command.
    *   `-y`: Automatically answers "yes" to prompts from `npx`.
    *   `@modelcontextprotocol/server-filesystem`: The package name for the Filesystem MCP Server.
    *   The subsequent arguments (e.g., `"/Users/username/Desktop"`) are the absolute paths to the directories you want Claude to be able to access and modify. You can add more paths as needed.

**Node.js Prerequisite:**
The `npx` command requires [Node.js](https://nodejs.org) to be installed on your computer. To verify your Node.js installation:
1.  Open your command line (Terminal on macOS, Command Prompt on Windows).
2.  Enter `node --version`.
3.  If you receive an error like "command not found" or "node is not recognized," download and install Node.js from [nodejs.org](https://nodejs.org/).

<Warning>
**Command Privileges**
Claude for Desktop executes commands specified in the configuration file with the same permissions as your user account, granting them access to your local files. Only add commands from sources you understand and explicitly trust.
</Warning>

### Restarting Claude and Verifying Server Load

After saving changes to your `claude_desktop_config.json` file, you must restart Claude for Desktop completely.

Upon successful restart, you should observe a hammer icon (<img src="/images/claude-desktop-mcp-hammer-icon.svg" style={{display: 'inline', margin: 0, height: '1.3em'}} />) in the bottom right corner of the input box within Claude Desktop. Clicking this icon will display the tools provided by the Filesystem MCP Server, confirming it has loaded correctly.

### Trying Out the Filesystem Server

With the Filesystem MCP Server active, you can now interact with Claude and ask it to perform file system operations. Claude is designed to intelligently call the relevant tools when needed.

**Example Prompts:**
*   "Can you write a poem and save it to my desktop?"
*   "What are some work-related files in my downloads folder?"
*   "Can you take all the images on my desktop and move them to a new folder called 'Images'?"

Claude will prompt you for approval before executing any actions that modify your file system.

### Troubleshooting

If you encounter issues, refer to these common troubleshooting steps:

<AccordionGroup>
<Accordion title="Server not showing up in Claude / hammer icon missing">
  1.  **Restart Claude for Desktop completely.** A full restart is often necessary for configuration changes to take effect.
  2.  **Check your `claude_desktop_config.json` file syntax.** Ensure there are no typos or formatting errors in the JSON.
  3.  **Verify file paths.** Make sure the directory paths included in `claude_desktop_config.json` are valid, absolute, and not relative.
  4.  **Review logs.** Check the Claude Desktop logs to identify specific connection failures or errors.
  5.  **Manually run the server.** Open your command line and try running the server command directly (replacing `username` as you did in the config file) to see if it produces any errors:
      <Tabs>
      <Tab title="MacOS/Linux">
      ```bash
      npx -y @modelcontextprotocol/server-filesystem /Users/username/Desktop /Users/username/Downloads
      ```
      </Tab>
      <Tab title="Windows">
      ```bash
      npx -y @modelcontextprotocol/server-filesystem C:\Users\username\Desktop C:\Users\username\Downloads
      ```
      </Tab>
      </Tabs>
</Accordion>
<Accordion title="Getting logs from Claude for Desktop">
  Claude.app logging related to MCP is written to log files in:
  -   **macOS**: `~/Library/Logs/Claude`
  -   **Windows**: `%APPDATA%\Claude\logs`

  -   `mcp.log` contains general logging about MCP connections and connection failures.
  -   Files named `mcp-server-SERVERNAME.log` contain error (stderr) logging from the named server.

  You can run the following command to list recent logs and follow along with any new ones (on Windows, it will only show recent logs):
  <Tabs>
  <Tab title="MacOS/Linux">
  ```bash
  # Check Claude's logs for errors
  tail -n 20 -f ~/Library/Logs/Claude/mcp*.log
  ```
  </Tab>
  <Tab title="Windows">
  ```bash
  type "%APPDATA%\Claude\logs\mcp*.log"
  ```
  </Tab>
  </Tabs>
</Accordion>
<Accordion title="Tool calls failing silently">
  If Claude attempts to use the tools but they fail without explicit error messages:
  1.  **Check Claude's logs for errors.** This is the primary place to find details about tool execution failures.
  2.  **Verify your server builds and runs without errors.** Ensure the underlying server process itself is stable.
  3.  **Try restarting Claude for Desktop.** A fresh start can sometimes resolve transient issues.
</Accordion>
<Accordion title="None of this is working. What do I do?">
  For more in-depth debugging tools and guidance, refer to the official [debugging guide](/docs/tools/debugging).
</Accordion>
<Accordion title="ENOENT error and `${APPDATA}` in paths on Windows">
If your configured server fails to load, and its logs show an `ENOENT` error referring to `${APPDATA}` within a path, you might need to explicitly add the expanded value of `%APPDATA%` to your `env` key in `claude_desktop_config.json`:

```json
{
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "APPDATA": "C:\\Users\\user\\AppData\\Roaming\\",
      "BRAVE_API_KEY": "..."
    }
  }
}
```

After making this change, relaunch Claude Desktop.

<Warning>
**NPM should be installed globally**
The `npx` command may continue to fail if NPM is not installed globally. If NPM is globally installed, you will find `%APPDATA%\npm` on your system. If not, you can install NPM globally by running:
```bash
npm install -g npm
```
</Warning>
</Accordion>
</AccordionGroup>