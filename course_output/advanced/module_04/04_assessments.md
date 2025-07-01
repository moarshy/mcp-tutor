# Building MCP Servers Assessment

This assessment evaluates your knowledge and practical understanding of setting up and working with Minecraft Coder Pack (MCP) for server development.

---

### Section 1: Fundamentals and Prerequisites

**Question 1 (Multiple Choice):**
What does MCP primarily stand for and what is its main purpose in the context of Minecraft modding?
a) Minecraft Core Protocol; for network communication.
b) Minecraft Coder Pack; for decompiling and recompiling Minecraft source code.
c) Modding Creation Platform; for creating new game assets.
d) Minecraft Client Program; for running the game directly.

**Answer:**
b) Minecraft Coder Pack; for decompiling and recompiling Minecraft source code.
*   **Explanation:** MCP (Minecraft Coder Pack) is a set of tools that allows modders to decompile the obfuscated Minecraft client and server JAR files into human-readable Java source code, make modifications, and then recompile and reobfuscate them.

**Question 2 (Short Answer):**
List at least three essential software prerequisites that must be installed and correctly configured on a system before attempting to set up and use MCP.

**Answer:**
1.  **Java Development Kit (JDK):** A specific version of the JDK (e.g., JDK 8 for older MCP versions, newer JDKs for newer MCP/Minecraft versions) is required for compiling and running Java applications, which MCP heavily relies on.
2.  **Minecraft Client JAR:** The specific version of the Minecraft client JAR file that corresponds to the MCP version you are using. This file is needed for MCP to decompile.
3.  **MCP itself:** The downloaded and extracted MCP archive for the desired Minecraft version.
4.  **(Optional but highly recommended) An Integrated Development Environment (IDE):** Such as Eclipse, IntelliJ IDEA, or VS Code, configured with Java development tools, to work with the decompiled source code.

---

### Section 2: Core MCP Workflow

**Question 3 (Step-by-Step):**
You have downloaded MCP and placed the correct Minecraft client JAR file in the `jars` folder. Describe the typical sequence of command-line scripts you would run *for the first time* to set up your MCP development environment for both client and server modding, including preparing an IDE workspace.

**Answer:**
1.  **`decompile.bat` (Windows) / `decompile.sh` (Linux/macOS):** This is the first crucial step. It takes the obfuscated Minecraft client and server JARs, decompiles them into readable Java source code, and applies MCP's patches to make the code more manageable and readable. This process can take a significant amount of time.
2.  **`setup.bat` (Windows) / `setup.sh` (Linux/macOS):** After decompilation, this script sets up the development environment. It typically generates the necessary project files for common IDEs (like Eclipse or IntelliJ IDEA) and performs other initial configurations required for compilation and running. It also sets up the server environment.
3.  **`recompile.bat` (Windows) / `recompile.sh` (Linux/macOS):** While not strictly part of the *initial setup* for the first time, it's the next logical step after `setup` if you want to ensure everything compiles correctly before making changes. It compiles the decompiled source code.

---

### Section 3: Server Specifics and Troubleshooting

**Question 4 (Scenario-Based Troubleshooting):**
You are trying to run the Minecraft server from your MCP environment for testing. You execute `startserver.bat` (or `startserver.sh`), but the server fails to launch, displaying an error message related to "port already in use" or "address already in use."

a) What is the most likely cause of this error?
b) How would you typically resolve this issue to get your server running?

**Answer:**
a) **Most Likely Cause:** The error "port already in use" or "address already in use" indicates that another application or another instance of a Minecraft server is already running and occupying the default Minecraft server port (25565) on your machine. This could be a previous server instance that wasn't properly shut down, or another program using that specific port.

b) **Resolution:**
    1.  **Identify and Terminate Existing Process:**
        *   **Windows:** Open Task Manager (Ctrl+Shift+Esc), go to the "Details" tab, and look for `javaw.exe` or `java.exe` processes that might be running a Minecraft server. End the task for any suspicious processes. You can also use `netstat -ano | findstr :25565` in Command Prompt to find the PID (Process ID) using the port, then use `taskkill /PID [PID] /F`.
        *   **Linux/macOS:** Use `lsof -i :25565` or `netstat -tulnp | grep 25565` to find the process ID (PID) using the port, then use `kill -9 [PID]` to terminate it.
    2.  **Change Server Port:** If you consistently encounter this issue or need to run multiple servers, you can change the default port for your MCP server.
        *   Navigate to the `eclipse` (or `forge`) folder within your MCP directory.
        *   Locate the `server.properties` file.
        *   Open `server.properties` with a text editor and change the `server-port=25565` line to a different available port (e.g., `server-port=25566`). Save the file and try running `startserver.bat` again.

**Question 5 (Short Answer):**
After making modifications to the decompiled server source code within your IDE, which MCP script must you run to compile these changes so they can be tested by launching the server?

**Answer:**
You must run the `recompile.bat` (Windows) or `recompile.sh` (Linux/macOS) script. This script compiles all the Java source files in the `src/minecraft` and `src/minecraft_server` directories (and potentially `src/mcp` for MCP-specific code) into `.class` files, incorporating your changes.

**Question 6 (True/False):**
MCP is designed to work with any version of the Minecraft client JAR file, regardless of the MCP version downloaded.

**Answer:**
**False.**
*   **Explanation:** MCP versions are highly specific to particular Minecraft client and server versions. Each MCP release is tailored to a specific Minecraft update, as the underlying code changes significantly between Minecraft versions. Using an incorrect Minecraft JAR with an MCP version will almost certainly lead to compilation errors, decompilation failures, or runtime issues.

---

### Section 4: Advanced Concepts (Briefly)

**Question 7 (Short Answer):**
What is the primary purpose of the `reobfuscate.bat` (or `reobfuscate.sh`) script in the MCP workflow, especially when preparing a mod for distribution?

**Answer:**
The primary purpose of `reobfuscate.bat` (or `reobfuscate.sh`) is to take the compiled, deobfuscated (human-readable) code and convert it back into an obfuscated format, similar to how Mojang distributes Minecraft. This process is crucial for creating a distributable mod that can be injected into the original, obfuscated Minecraft JAR. It maps the deobfuscated names (e.g., `BlockGrass`) back to their original obfuscated names (e.g., `a.class` or `net.minecraft.block.BlockGrass` in newer versions after Mojang's official mappings).

---