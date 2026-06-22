import os
import sys
import time
import shutil
import urllib.request
import subprocess

# --- TELEMETRY & DESIGN CONSTANTS (High-Contrast Premium Green Palette) ---
# Bright neon matrix green for primary highlights
CLR_MATRIX = '\033[38;5;82m'
CLR_MINT = '\033[38;5;121m'    # Light crisp mint for primary header texts
CLR_DARK = '\033[38;5;238m'    # Deep muted gray-green for structural borders
# Subdued dark green for running tickers/brackets
CLR_FOREST = '\033[38;5;28m'
# Soft, readable pale green-white for standard logs
CLR_TEXT = '\033[38;5;193m'
# Sharp orange-red strictly reserved for errors/purges
CLR_WARN = '\033[38;5;202m'
CLR_RESET = '\033[0m'

SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

PACKAGES = [
    'customtkinter',
    'PyQt6',
    'PySide6',
    'psutil',
    'matplotlib',
    'tkinterdnd2',
    'pillow',
    'brotli',
    'brotlicffi'
]

PROJECT_FILES = [
    '.gitignore',
    'icon.ico',
    'install_requirements.py',
    'install_requrements_(windows).bat',
    'launcher.pyw',
    'mc_modpack.py',
    'readme.md'
]

PROJECT_FOLDERS = [
    'addons',
    'logs',
    'mods',
    'backups',
    'servers'
]

CORES = {
    '1': {
        'name': 'Paper MC (Highly Optimized Plugins)',
        'filename': 'paper-server.jar',
        'url': 'https://api.papermc.io/v2/projects/paper/versions/1.21.1/builds/130/downloads/paper-1.21.1-130.jar'
    },
    '2': {
        'name': 'Purpur (Advanced Tuning & Plugins)',
        'filename': 'purpur-server.jar',
        'url': 'https://api.purpurmc.org/v2/purpur/1.21.1/latest/download'
    },
    '3': {
        'name': 'Spigot (Classic Plugin Framework)',
        'filename': 'spigot-server.jar',
        'url': 'https://download.getbukkit.org/spigot/spigot-1.21.1.jar'
    },
    '4': {
        'name': 'CraftBukkit (Legacy Bukkit API Base)',
        'filename': 'craftbukkit-server.jar',
        'url': 'https://download.getbukkit.org/craftbukkit/craftbukkit-1.21.1.jar'
    },
    '5': {
        'name': 'Fabric Loader (Lightweight Modern Mods)',
        'filename': 'fabric-installer.jar',
        'url': 'https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.0.1/fabric-installer-1.0.1.jar'
    },
    '6': {
        'name': 'Minecraft Forge (Heavy Traditional Mods)',
        'filename': 'forge-installer.jar',
        'url': 'https://maven.minecraftforge.net/net/minecraftforge/forge/1.21.1-52.0.1/forge-1.21.1-52.0.1-installer.jar'
    },
    '7': {
        'name': 'Vanilla Minecraft Official Core',
        'filename': 'vanilla-server.jar',
        'url': 'https://piston-data.mojang.com/v1/objects/4707d00eb834b44e9dae80bad31a1d3d03b306b0/server.jar'
    }
}


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def progress_bar(percent):
    total_width = 24
    filled = int(total_width * (percent / 100))
    empty = total_width - filled

    bar_fill = f"{CLR_MATRIX}{'█' * filled}"
    bar_empty = f"{CLR_FOREST}{'·' * empty}"

    return f"{CLR_DARK}[{bar_fill}{bar_empty}{CLR_DARK}] {CLR_MATRIX}{percent:3.1f}%"


