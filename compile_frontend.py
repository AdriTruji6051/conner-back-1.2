#!/usr/bin/env python3
"""
Conner POS - Frontend Compilation Script
Compiles the Angular project and copies files to the backend.
"""

import os
import sys
import socket
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv


# Configure logging with UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("compilation.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure stdout for UTF-8 on Windows
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def load_compile_config() -> dict:
    """
    Load configuration from .compile.env
    
    Returns:
        Dictionary with configuration
    """
    logger.info("Loading configuration from .compile.env...")
    
    if not os.path.exists('.compile.env'):
        logger.error(".compile.env file not found")
        logger.info("Copy .compile.env.example to .compile.env and adjust configuration")
        sys.exit(1)
    
    load_dotenv('.compile.env')
    
    config = {
        'frontend_path': os.getenv('FRONTEND_PATH', '../conner-front-1.2'),
        'backend_path': os.getenv('BACKEND_PATH', '.'),
        'backend_ip': os.getenv('BACKEND_IP'),  # Opcional
        'backend_port': os.getenv('BACKEND_PORT', '5000'),
        'angular_build_config': os.getenv('ANGULAR_BUILD_CONFIG', 'production'),
        'verbose_logging': os.getenv('VERBOSE_LOGGING', 'true').lower() == 'true',
    }
    
    logger.info(f"Configuration loaded: {config}")
    return config


def get_lan_ip() -> str:
    """
    Automatically detect the server's LAN IP.
    
    Returns:
        LAN IP as string
    """
    logger.info("Detecting server LAN IP...")
    
    try:
        # Create UDP socket (doesn't need real connection)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to external address (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        logger.info(f"LAN IP detected: {ip}")
        return ip
    except Exception as e:
        logger.warning(f"Error detecting LAN IP: {e}")
        logger.warning("Using localhost as fallback")
        return "127.0.0.1"


def validate_frontend_path(frontend_path: str) -> bool:
    """
    Validate that the frontend path exists and contains necessary files.
    
    Args:
        frontend_path: Path to frontend project
    
    Returns:
        True if valid, False otherwise
    """
    logger.info(f"Validating frontend path: {frontend_path}")
    
    if not os.path.exists(frontend_path):
        logger.error(f"Frontend path does not exist: {frontend_path}")
        return False
    
    required_files = ['package.json', 'angular.json', 'src']
    for file in required_files:
        file_path = os.path.join(frontend_path, file)
        if not os.path.exists(file_path):
            logger.error(f"Required file/folder not found: {file_path}")
            return False
    
    logger.info("Frontend path validated correctly")
    return True


