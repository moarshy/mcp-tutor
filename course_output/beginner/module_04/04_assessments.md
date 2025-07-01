# Building Your First MCP Server Assessment

This assessment tests your knowledge of setting up and working with the Minecraft Coder Pack (MCP) for server development.

---

### Question 1: Understanding MCP's Role

What is MCP (Minecraft Coder Pack), and why is it considered an essential tool for Minecraft server development, particularly when it comes to modding?

**Detailed Answer:**
MCP (Minecraft Coder Pack) is a set of tools designed to deobfuscate and decompile the Minecraft client and server JAR files. Minecraft's original code is "obfuscated," meaning its variable names, method names, and class names are scrambled into unreadable sequences (e.g., `a`, `b`, `aa`, `ab`). This makes it extremely difficult for developers to understand and modify the game's internal workings directly.

MCP's essential role is to:
1.  **Deobfuscate:** It maps the scrambled names back to human-readable, descriptive names (e.g., `a` becomes `EntityPlayer`, `b` becomes `updateTick`). This transformation makes the source code comprehensible.
2.  **Decompile:** It converts the compiled Java bytecode (`.class` files) back into readable Java source code (`.java` files).

For modding, MCP is indispensable because:
*   **Enables Code Comprehension:** Developers can read and understand the game's logic, allowing them to identify where and how to inject their own modifications.
*   **Provides a Development Environment:** It sets up a structured workspace with the deobfuscated source code, making it possible to write new code that interacts seamlessly with the game's existing functions.
*   **Facilitates Compatibility:** It allows developers to compile their mods against the deobfuscated code and then re-obfuscate them to match the original game's structure, ensuring compatibility with the official Minecraft client/server. Without MCP, creating complex, stable mods would be nearly impossible due to the obfuscated nature of the game's code.

---

### Question 2: Prerequisites for MCP Server Setup

Before you begin the process of setting up an MCP server, what are the fundamental software prerequisites you need to have installed and prepared on your system? List at least three.

**Detailed Answer:**
To successfully set up an MCP server environment, you need the following fundamental software prerequisites:

1.  **Java Development Kit (JDK):** This is crucial. MCP is written in Java and needs a JDK to compile and run the Minecraft server and its own tools. The specific version of the JDK (e.g., JDK 8, JDK 11, JDK 17) depends on the version of Minecraft and MCP you are using. It's important to install the *Development Kit* (JDK), not just the Java Runtime Environment (JRE), as the JDK includes the compiler and other development tools.
2.  **Minecraft Server JAR File:** You need the specific `minecraft_server.jar` file for the version of Minecraft you intend to decompile and modify. This file is the raw, obfuscated server code that MCP will process. It must be placed in the correct directory within the MCP folder structure (typically the `jars` folder).
3.  **MCP (Minecraft Coder Pack) Itself:** The MCP archive (usually a `.zip` file) for the specific Minecraft version you are targeting. This contains all the scripts, configuration files, and mapping data that MCP uses to perform its deobfuscation and compilation tasks.
4.  **A Text Editor or Integrated Development Environment (IDE):** While not strictly required for MCP's initial setup, it's essential for any actual development. Tools like Visual Studio Code, IntelliJ IDEA, or Eclipse are highly recommended for writing, editing, and debugging your Java code within the MCP environment.

---

### Question 3: Step-by-Step MCP Server Setup

Outline the step-by-step process to set up an MCP server environment from a fresh download of MCP. Assume you have all the necessary prerequisites in place.

**Detailed Answer:**
Here's the typical step-by-step process to set up an MCP server environment:

1.  **Download and Extract MCP:**
    *   Download the correct version of the MCP archive (e.g., `mcp918.zip` for Minecraft 1.8.9) from a reliable source.
    *   Extract the contents of the downloaded ZIP file to a clean, easily accessible directory on your computer (e.g., `C:\mcp` on Windows, or `~/mcp` on Linux/macOS). Avoid paths with spaces or special characters if possible, though modern MCP versions are more robust.

2.  **Place Minecraft Server JAR:**
    *   Locate the `minecraft_server.jar` file for the specific Minecraft version you want to work with.
    *   Copy this `minecraft_server.jar` file into the `jars` folder located inside your extracted MCP directory (e.g., `C:\mcp\jars`). Ensure the filename is exactly `minecraft_server.jar` or whatever the MCP version specifically requires (sometimes it might be `minecraft_server.1.x.x.jar`).

3.  **Run the Decompile Script:**
    *   Navigate to your MCP directory using a command prompt or terminal.
    *   Execute the appropriate decompile script:
        *   **Windows:** Run `decompile.bat`
        *   **Linux/macOS:** Run `sh decompile.sh` (or `./decompile.sh` if executable permissions are set)
    *   This script will download necessary libraries, decompile the `minecraft_server.jar`, apply the deobfuscation mappings, and set up the development environment. This process can take a significant amount of time and requires an active internet connection.

4.  **Verify Setup (Optional but Recommended):**
    *   Once the `decompile` script completes successfully, check the `src/minecraft` directory within your MCP folder. You should find the deobfuscated Java source code files for the Minecraft server there.
    *   If you plan to use an IDE, you might also run `eclipse.bat`/`eclipse.sh` or `idea.bat`/`idea.sh` to generate project files for your chosen IDE.

After these steps, your MCP server development environment is ready for you to start making code modifications.

---

### Question 4: `recompile` vs. `reobfuscate`