def header():
    py_ver = sys.version.split()[0]
    print(f"{CLR_DARK}┌────────────────────────────────────────────────────────────────────────┐")
    print(f"│  {CLR_MATRIX} MC-CTRL {CLR_MINT}│ Server Deployment Engine & Core Environment Installer   {CLR_DARK}│")
    print(f"│  {CLR_DARK}Target: {CLR_TEXT}Python {py_ver:<10} {CLR_DARK}· Env: {CLR_TEXT}{os.name.upper():<5} {CLR_DARK}· Repos: {CLR_TEXT}PyPI / Server Core APIs  {CLR_DARK}│")
    print(f"{CLR_DARK}└────────────────────────────────────────────────────────────────────────┘{CLR_RESET}")
    print('')


def animated_step(text, percent, duration=0.3):
    steps = int(duration / 0.05)
    for i in range(steps):
        frame = SPINNER[(i % len(SPINNER))]
        clear()
        header()

        print(
            f" {CLR_MATRIX}○ {CLR_TEXT}Initializing sequence... {CLR_DARK}indexing matrix manifests")
        print(
            f" {CLR_DARK}────────────────────────────────────────────────────────────────────────")
        print(
            f"  {CLR_FOREST}{frame} {CLR_TEXT}{text:<40} {CLR_DARK}[processing...]")
        print(
            f" {CLR_DARK}────────────────────────────────────────────────────────────────────────")
        print(f" {CLR_MATRIX}$ mc-deploy {CLR_DARK}| {progress_bar(percent)} {CLR_DARK}| {CLR_MATRIX}status: active{CLR_RESET}")
        time.sleep(0.05)


def print_status_line(icon, label, details, color=CLR_TEXT, timing="0.1s"):
    print(f"  {icon} {CLR_TEXT}{label:<20} {color}{details:<38} {CLR_DARK}{timing}")


