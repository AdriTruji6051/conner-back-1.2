#!/usr/bin/env python3
"""
Conner POS - Prerequisites Checker
Verifies that all necessary tools are installed before compiling.
"""

import subprocess
import sys
import os
from typing import Tuple, List


def check_command(command: str, version_flag: str = '--version') -> Tuple[bool, str]:
    """
    Check if a command is available on the system.
    
    Args:
        command: Name of the command to check
        version_flag: Flag to get version (default: --version)
    
    Returns:
        Tuple with (available: bool, version: str)
    """
    try:
        # On Windows, use shell=True to access global commands
        result = subprocess.run(
            [command, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
            shell=True  # Permite encontrar comandos en PATH del sistema
        )
        # Combine stdout and stderr as some commands use stderr for version
        output = result.stdout.strip() or result.stderr.strip()
        return True, output.split('\n')[0]  # First line of output
    except FileNotFoundError:
        return False, 'NOT FOUND'
    except subprocess.TimeoutExpired:
        return False, 'TIMEOUT'
    except Exception as e:
        return False, f'ERROR: {str(e)}'


def check_python_package(package: str) -> Tuple[bool, str]:
    """
    Check if a Python package is installed.
    
    Args:
        package: Name of the package to check
    
    Returns:
        Tuple with (installed: bool, version: str)
    """
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Extract version from output
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    return True, version
            return True, 'INSTALLED'
        return False, 'NOT INSTALLED'
    except Exception as e:
        return False, f'ERROR: {str(e)}'


def check_file_exists(filepath: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        filepath: Path to the file to check
    
    Returns:
        True if exists, False otherwise
    """
    return os.path.exists(filepath)


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_check(name: str, status: bool, details: str = ''):
    """
    Print the result of a check.
    
    Args:
        name: Name of what is being checked
        status: True if passed, False if failed
        details: Additional details (version, error message, etc.)
    """
    symbol = '✓' if status else '✗'
    color = '\033[92m' if status else '\033[91m'  # Green or Red
    reset = '\033[0m'
    
    print(f"{color}{symbol}{reset} {name:25} {details}")


def main() -> int:
    """
    Main function that executes all checks.
    
    Returns:
        0 if all checks passed, 1 otherwise
    """
    print_header("PREREQUISITES CHECK - CONNER POS")
    
    all_checks_passed = True
    
    # ========================================
    # Check system tools
    # ========================================
    print_header("System Tools")
    
    system_tools: List[Tuple[str, str, str]] = [
        ('python', '--version', 'Python 3.12+'),
        ('pip', '--version', 'pip (package manager)'),
        ('node', '--version', 'Node.js 18+'),
        ('npm', '--version', 'npm (package manager)'),
    ]
    
    for cmd, flag, description in system_tools:
        available, version = check_command(cmd, flag)
        print_check(description, available, version)
        if not available:
            all_checks_passed = False
    
    # ========================================
    # Check Angular CLI
    # ========================================
    print_header("Angular CLI")
    
    ng_available, ng_version = check_command('ng', 'version')
    print_check('Angular CLI', ng_available, ng_version if ng_available else 'NOT INSTALLED')
    if not ng_available:
        all_checks_passed = False
        print(f"\n  💡 Install with: npm install -g @angular/cli\n")
    
    # ========================================
    # Check Python packages
    # ========================================
    print_header("Required Python Packages")
    
    python_packages = [
        'flask',
        'flask-cors',
        'flask-jwt-extended',
        'flask-socketio',
        'python-dotenv',
        'bcrypt',
        'flask-sqlalchemy',
        'gevent',
        'pillow',
        'num2words',
        'python-barcode',
        'pyinstaller',
    ]
    
    for package in python_packages:
        installed, version = check_python_package(package)
        print_check(package, installed, version)
        if not installed:
            all_checks_passed = False
    
    if not all([check_python_package(pkg)[0] for pkg in python_packages]):
        print(f"\n  💡 Install missing packages with: pip install -r requirements.txt\n")
    
    # ========================================
    # Check file structure
    # ========================================
    print_header("File Structure")
    
    required_files = [
        ('requirements.txt', 'Python dependencies'),
        ('.env', 'Backend configuration'),
        ('../conner-front-1.2/package.json', 'Frontend project'),
        ('../conner-front-1.2/angular.json', 'Angular configuration'),
    ]
    
    for filepath, description in required_files:
        exists = check_file_exists(filepath)
        print_check(description, exists, filepath if exists else 'NOT FOUND')
        if not exists and filepath != '.env':  # .env is optional
            all_checks_passed = False
    
    # ========================================
    # Check compilation configuration file
    # ========================================
    print_header("Compilation Configuration")
    
    compile_env_exists = check_file_exists('.compile.env')
    print_check('.compile.env file', compile_env_exists, 
                '.compile.env' if compile_env_exists else 'NOT FOUND (use .compile.env.example)')
    
    if not compile_env_exists:
        print(f"\n  💡 Copy .compile.env.example to .compile.env and adjust configuration\n")
    
    # ========================================
    # Final summary
    # ========================================
    print_header("SUMMARY")
    
    if all_checks_passed:
        print("✓ All requirements are installed and configured correctly.")
        print("✓ The system is ready to compile Conner POS.\n")
        print("Next step: python compile_all.py\n")
        return 0
    else:
        print("✗ Some requirements are not satisfied.")
        print("✗ Please install the missing tools before continuing.\n")
        print("See COMPILATION_PLAN.md for more details.\n")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✗ Check cancelled by user.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}\n")
        sys.exit(1)