Explain the primary purpose of the `recompile` and `reobfuscate` tasks (or scripts) within the MCP workflow. Why are both necessary steps after you've made modifications to the server's source code?

**Detailed Answer:**
After making modifications to the deobfuscated source code in an MCP environment, two crucial tasks are performed: `recompile` and `reobfuscate`.

1.  **`recompile` (e.g., `recompile.bat` / `recompile.sh`):**
    *   **Purpose:** This task takes the Java source code files (`.java` files) that you have modified (located in the `src` directory) and compiles them into Java bytecode (`.class` files). It essentially translates your human-readable code into machine-executable instructions.
    *   **Necessity:** The Minecraft server (and Java applications in general) runs on compiled bytecode, not raw source code. Therefore, any changes you make to the source code must be compiled before they can be executed by the Java Virtual Machine (JVM).

2.  **`reobfuscate` (e.g., `reobfuscate.bat` / `reobfuscate.sh`):**
    *   **Purpose:** This task takes the newly compiled `.class` files (which are currently deobfuscated) and re-applies the original Minecraft obfuscation mappings. It scrambles the variable, method, and class names back to their original, unreadable forms.
    *   **Necessity:** This step is critical for compatibility. The official Minecraft client and server expect the code to be obfuscated in a very specific way. If you were to distribute your modified code without reobfuscation, it would not be compatible with the official game files, leading to errors or crashes. Reobfuscation ensures that your modified code can be seamlessly integrated back into the original Minecraft JAR structure, allowing it to run alongside or replace official game components.

**Why both are necessary:**
*   `recompile` is necessary to turn your source code changes into executable bytecode.
*   `reobfuscate` is necessary to make that compiled bytecode compatible with the official Minecraft game environment, allowing it to be distributed and run correctly. You compile your changes in a readable format, then obfuscate them back to the game's expected format.

---

### Question 5: Running the Modified Server

After successfully setting up MCP, making your desired code modifications, and running the necessary compilation steps, how would you typically run the modified Minecraft server for testing purposes within the MCP environment?

**Detailed Answer:**
After successfully setting up MCP, making code modifications, and ensuring they are compiled (by running `recompile.bat` or `recompile.sh`), you would typically run the modified Minecraft server for testing using the following steps:

1.  **Ensure Compilation:** First, make sure you have executed `recompile.bat` (Windows) or `recompile.sh` (Linux/macOS) from the MCP root directory. This step compiles any changes you've made to the deobfuscated source code into `.class` files.
2.  **Run the Server Script:** Then, you would execute the dedicated server startup script provided by MCP:
    *   **Windows:** Run `startserver.bat`
    *   **Linux/macOS:** Run `sh startserver.sh` (or `./startserver.sh`)

This script launches the Minecraft server using the deobfuscated and recompiled code from your development environment. It typically sets up the classpath to include your modified classes, allowing you to test your changes directly without needing to manually re-package the server JAR. The server will run in your console, and you can connect to it from a Minecraft client (usually by connecting to `localhost` or `127.0.0.1`).

---

### Question 6: Common Issues and Troubleshooting

List two common issues encountered when setting up or working with an MCP server and provide a brief troubleshooting tip for each.

**Detailed Answer:**

1.  **Issue 1: `decompile.bat` (or `decompile.sh`) fails or gets stuck, often with Java-related errors or "Could not find or load main class."**
    *   **Troubleshooting Tip:** This is frequently caused by an incorrect or incompatible Java Development Kit (JDK) version.
        *   **Check JDK Version:** Ensure you have the correct JDK version installed that is compatible with your specific MCP and Minecraft version (e.g., JDK 8 for older Minecraft versions, newer JDKs for newer ones). Remember, it must be a JDK, not just a JRE.
        *   **Verify `JAVA_HOME`:** Confirm that your `JAVA_HOME` environment variable is correctly set to the root directory of your JDK installation, and that your system's `PATH` variable includes `%JAVA_HOME%\bin` (Windows) or `$JAVA_HOME/bin` (Linux/macOS).
        *   **Internet Connection:** `decompile` downloads necessary libraries, so ensure you have a stable internet connection.

2.  **Issue 2: `minecraft_server.jar` not found or "Missing server jar" errors during `decompile`.**
    *   **Troubleshooting Tip:** This indicates that MCP cannot locate the Minecraft server JAR file it needs to decompile.
        *   **Correct Placement:** Double-check that you have placed the `minecraft_server.jar` file directly into the `jars` folder within your MCP directory (e.g., `C:\mcp\jars`).
        *   **Correct Filename:** Ensure the JAR file is named exactly `minecraft_server.jar`. Some MCP versions or specific Minecraft versions might require a slightly different name (e.g., `minecraft_server.1.x.x.jar`), so consult the MCP documentation if the generic name doesn't work.
        *   **Integrity:** Ensure the JAR file itself is not corrupted and is the correct version for your MCP release.

3.  **Issue 3: Compilation errors after making code changes when running `recompile`.**
    *   **Troubleshooting Tip:** These are typically syntax errors or logical errors in the Java code you've written or modified.
        *   **Review Error Messages:** The console output from `recompile` will display detailed error messages, including file names and line numbers. Carefully read these messages to pinpoint the exact location and nature of the error.
        *   **Use an IDE:** If you're not already, import your MCP project into an IDE like IntelliJ IDEA or Eclipse. IDEs provide real-time syntax checking, error highlighting, and debugging tools that make it much easier to identify and fix compilation issues before running `recompile`.

---