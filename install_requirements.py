import os
import sys
import time
import shutil
import urllib.request
import subprocess

SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

PACKAGES = [
    'customtkinter',
    'psutil',
    'matplotlib',
    'tkinterdnd2',
    'pillow'
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

PAPER_URL = (
    'https://api.papermc.io/v2/projects/paper/versions/'
    '1.21.1/builds/130/downloads/paper-1.21.1-130.jar'
)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def progress_bar(percent):
    filled = int(percent / 5)
    empty = 20 - filled

    return '[' + '█' * filled + '░' * empty + f'] {percent:.1f}%'


def header():
    print('')
    print('  ███╗   ███╗ ██████╗      ██████╗████████╗██████╗ ██╗     ')
    print('  ████╗ ████║██╔════╝     ██╔════╝╚══██╔══╝██╔══██╗██║     ')
    print('  ██╔████╔██║██║          ██║        ██║   ██████╔╝██║     ')
    print('  ██║╚██╔╝██║██║          ██║        ██║   ██╔══██╗██║     ')
    print('  ██║ ╚═╝ ██║╚██████╗     ╚██████╗   ██║   ██║  ██║███████╗')
    print('  ╚═╝     ╚═╝ ╚═════╝      ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝')
    print('')
    print('           Minecraft Server Control Center')
    print('')


def animated_step(text, percent):
    for frame in SPINNER:
        clear()

        header()

        print(f'{frame} {text}')
        print(progress_bar(percent))
        print('')

        time.sleep(0.05)


def install_package(package):
    return subprocess.call([
        sys.executable,
        '-m',
        'pip',
        'install',
        package
    ])


def uninstall_package(package):
    return subprocess.call([
        sys.executable,
        '-m',
        'pip',
        'uninstall',
        '-y',
        package
    ])


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
        subprocess.check_output(
            ['java', '-version'],
            stderr=subprocess.STDOUT
        )

        print('✓ Java detected')
        return True

    except Exception:
        print('✗ Java not found')
        return False


def create_folders():
    print('\nFolder Setup\n')

    answer = input('Create MC CTRL folders? (y/n): ').lower()

    if answer != 'y':
        print('\nSkipping folder creation.')
        return

    location = input(
        '\nFolder location (leave blank for current directory): '
    ).strip()

    if not location:
        location = os.getcwd()

    base_path = os.path.abspath(location)

    print(f'\nCreating folders in:\n{base_path}\n')

    for folder in PROJECT_FOLDERS:
        folder_path = os.path.join(base_path, folder)

        os.makedirs(folder_path, exist_ok=True)

        print(f'✓ Created: {folder_path}')


def download_paper():
    answer = input('\nDownload Paper server jar? (y/n): ').lower()

    if answer != 'y':
        return

    os.makedirs('servers', exist_ok=True)

    target = os.path.join('servers', 'paper-server.jar')

    print('\nDownloading Paper server...')

    urllib.request.urlretrieve(PAPER_URL, target)

    print('✓ Download complete')


def repair_mode():
    print('\nRepair Mode Started\n')

    missing = []

    for package in PACKAGES:
        if not verify_package(package):
            missing.append(package)

    if not missing:
        print('✓ No missing dependencies detected.')
        return

    print('Missing packages found:\n')

    for package in missing:
        print('-', package)

    print('')

    for package in missing:
        print(f'Repairing {package}...')
        install_package(package)


def uninstall_dependencies():
    print('\nUninstalling dependencies...\n')

    for i, package in enumerate(PACKAGES, start=1):
        percent = (i / len(PACKAGES)) * 100

        animated_step(f'Removing {package}...', percent)

        uninstall_package(package)

        print(f'✓ Removed {package}')

        time.sleep(0.5)

    print('\n✓ Dependencies removed')


def remove_launcher_files():
    print('\nRemoving launcher files...\n')

    for file in PROJECT_FILES:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f'✓ Deleted file: {file}')

            except Exception as e:
                print(f'✗ Failed to delete {file}')
                print(e)

    for folder in PROJECT_FOLDERS:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f'✓ Deleted folder: {folder}')

            except Exception as e:
                print(f'✗ Failed to delete {folder}')
                print(e)


def full_uninstall():
    print('\nWARNING: FULL UNINSTALL MODE\n')

    keep_servers = input(
        'Keep servers/backups folder? (y/n): '
    ).lower()

    uninstall_dependencies()

    print('\nRemoving project files...\n')

    for file in PROJECT_FILES:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f'✓ Deleted file: {file}')

            except Exception as e:
                print(f'✗ Failed to delete {file}')
                print(e)

    for folder in PROJECT_FOLDERS:

        if keep_servers == 'y' and folder in ['servers', 'backups']:
            print(f'✓ Preserved folder: {folder}')
            continue

        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f'✓ Deleted folder: {folder}')

            except Exception as e:
                print(f'✗ Failed to delete {folder}')
                print(e)

    print('\n✓ Full uninstall complete')


clear()

header()

print('1. Normal Install')
print('2. Repair Mode')
print('3. Uninstall Dependencies Only')
print('4. Remove Launcher Files')
print('5. Full Uninstall')
print('')

mode = input('Select option: ')

if mode == '2':
    repair_mode()

    input('\nPress Enter to exit...')
    sys.exit()

elif mode == '3':
    uninstall_dependencies()

    input('\nPress Enter to exit...')
    sys.exit()

elif mode == '4':
    remove_launcher_files()

    input('\nPress Enter to exit...')
    sys.exit()

elif mode == '5':
    full_uninstall()

    input('\nPress Enter to exit...')
    sys.exit()

animated_step('Checking Python...', 5)

print(f'✓ Python {sys.version.split()[0]} detected')

time.sleep(1)

animated_step('Upgrading pip...', 10)

subprocess.call([
    sys.executable,
    '-m',
    'pip',
    'install',
    '--upgrade',
    'pip'
])

animated_step('Creating folders...', 20)

create_folders()

time.sleep(1)

print('\nDependency Installation\n')

for i, package in enumerate(PACKAGES, start=1):
    percent = 20 + (i / len(PACKAGES)) * 50

    animated_step(f'Installing {package}...', percent)

    result = install_package(package)

    if result == 0:
        print(f'✓ {package} installed')

    else:
        print(f'✗ Failed to install {package}')

    time.sleep(0.5)

animated_step('Verifying dependencies...', 80)

failed = []

for package in PACKAGES:
    if not verify_package(package):
        failed.append(package)

if failed:
    print('\nVerification failed:\n')

    for package in failed:
        print('-', package)

else:
    print('\n✓ All dependencies verified')

print('')

animated_step('Checking Java...', 85)

check_java()

print('')

download_paper()

animated_step('Finalizing setup...', 100)

print('\n=========================================')
print('       MC CTRL INSTALL COMPLETE')
print('=========================================')
print('')
print('✓ Dependencies installed')
print('✓ Environment verified')
print('✓ Setup complete')
print('')
print('You can now launch:')
print('launcher.pyw')
print('')

input('Press Enter to exit...')
