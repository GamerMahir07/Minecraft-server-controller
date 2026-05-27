import os
import sys
import time
import subprocess

SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
PACKAGES = [
    'customtkinter',
    'psutil',
    'matplotlib',
    'tkinterdnd2',
    'pillow'
]


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def progress_bar(percent):
    filled = int(percent / 5)
    empty = 20 - filled
    return '[' + '█' * filled + '░' * empty + f'] {percent:.1f}%'


clear()

print('')
print('╔══════════════════════════════════════════════════════╗')
print('║                MC CTRL INSTALLER                    ║')
print('║          Professional Dependency Setup              ║')
print('╚══════════════════════════════════════════════════════╝')
print('')

print('Checking Python...')
time.sleep(1)

print(f'Python Version: {sys.version.split()[0]}')
print('')

print('Upgrading pip...')
subprocess.call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
print('')

for i, package in enumerate(PACKAGES, start=1):
    percent = (i - 1) / len(PACKAGES) * 100

    for frame in SPINNER:
        clear()

        print('╔══════════════════════════════════════════════════════╗')
        print('║                MC CTRL INSTALLER                    ║')
        print('╚══════════════════════════════════════════════════════╝')
        print('')

        print(f'{frame} Installing {package}...')
        print(progress_bar(percent))
        print('')

        time.sleep(0.07)

    result = subprocess.call([
        sys.executable,
        '-m',
        'pip',
        'install',
        package
    ])

    if result == 0:
        print(f'✓ {package} installed successfully.')
    else:
        print(f'✗ Failed to install {package}')

    time.sleep(0.5)

clear()

print('╔══════════════════════════════════════════════════════╗')
print('║                 INSTALL COMPLETE                    ║')
print('╚══════════════════════════════════════════════════════╝')
print('')
print(progress_bar(100))
print('')
print('Installed Packages:')
print('')

for p in PACKAGES:
    print(f'✓ {p}')

print('')
print('You can now launch: launcher.pyw')
print('')
input('Press Enter to exit...')