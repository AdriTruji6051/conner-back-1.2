#!/usr/bin/env python3
"""
Conner POS - Backend Preparation Script
Prepares the backend for compilation with PyInstaller.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple


# Configure logging with UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("compilation.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure stdout for UTF-8 on Windows
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def verify_directory_structure() -> bool:
    """
    Verify that the necessary directory structure exists.
    
    Returns:
        True if structure is correct, False otherwise
    """
    logger.info("Verifying directory structure...")
    
    required_dirs = [
        'templates',
        'static',
        'static/browser',
        'app',
        'config',
        'translations',
        'db',
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            logger.info(f"✓ Directory found: {dir_path}")
        else:
            logger.warning(f"✗ Directory not found: {dir_path}")
            if dir_path in ['templates', 'static', 'static/browser']:
                logger.error(f"Critical directory missing: {dir_path}")
                logger.error("Run compile_frontend.py first")
                all_exist = False
    
    return all_exist


def verify_frontend_files() -> bool:
    """
    Verify that compiled frontend files are present.
    
    Returns:
        True if files are present, False otherwise
    """
    logger.info("Verifying compiled frontend files...")
    
    # Verify index.html
    index_path = os.path.join('templates', 'index.html')
    if not os.path.exists(index_path):
        logger.error(f"index.html not found in {index_path}")
        logger.error("Run compile_frontend.py first")
        return False
    
    logger.info(f"✓ index.html found: {index_path}")
    
    # Verify static files
    static_browser = os.path.join('static', 'browser')
    if not os.path.exists(static_browser):
        logger.error(f"Static files folder not found: {static_browser}")
        logger.error("Run compile_frontend.py first")
        return False
    
    # Count files in static/browser
    file_count = sum([len(files) for _, _, files in os.walk(static_browser)])
    logger.info(f"✓ Static files found: {file_count} files in {static_browser}")
    
    if file_count == 0:
        logger.error("No files in static/browser")
        return False
    
    return True


def verify_backend_files() -> bool:
    """
    Verify that critical backend files are present.
    
    Returns:
        True if files are present, False otherwise
    """
    logger.info("Verifying backend files...")
    
    required_files = [
        'run.py',
        'requirements.txt',
        'config/config.py',
        'app/extensions.py',
        'app/routes_constants.py',
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"✓ File found: {file_path}")
        else:
            logger.error(f"✗ Critical file not found: {file_path}")
            all_exist = False
    
    return all_exist


def verify_dependencies() -> Tuple[bool, List[str]]:
    """
    Verify that all dependencies are in requirements.txt.
    
    Returns:
        Tuple with (all_present: bool, missing_dependencies: List[str])
    """
    logger.info("Verifying dependencies in requirements.txt...")
    
    required_packages = [
        'Flask',
        'Flask-Cors',
        'Flask-JWT-Extended',
        'Flask-SocketIO',
        'python-dotenv',
        'bcrypt',
        'Flask-SQLAlchemy',
        'greenlet',
        'gevent',
        'gevent-websocket',
        'Pillow',
        'num2words',
        'python-barcode',
        'pyinstaller',
    ]
    
    if not os.path.exists('requirements.txt'):
        logger.error("requirements.txt not found")
        return False, required_packages
    
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    missing = []
    for package in required_packages:
        package_lower = package.lower()
        if package_lower not in content:
            logger.warning(f"✗ Dependency not found in requirements.txt: {package}")
            missing.append(package)
        else:
            logger.info(f"✓ Dependency found: {package}")
    
    if missing:
        logger.warning(f"Missing dependencies: {', '.join(missing)}")
        return False, missing
    
    logger.info("✓ All dependencies are in requirements.txt")
    return True, []


def create_pyinstaller_data_list() -> List[Tuple[str, str]]:
    """
    Create a list of files and folders to include in PyInstaller.
    
    Returns:
        List of tuples (source, destination) for PyInstaller
    """
    logger.info("Generating file list for PyInstaller...")
    
    data_files = []
    
    # Directories to include
    directories = [
        ('templates', 'templates'),
        ('static', 'static'),
        ('translations', 'translations'),
        ('config', 'config'),
        ('app', 'app'),
    ]
    
    for src, dst in directories:
        if os.path.exists(src):
            data_files.append((src, dst))
            logger.info(f"✓ Include directory: {src} -> {dst}")
        else:
            logger.warning(f"✗ Directory not found: {src}")
    
    # Individual files
    individual_files = [
        ('.env', '.'),
    ]
    
    for src, dst in individual_files:
        if os.path.exists(src):
            data_files.append((src, dst))
            logger.info(f"✓ Include file: {src} -> {dst}")
        else:
            logger.info(f"ℹ Optional file not found: {src}")
    
    logger.info(f"Total elements to include: {len(data_files)}")
    return data_files


def verify_database_directory() -> bool:
    """
    Verify that the database directory exists.
    
    Returns:
        True if exists or was created correctly, False otherwise
    """
    logger.info("Verifying database directory...")
    
    db_dir = 'db'
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            logger.info(f"✓ Database directory created: {db_dir}")
        except Exception as e:
            logger.error(f"✗ Error creating database directory: {e}")
            return False
    else:
        logger.info(f"✓ Database directory exists: {db_dir}")
    
    return True


def check_environment_file() -> bool:
    """
    Verify that a .env file exists or create an example one.
    
    Returns:
        True if exists or was created correctly, False otherwise
    """
    logger.info("Verifying .env file...")
    
    if os.path.exists('.env'):
        logger.info("✓ .env file found")
        return True
    
    logger.warning("✗ .env file not found")
    logger.info("Creating example .env file...")
    
    env_content = """# Conner POS - Backend Configuration