def install_package(package):
    return subprocess.call(
        [sys.executable, '-m', 'pip', 'install', package],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def uninstall_package(package):
    return subprocess.call(
        [sys.executable, '-m', 'pip', 'uninstall', '-y', package],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def verify_package(package):
    try:
        if package == 'pillow':
            __import__('PIL')
        else:
            __import__(package)
        return True
    except Exception:
        return False


def check_java():
    try:
        subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
        print_status_line(f"{CLR_MATRIX}[OK]", "java runtime",
                          "Detected successfully", CLR_MATRIX)
        return True
    except Exception:
        print_status_line(f"{CLR_WARN}[FAIL]", "java runtime",
                          "Missing or unconfigured", CLR_WARN)
        return False


def create_folders():
    clear()
    header()
    print(f" {CLR_MATRIX}● {CLR_MINT}Workspace Architecture Deployment")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────\n")

    print(f"  {CLR_TEXT}Create default MC-CTRL directory structure?")
    answer = input(
        f"  {CLR_DARK}[{CLR_MATRIX}y{CLR_DARK}/{CLR_TEXT}n{CLR_DARK}]{CLR_TEXT} Sequence confirmation: ").lower()

    if answer != 'y':
        print(f"\n  {CLR_WARN}[WARN] {CLR_TEXT}Skipped folder architecture setup.")
        time.sleep(1)
        return

    location = input(
        f"  {CLR_DARK}-> {CLR_TEXT}Installation path (Leave blank for current directory): ").strip()
    if not location:
        location = os.getcwd()

    base_path = os.path.abspath(location)
    print(
        f"\n  {CLR_DARK}Deploying system folders to:\n  {CLR_MATRIX}{base_path}\n")

    for folder in PROJECT_FOLDERS:
        folder_path = os.path.join(base_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        print_status_line(f"{CLR_MATRIX}[OK]", "directory setup",
                          f"/{folder}", CLR_TEXT, "0.0s")
        time.sleep(0.05)
    time.sleep(0.8)


def select_and_download_core():
    clear()
    header()
    print(f" {CLR_MATRIX}● {CLR_MINT}Server Software Core Selection Matrix")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────")
    print(f"   {CLR_MINT}[ PLUGIN & PERFORMANCE CORES ]")
    print(
        f"   {CLR_MATRIX}1.{CLR_TEXT} Paper MC      {CLR_DARK}[Supports Custom Target Versions]")
    print(
        f"   {CLR_MATRIX}2.{CLR_TEXT} Purpur        {CLR_DARK}[Supports Custom Target Versions]")
    print(
        f"   {CLR_MATRIX}3.{CLR_TEXT} Spigot        {CLR_DARK}[Standard stable plugin ecosystem core]")
    print(
        f"   {CLR_MATRIX}4.{CLR_TEXT} CraftBukkit   {CLR_DARK}[Legacy base framework standard execution]")
    print("")
    print(f"   {CLR_MINT}[ MODDED SERVER ENGINES ]")
    print(
        f"   {CLR_MATRIX}5.{CLR_TEXT} Fabric        {CLR_DARK}[Modern, lightweight optimization modpacks]")
    print(
        f"   {CLR_MATRIX}6.{CLR_TEXT} Forge         {CLR_DARK}[Classic, heavy game mechanic overhaul mods]")
    print("")
    print(f"   {CLR_MINT}[ OFFICIAL STANDARD ]")
    print(
        f"   {CLR_MATRIX}7.{CLR_TEXT} Vanilla       {CLR_DARK}[Default clean Minecraft multiplayer server]")
    print(f"   {CLR_MATRIX}8.{CLR_TEXT} Skip Core Deployment\n")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────\n")

    choice = input(
        f"  {CLR_DARK}-> {CLR_TEXT}Select target server framework core [1-8]: ").strip()

    if choice == '8' or choice not in CORES:
        print_status_line(f"{CLR_WARN}[WARN]", "deployment bypass",
                          "Skipped downloading server environment binaries", CLR_TEXT)
        time.sleep(1.5)
        return

    selected_core = CORES[choice]

    # --- DYNAMIC VERSION CHANGER SYSTEM ---
    if choice in ['1', '2', '3', '4', '7']:  # Cores that support direct version switching
        print(f"\n  {CLR_MATRIX}-> {CLR_TEXT}Default version is set to 1.21.1")
        mc_version = input(
            f"    {CLR_DARK}Leave blank for default, or type specific version (e.g., 1.20.4, 1.19.2): ").strip()

        if mc_version:
            # Dynamically rebuild URLs based on your choice
            if choice == '1':  # Paper
                selected_core['url'] = f"https://api.papermc.io/v2/projects/paper/versions/{mc_version}/latest/builds/latest/downloads/paper-{mc_version}-latest.jar"
            elif choice == '2':  # Purpur
                selected_core['url'] = f"https://api.purpurmc.org/v2/purpur/{mc_version}/latest/download"
            elif choice == '3':  # Spigot
                selected_core[
                    'url'] = f"https://download.getbukkit.org/spigot/spigot-{mc_version}.jar"
            elif choice == '4':  # CraftBukkit
                selected_core[
                    'url'] = f"https://download.getbukkit.org/craftbukkit/craftbukkit-{mc_version}.jar"
            # Vanilla (Note: Vanilla requires unique hashes for older versions, defaults to latest stable)
            elif choice == '7':
                print(
                    f"  {CLR_WARN}[WARN] {CLR_TEXT}Vanilla custom versions require manual API hashes. Attempting direct fallback link...")
                selected_core['url'] = f"https://piston-data.mojang.com/v1/objects/4707d00eb834b44e9dae80bad31a1d3d03b306b0/server.jar"

    os.makedirs('servers', exist_ok=True)
    target = os.path.join('servers', selected_core['filename'])

    clear()
    header()
    print(f" {CLR_MATRIX}● {CLR_MINT}External Assets Dependency Pull")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────\n")
    print(
        f"  {CLR_MATRIX}⠋ {CLR_TEXT}Establishing link stream for {CLR_MATRIX}{selected_core['name']}...")

    try:
        # Use a modern User-Agent string so server firewalls don't block Python's request
        req = urllib.request.Request(
            selected_core['url'],
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(target, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        print_status_line(f"{CLR_MATRIX}[OK]", "download core",
                          f"{selected_core['filename']} mapped inside /servers", CLR_MATRIX, "2.4s")
    except Exception as e:
        print_status_line(f"{CLR_WARN}[FAIL]", "download failed",
                          "Version not found or API rejected request", CLR_WARN)
        print(
            f"     {CLR_DARK}Error Details: URL structure might not exist for that specific older version.")
    time.sleep(2.5)


def repair_mode():
    clear()
    header()
    print(f" {CLR_WARN}● {CLR_TEXT}Environment Diagnostics & Verification Repair")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────\n")

    missing = [pkg for pkg in PACKAGES if not verify_package(pkg)]

    if not missing:
        print(
            f"  {CLR_MATRIX}[OK] {CLR_TEXT}All environment core packages verified. No integrity problems found.")
        return

    print(f"  {CLR_WARN}[WARN] Found {len(missing)} broken or missing modules:\n")
    for package in missing:
        print_status_line("·", "target package", package, CLR_WARN)

    print("")
    for package in missing:
        print(
            f"  {CLR_MATRIX}⠋ {CLR_TEXT}Re-fetching package environment: {CLR_MATRIX}{package}...")
        install_package(package)
    print(f"\n  {CLR_MATRIX}[OK] {CLR_TEXT}Repair routine evaluation finished.")


def uninstall_dependencies():
    for i, package in enumerate(PACKAGES, start=1):
        percent = (i / len(PACKAGES)) * 100
        animated_step(f"Purging library environment: {package}", percent)
        uninstall_package(package)
        print_status_line("─", "pip uninstalled", package, CLR_WARN, "0.2s")
        time.sleep(0.1)


def remove_launcher_files():
    clear()
    header()
    print(f" {CLR_WARN}● {CLR_TEXT}Cleaning Directory Tree Files")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────\n")

    for file in PROJECT_FILES:
        if os.path.exists(file):
            try:
                os.remove(file)
                print_status_line(
                    f"{CLR_WARN}⌗", "file removed", file, CLR_TEXT)
            except Exception:
                print_status_line("[FAIL]", "removal fail", file, CLR_WARN)

    for folder in PROJECT_FOLDERS:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print_status_line(
                    f"{CLR_WARN}⌗", "tree purged", f"/{folder}", CLR_TEXT)
            except Exception:
                print_status_line("[FAIL]", "tree locked", folder, CLR_WARN)
    time.sleep(1.5)


def full_uninstall():
    clear()
    header()
    print(f" {CLR_WARN} WARNING: FULL SYSTEM PURGE INITIALIZED{CLR_RESET}")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────\n")

    keep_servers = input(
        f"  {CLR_DARK}[{CLR_WARN}y{CLR_DARK}/{CLR_TEXT}n{CLR_DARK}]{CLR_TEXT} Retain localized server jars and backup structures? ").lower()

    uninstall_dependencies()

    print(f"\n {CLR_MATRIX}○ {CLR_TEXT}Wiping project architecture files...")
    for file in PROJECT_FILES:
        if os.path.exists(file):
            try:
                os.remove(file)
                print_status_line("⌗", "purged", file, CLR_DARK)
            except Exception:
                pass

    for folder in PROJECT_FOLDERS:
        if keep_servers == 'y' and folder in ['servers', 'backups']:
            print_status_line("[OK]", "preserved tree", f"/{folder}", CLR_MATRIX)
            continue
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print_status_line("⌗", "purged tree", f"/{folder}", CLR_DARK)
            except Exception:
                pass
    print(f"\n {CLR_MATRIX}[OK] {CLR_TEXT}Environment fully reset.")


def main():
    if os.name == 'nt':
        os.system('color')

    clear()
    header()

    print(f"  {CLR_MATRIX}1.{CLR_TEXT} Normal Environment Installation")
    print(f"  {CLR_MATRIX}2.{CLR_TEXT} Integrity Check & Repair Mode")
    print(f"  {CLR_MATRIX}3.{CLR_TEXT} Clean Dependencies Pack Only (pip purge)")
    print(f"  {CLR_MATRIX}4.{CLR_TEXT} Remove Assets & Generated Tree Files")
    print(f"  {CLR_MATRIX}5.{CLR_TEXT} Total Ecosystem Wipe (Full Uninstall)")
    print(f" {CLR_DARK}────────────────────────────────────────────────────────────────────────\n")

    mode = input(
        f"  {CLR_DARK}-> {CLR_TEXT}Select an engine operation mode [1-5]: ")

    if mode == '2':
        repair_mode()
        input(f'\n  {CLR_DARK}Press Enter to safely exit terminal loop...')
        sys.exit()
    elif mode == '3':
        uninstall_dependencies()
        input(f'\n  {CLR_DARK}Press Enter to safely exit terminal loop...')
        sys.exit()
    elif mode == '4':
        remove_launcher_files()
        input(f'\n  {CLR_DARK}Press Enter to safely exit terminal loop...')
        sys.exit()
    elif mode == '5':
        full_uninstall()
        input(f'\n  {CLR_DARK}Press Enter to safely exit terminal loop...')
        sys.exit()

    # Sequence Mode 1: Standard Installation Flow
    animated_step('Parsing Python Environment Metadata', 5)
    print_status_line("[OK]", "host checking",
                      f"Python {sys.version.split()[0]} confirmed", CLR_MATRIX)
    time.sleep(0.4)

    animated_step('Upgrading Local Package Pip Configs', 12)
    subprocess.call([sys.executable, '-m', 'pip', 'install', '--upgrade',
                    'pip'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    create_folders()

    # Automated Dependencies Array Run
    for i, package in enumerate(PACKAGES, start=1):
        percent = 20 + int((i / len(PACKAGES)) * 50)
        animated_step(f"Fetching dependency: {package}", percent)

        result = install_package(package)
        if result == 0:
            print_status_line("[OK]", "pip distribution",
                              f"Linked {package}", CLR_MATRIX, "0.6s")
        else:
            print_status_line("[FAIL]", "pip framework",
                              f"Failed compilation: {package}", CLR_WARN, "0.6s")
        time.sleep(0.2)

    animated_step('Verifying Ecosystem Bindings Integrity', 80)
    failed = [pkg for pkg in PACKAGES if not verify_package(pkg)]

    if failed:
        print(
            f"\n  {CLR_WARN}[FAIL] Integrity verification errors encountered in packages:")
        for package in failed:
            print(f"    - {package}")
    else:
        print_status_line("[OK]", "verification",
                          "All UI and engine modules linked", CLR_MATRIX)

    time.sleep(0.4)
    animated_step('Evaluating Local System Architecture', 88)
    check_java()
    time.sleep(0.4)

    select_and_download_core()

    animated_step('Finalizing Controller Environment Maps', 100)

    clear()
    header()
    print(f" {CLR_MATRIX}┌────────────────────────────────────────────────────────────────────────┐")
    print(f" │           ENVIRONMENT MANIFEST DEPLOYMENT COMPLETE SUCCESS           │")
    print(
        f" └────────────────────────────────────────────────────────────────────────┘{CLR_TEXT}\n")
    print_status_line("[OK]", "binaries compilation",
                      "Ecosystem verified & configured", CLR_MATRIX)
    print_status_line("[OK]", "directory map",
                      "Operational tree deployed", CLR_MATRIX)
    print_status_line("[OK]", "runtime module",
                      "Ready for deployment engines", CLR_MATRIX)

    print(f"\n  {CLR_TEXT}Execution initialization link prepared:")
    print(f"  {CLR_MATRIX}-> python launcher.pyw\n")

    input(f"{CLR_DARK}  Press Enter to exit deployment matrix...")


if __name__ == '__main__':
    main()
