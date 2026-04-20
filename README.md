MC Server Controller
A sleek, Python-based GUI for managing a Minecraft server with integrated Git synchronization. This tool automates the process of pulling world updates, launching the server with optimized Aikar JVM flags, and pushing changes back to GitHub for easy hosting hand-offs.

Key Features: 
Automated Git Sync: Automatically pulls the latest world data on startup and pushes updates when the server stops.Optimized JVM Flags: Launches the server using Aikar’s flags to ensure high performance and stable garbage collection.Dual-Log Interface: Features a dedicated Activity Log for system events and a separate Chat/Events box to monitor player activity, such as joins, deaths, and messages.Customizable Themes: Includes 8 visual presets, including "Midnight Blue," "Creeper Green," "Nether Red," and "Obsidian".Hand-Off Routine: A specialized button to gracefully stop the server, sync the world, and notify friends that the repository is ready for them to pull and host.Headless Operation: Runs the Java process without an external command window, keeping your desktop clean while routing all output to the app.

Requirements
To run this controller, your system must meet the following criteria:
Python 3.x: Requires the customtkinter library for a modern UI.
Git: Must be installed and configured in your system PATH to handle world synchronization.
Java 21: The default configuration points to JDK 21, though this can be adjusted in the settings.
Operating System: Designed for Windows (uses ctypes for taskbar icons and taskkill for process management).

 📦 Setup & Configuration
Dependencies: Install the required Python library:

pip install customtkinter

File Placement: Ensure launcher.pyw and icon.ico are in the same directory.
Local Paths: Update the following variables in the script to match your setup:

SRV_PATH: The folder containing your server.jar.

JAVA_PATH: The location of your java.exe.

REPO_URL: Your GitHub repository for world storage.

UsageStart:
Pulls the latest files from GitHub and launches the server.Stop: Sends the /stop command to the server, kills the Java process, and pushes world/, world_nether/, and world_the_end/ to your repository.Sync & Upload: Performs a manual git add . and push for non-world files (like configuration changes).Console: Type commands (without the leading /) into the bottom entry field to interact with the server live.