def update_environment_file(frontend_path: str, backend_ip: str, backend_port: str) -> Optional[str]:
    """
    Update environment.ts file with backend IP.
    
    Args:
        frontend_path: Path to frontend project
        backend_ip: Backend IP
        backend_port: Backend port
    
    Returns:
        Backup file path or None if error
    """
    logger.info("Updating environment.ts file...")
    
    env_file = os.path.join(frontend_path, 'src', 'app', 'environment', 'environment.ts')
    
    if not os.path.exists(env_file):
        logger.error(f"environment.ts file not found: {env_file}")
        return None
    
    # Create backup
    backup_file = env_file + '.backup'
    try:
        shutil.copy2(env_file, backup_file)
        logger.info(f"Backup created: {backup_file}")
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None
    
    # Update content
    api_url = f"http://{backend_ip}:{backend_port}"
    content = f"""export const ENVIRONMENT = {{
    conner_api_url: '{api_url}'
}};"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"environment.ts updated with API URL: {api_url}")
        return backup_file
    except Exception as e:
        logger.error(f"Error updating environment.ts: {e}")
        # Restore backup
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, env_file)
        return None


def run_angular_build(frontend_path: str, build_config: str) -> bool:
    """
    Execute Angular build.
    
    Args:
        frontend_path: Path to frontend project
        build_config: Build configuration (production or development)
    
    Returns:
        True if build was successful, False otherwise
    """
    logger.info(f"Starting Angular build (configuration: {build_config})...")
    
    try:
        # Change to frontend directory
        original_dir = os.getcwd()
        os.chdir(frontend_path)
        
        # Execute ng build with shell=True for Windows
        cmd = f'ng build --configuration {build_config}'
        logger.info(f"Executing command: {cmd}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
            shell=True  # Necessary on Windows to find ng
        )
        
        # Return to original directory
        os.chdir(original_dir)
        
        if result.returncode == 0:
            logger.info("Angular build completed successfully")
            logger.debug(f"Output: {result.stdout}")
            return True
        else:
            logger.error("Error in Angular build")
            logger.error(f"Exit code: {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Angular build timeout (>10 minutes)")
        os.chdir(original_dir)
        return False
    except Exception as e:
        logger.error(f"Error executing Angular build: {e}")
        os.chdir(original_dir)
        return False


def copy_compiled_files(frontend_path: str, backend_path: str) -> bool:
    """
    Copy compiled frontend files to backend.
    
    Args:
        frontend_path: Path to frontend project
        backend_path: Path to backend project
    
    Returns:
        True if copy was successful, False otherwise
    """
    logger.info("Copying compiled files to backend...")
    
    # Source paths
    dist_path = os.path.join(frontend_path, 'dist', 'conner-front-1.2')
    browser_path = os.path.join(dist_path, 'browser')
    
    if not os.path.exists(browser_path):
        logger.error(f"Build folder not found: {browser_path}")
        return False
    
    # Destination paths
    templates_dir = os.path.join(backend_path, 'templates')
    static_dir = os.path.join(backend_path, 'static')
    
    try:
        # Create directories if they don't exist
        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(static_dir, exist_ok=True)
        logger.info(f"Destination directories prepared: {templates_dir}, {static_dir}")
        
        # Copy index.html to templates/
        index_src = os.path.join(browser_path, 'index.html')
        index_dst = os.path.join(templates_dir, 'index.html')
        
        if os.path.exists(index_src):
            shutil.copy2(index_src, index_dst)
            logger.info(f"index.html copied to {index_dst}")
            
            # Fix static file paths in index.html
            fix_static_paths(index_dst)
        else:
            logger.error(f"index.html not found in {index_src}")
            return False
        
        # Copy all browser/ content to static/browser/
        static_browser_dir = os.path.join(static_dir, 'browser')
        
        # Remove existing folder if it exists
        if os.path.exists(static_browser_dir):
            shutil.rmtree(static_browser_dir)
            logger.info(f"Existing folder removed: {static_browser_dir}")
        
        # Copy new folder
        shutil.copytree(browser_path, static_browser_dir)
        logger.info(f"Static files copied to {static_browser_dir}")
        
        # Count copied files
        file_count = sum([len(files) for _, _, files in os.walk(static_browser_dir)])
        logger.info(f"Total files copied: {file_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error copying files: {e}")
        return False


def fix_static_paths(index_path: str) -> bool:
    """
    Fix static file paths in index.html for Flask.
    
    Args:
        index_path: Path to index.html file
    
    Returns:
        True if paths were fixed, False otherwise
    """
    logger.info("Fixing static file paths in index.html...")
    
    try:
        # Read content
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace relative paths with Flask absolute paths
        # JS and CSS files
        content = content.replace('src="', 'src="/static/browser/')
        content = content.replace('href="', 'href="/static/browser/')
        
        # Fix paths that already had /static/browser/ (avoid duplicates)
        content = content.replace('src="/static/browser//static/browser/', 'src="/static/browser/')
        content = content.replace('href="/static/browser//static/browser/', 'href="/static/browser/')
        
        # Fix font and external resource paths (should not have /static/browser/)
        content = content.replace('src="/static/browser/https://', 'src="https://')
        content = content.replace('href="/static/browser/https://', 'href="https://')
        
        # Save modified content
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("Static file paths fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing static file paths: {e}")
        return False


def restore_environment_file(backup_file: str) -> bool:
    """
    Restore environment.ts file from backup.
    
    Args:
        backup_file: Backup file path
    
    Returns:
        True if restoration was successful, False otherwise
    """
    if not backup_file or not os.path.exists(backup_file):
        logger.warning("No backup file to restore")
        return False
    
    try:
        original_file = backup_file.replace('.backup', '')
        shutil.copy2(backup_file, original_file)
        os.remove(backup_file)
        logger.info("environment.ts file restored from backup")
        return True
    except Exception as e:
        logger.error(f"Error restoring environment.ts: {e}")
        return False


def main() -> int:
    """
    Main script function.
    
    Returns:
        0 if everything was successful, 1 otherwise
    """
    logger.info("=" * 70)
    logger.info("FRONTEND COMPILATION - CONNER POS")
    logger.info("=" * 70)
    
    backup_file = None
    
    try:
        # 1. Load configuration
        config = load_compile_config()
        
        # 2. Validate frontend path
        if not validate_frontend_path(config['frontend_path']):
            return 1
        
        # 3. Detect LAN IP (or use configured one)
        backend_ip = config['backend_ip'] or get_lan_ip()
        
        # 4. Update environment.ts
        backup_file = update_environment_file(
            config['frontend_path'],
            backend_ip,
            config['backend_port']
        )
        
        if not backup_file:
            logger.error("Error updating environment.ts")
            return 1
        
        # 5. Execute Angular build
        if not run_angular_build(config['frontend_path'], config['angular_build_config']):
            logger.error("Error in Angular build")
            restore_environment_file(backup_file)
            return 1
        
        # 6. Copy compiled files
        if not copy_compiled_files(config['frontend_path'], config['backend_path']):
            logger.error("Error copying compiled files")
            restore_environment_file(backup_file)
            return 1
        
        # 7. Restore environment.ts
        restore_environment_file(backup_file)
        
        logger.info("=" * 70)
        logger.info("✓ FRONTEND COMPILATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"API URL configured: http://{backend_ip}:{config['backend_port']}")
        logger.info(f"Files copied to: {config['backend_path']}/templates and /static")
        
        return 0
        
    except KeyboardInterrupt:
        logger.error("\n✗ Compilation cancelled by user")
        if backup_file:
            restore_environment_file(backup_file)
        return 1
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        if backup_file:
            restore_environment_file(backup_file)
        return 1


if __name__ == '__main__':
    sys.exit(main())