SECRET_KEY=change-this-secret-key-in-production
JWT_SECRET_KEY=change-this-jwt-secret-key-in-production
TOKEN_HOURS=8
DB_PATH=./db/conner.db
HOST=0.0.0.0
PORT=5000
DEBUG=False
LOGGING=True
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        logger.info("✓ Example .env file created")
        logger.warning("⚠ IMPORTANT: Change secret keys before using in production")
        return True
    except Exception as e:
        logger.error(f"✗ Error creating .env file: {e}")
        return False


def generate_preparation_report() -> dict:
    """
    Generate a preparation status report.
    
    Returns:
        Dictionary with the report
    """
    logger.info("Generating preparation report...")
    
    report = {
        'directory_structure': verify_directory_structure(),
        'frontend_files': verify_frontend_files(),
        'backend_files': verify_backend_files(),
        'dependencies': verify_dependencies()[0],
        'database_directory': verify_database_directory(),
        'environment_file': check_environment_file(),
    }
    
    return report


def main() -> int:
    """
    Main script function.
    
    Returns:
        0 if everything was successful, 1 otherwise
    """
    logger.info("=" * 70)
    logger.info("BACKEND PREPARATION - CONNER POS")
    logger.info("=" * 70)
    
    try:
        # Generate preparation report
        report = generate_preparation_report()
        
        # Check if everything is ready
        all_ready = all(report.values())
        
        logger.info("\n" + "=" * 70)
        logger.info("PREPARATION REPORT")
        logger.info("=" * 70)
        
        for check, status in report.items():
            symbol = "✓" if status else "✗"
            logger.info(f"{symbol} {check.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")
        
        if all_ready:
            logger.info("\n" + "=" * 70)
            logger.info("✓ BACKEND READY FOR COMPILATION")
            logger.info("=" * 70)
            logger.info("The backend is ready to generate the executable")
            logger.info("Next step: python build_exe.py")
            return 0
        else:
            logger.error("\n" + "=" * 70)
            logger.error("✗ BACKEND NOT READY FOR COMPILATION")
            logger.error("=" * 70)
            logger.error("Fix the issues indicated above before continuing")
            
            # Specific suggestions
            if not report['frontend_files']:
                logger.error("\n💡 Run: python compile_frontend.py")
            
            if not report['dependencies']:
                logger.error("\n💡 Run: pip install -r requirements.txt")
            
            return 1
        
    except KeyboardInterrupt:
        logger.error("\n✗ Preparation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
