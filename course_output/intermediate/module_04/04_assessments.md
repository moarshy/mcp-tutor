# Module 4: Building MCP Servers: Quickstart & Best Practices Assessment

This assessment covers key concepts related to setting up, configuring, and maintaining Minecraft Coder Pack (MCP) servers, with a focus on quick deployment and adherence to best practices for mod development.

---

**Instructions:** Answer all questions thoroughly. For multiple-choice or fill-in-the-blank questions, select the best option or provide the correct term. For short answer questions, provide concise yet comprehensive explanations.

---

### Section 1: Quickstart Fundamentals

**Question 1:** What is the primary purpose of setting up an MCP server in the context of Minecraft mod development?

**Answer:**
The primary purpose of setting up an MCP server is to provide a local, isolated server environment for developers to test their Minecraft mods. This allows for rapid iteration, debugging, and verification of mod functionality without affecting live game servers or requiring a public deployment. It's crucial for ensuring mods work correctly in a server-side context.

---

**Question 2:** List the essential command-line steps required to get an MCP server running for the first time after downloading and extracting the MCP package. Assume you are in the MCP root directory.

**Answer:**
The essential command-line steps are:
1.  **`setup.sh` (Linux/macOS) or `setup.bat` (Windows):** This command downloads and sets up the necessary Minecraft client and server JARs, patches them, and prepares the environment.
2.  **`decompile.sh` (Linux/macOS) or `decompile.bat` (Windows):** This command decompiles the Minecraft source code, making it readable and editable for mod development.
3.  **`startserver.sh` (Linux/macOS) or `startserver.bat` (Windows):** This command starts the MCP-prepared Minecraft server. (Alternatively, you might navigate to the `jars` folder and run the `minecraft_server.jar` or `minecraft_server_reobf.jar` directly with Java).

---

**Question 3:** Which configuration file is crucial for adjusting basic server settings such as the server port, game mode, maximum players, and enabling/disabling PvP?

**Answer:**
The `server.properties` file.

---

**Question 4:** You've just run `startserver.sh` (or `.bat`), but the server immediately shuts down or gives an "Out of Memory" error. What is the most common cause for this, and how would you typically resolve it?

**Answer:**
**Most Common Cause:** The server is not allocated enough RAM (Random Access Memory) to run effectively, or the default allocation is insufficient for the current workload (e.g., if you've added many mods).

**Resolution:** You would typically resolve this by increasing the maximum heap size allocated to the Java Virtual Machine (JVM) that runs the server. This is done by modifying the `-Xmx` JVM argument in the server startup script (e.g., `startserver.sh`/`startserver.bat` or a custom script you've created). For example, changing `java -Xmx1024M -Xms1024M -jar minecraft_server.jar nogui` to `java -Xmx4G -Xms4G -jar minecraft_server.jar nogui` to allocate 4 Gigabytes of RAM.

---

### Section 2: Best Practices for Development & Performance

**Question 5:** From a security perspective, why is it generally considered a bad practice to expose an MCP development server directly to the public internet without additional security measures? Name at least two reasons.

**Answer:**
It's a bad practice for several reasons:
1.  **Vulnerability to Attacks:** Development servers often have less stringent security configurations than production servers. They might run with default passwords, have open ports, or contain unpatched software, making them easy targets for malicious actors.
2.  **Exposure of Unreleased Code/Data:** A development server might contain unreleased mod features, sensitive configuration data, or even personal information if not properly secured. Exposing it risks intellectual property theft or data breaches.
3.  **Resource Exploitation:** An exposed server can be exploited for DDoS attacks, cryptocurrency mining, or other illicit activities, consuming your resources and potentially leading to legal issues.
4.  **Lack of Optimization:** Development servers are typically not optimized for public traffic, leading to poor performance, instability, and a bad user experience if accessed by many people.

---

**Question 6:** Name two common JVM arguments (besides `-Xms` and `-Xmx`) that are often recommended for optimizing the performance of a Minecraft server, and briefly explain their purpose.

**Answer:**
1.  **`-XX:+UseG1GC`**: This argument enables the Garbage-First (G1) Garbage Collector. G1GC is designed to be a "soft real-time" collector, aiming to achieve high throughput while trying to meet user-defined pause time goals. It's generally recommended for servers with larger heap sizes (e.g., 4GB or more) as it can reduce garbage collection pauses, leading to smoother gameplay.
2.  **`-XX:MaxGCPauseMillis=<milliseconds>`**: This argument sets a target for the maximum pause time for garbage collection. While the JVM tries to meet this goal, it's not a strict guarantee. Setting a reasonable value (e.g., 50-200ms) can help prevent long, noticeable server freezes due to garbage collection.

*(Other valid answers could include `-XX:+UnlockExperimentalVMOptions`, `-XX:G1NewSizePercent`, `-XX:G1MaxNewSizePercent`, `-XX:G1HeapRegionSize`, etc., but `UseG1GC` and `MaxGCPauseMillis` are very common and impactful.)*

---

**Question 7:** When developing a mod, you make changes to your source code. Explain the role of the `recompile` and `reobfuscate` processes in MCP before you can test your changes on the server.

**Answer:**
1.  **`recompile`**: After you modify your mod's source code (Java files), the `recompile` process compiles these updated `.java` files into `.class` bytecode files. This step ensures that your latest code changes are translated into an executable format.
2.  **`reobfuscate`**: Minecraft's internal code is obfuscated (its names are scrambled) for various reasons. When you develop with MCP, you work with de-obfuscated, human-readable names. The `reobfuscate` process takes your compiled mod's `.class` files and re-scrambles their names to match the obfuscated names used by the actual Minecraft server JAR. This step is crucial because the server expects the obfuscated names, and without reobfuscation, your mod would not be able to interact correctly with the server's internal components.

In essence, `recompile` updates your code, and `reobfuscate` makes it compatible with the server's runtime environment.

---

**Question 8:** Why is it a best practice to use a version control system (like Git) for your mod development project, even if you're the sole developer working with an MCP server? Name at least two benefits.

**Answer:**
Using a version control system like Git is a best practice even for solo developers because:
1.  **Change Tracking and History:** Git meticulously tracks every change made to your code. This allows you to see who changed what, when, and why, providing a complete history of your project. This is invaluable for understanding how your mod evolved.
2.  **Rollbacks and Undoing Mistakes:** If you introduce a bug, break functionality, or simply want to revert to a previous working state, Git allows you to easily "rollback" your codebase to any prior commit. This saves significant time and effort compared to manually managing backups.
3.  **Experimentation and Branching:** Git's branching feature allows you to create separate lines of development for new features, bug fixes, or experimental changes without affecting your stable main codebase. You can work on multiple things simultaneously and merge them back when ready.
4.  **Backup and Disaster Recovery:** If your local development environment is corrupted or lost, your Git repository (especially if pushed to a remote like GitHub) serves as an off-site backup of your entire project history.

---

**Question 9:** Describe a good strategy for backing up your MCP server's world data and configuration files. Why is this important even for a development server?

**Answer:**
**Backup Strategy:**
A good strategy involves:
1.  **Regular Snapshots:** Schedule or manually create periodic backups of the entire server directory, especially the `world` folder (which contains all world data) and critical configuration files like `server.properties`, `ops.json`, `whitelist.json`, and any mod configuration files.
2.  **Automated Scripts:** Use simple shell scripts (e.g., `cron` jobs on Linux, Task Scheduler on Windows) to automate the backup process, compressing the files (e.g., using `tar` or `zip`) and storing them in a separate location.
3.  **Off-site Storage:** For critical projects, consider storing backups on a separate drive, network share, or cloud storage service to protect against local hardware failure.
4.  **Versioned Backups:** Keep multiple backup versions (e.g., daily for a week, weekly for a month) to allow reverting to different points in time.

**Importance for Development Server:**
Even for a development server, regular backups are crucial because:
*   **Prevent Data Loss:** Mod development can be unstable. Crashes, accidental deletions, or corrupted files (especially world data due to buggy mods) can lead to significant loss of progress.
*   **Revert to Stable States:** Backups allow you to quickly revert the server to a known stable state if a new mod or code change introduces critical bugs or breaks the world. This is invaluable for debugging and testing.
*   **Testing Scenarios:** You might want to test a mod's behavior on a specific world state or configuration. Backups allow you to easily restore that state for consistent testing.

---

### Section 3: Scenario & Application

**Question 10:** You've developed a new mod and compiled it, but when you start your MCP server, the mod doesn't appear to be loading or functioning in-game. List three common reasons for this issue and a corresponding troubleshooting step for each.

**Answer:**
Here are three common reasons and troubleshooting steps:

1.  **Reason: Mod JAR not in the correct location or not integrated into the build.**
    *   **Troubleshooting Step:** Ensure your compiled mod's `.jar` file is placed in the server's `mods` folder (if using a mod loader like Forge or Fabric) or that your MCP build process correctly integrates your mod's classes into the server's classpath. Double-check the `mods` folder path and verify the JAR is present.

2.  **Reason: Server not running with the correct mod loader (Forge/Fabric) or mod loader not installed/configured correctly.**
    *   **Troubleshooting Step:** Verify that your MCP server setup includes and correctly launches with the necessary mod loader (e.g., Forge or Fabric) if your mod depends on it. Check the server startup script and logs to confirm the mod loader is initializing. Sometimes, the MCP `startserver` script might need modification to launch a Forge/Fabric server instead of a vanilla one.

3.  **Reason: Compilation errors or runtime exceptions within the mod.**
    *   **Troubleshooting Step:** Check the server console and server log files (e.g., `logs/latest.log`) for any error messages, stack traces, or warnings related to your mod. These logs often provide specific details about why the mod failed to load or encountered an issue during initialization. Also, review your mod's build output for any compilation warnings or errors.

*(Other valid reasons could include: incorrect `mcmod.info` or `fabric.mod.json` metadata, missing mod dependencies, incorrect Minecraft version compatibility, etc.)*

---

**Question 11:** Your MCP development server, which usually runs smoothly, has suddenly started consuming an unusually high amount of CPU resources, even when no players are connected. What are two potential causes for this, and how would you investigate them?

**Answer:**
**Potential Causes & Investigation:**

1.  **Cause: A newly added or buggy mod is causing a performance bottleneck or infinite loop.**
    *   **Investigation:**
        *   **Check Server Logs:** Review the server console and `latest.log` file for any repetitive error messages, warnings, or unusual activity that might indicate a mod misbehaving.
        *   **Isolate Mods:** If you recently added or updated mods, try removing them one by one (or in batches) and restarting the server to see if the CPU usage returns to normal. This helps pinpoint the problematic mod.
        *   **Profiling Tools:** For more advanced debugging, consider using Java profiling tools (e.g., VisualVM, YourKit) to attach to the running server process and identify which threads or methods are consuming the most CPU cycles.

2.  **Cause: External factors or system-level issues on the host machine.**
    *   **Investigation:**
        *   **System Monitoring:** Use your operating system's task manager (Windows: Task Manager, Linux: `top` or `htop`, macOS: Activity Monitor) to identify which processes are consuming the most CPU. Confirm it's indeed the Java process running the Minecraft server and not another application.
        *   **Background Processes:** Check if any other resource-intensive applications, background tasks, or system updates are running on the same machine that could be competing for CPU resources.
        *   **Disk I/O:** High CPU can sometimes be linked to excessive disk I/O. Check if the server is constantly reading/writing to disk, which could indicate a world corruption issue or a mod constantly saving data.

---

**Question 12:** You are setting up a new MCP server for a team of three mod developers. Beyond the basic quickstart, what are two best practices you would implement to ensure a smooth and collaborative development environment?

**Answer:**
1.  **Implement a Version Control System (VCS) like Git:**
    *   **Why:** This is paramount for collaboration. Each developer can work on their features in separate branches, merge changes, resolve conflicts, and track the entire history of the codebase. It prevents accidental overwrites, allows for easy rollbacks, and provides a clear overview of who changed what.
    *   **Implementation:** Set up a shared Git repository (e.g., on GitHub, GitLab, or a private Git server). Educate the team on Git workflows (branching, committing, pulling, pushing, merging, conflict resolution). Ensure the MCP source directories (`src/minecraft`, `src/minecraft_server`, and your mod's source) are under version control.

2.  **Standardize Development Environment and Configuration:**
    *   **Why:** Inconsistent setups can lead to "works on my machine" issues. Standardizing ensures everyone is working with the same MCP version, Java Development Kit (JDK) version, server configuration, and potentially the same IDE settings.
    *   **Implementation:**
        *   **Document Setup:** Create clear, step-by-step documentation for setting up the MCP environment, including required JDK version, specific MCP commands, and any custom scripts.
        *   **Share Configuration Files:** Version control important server configuration files (like `server.properties` templates, `ops.json`, `whitelist.json`, and mod config files) so everyone uses the same base settings.
        *   **Consistent Mod Loaders:** If using Forge or Fabric, ensure all developers are using the exact same version and that the server is configured to run with it.
        *   **Shared Libraries/Dependencies:** Use a dependency management system (if applicable for your mod loader) or clearly define and share any external libraries required by the mods.

---