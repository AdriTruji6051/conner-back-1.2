#!/usr/bin/env python3
"""
Conner POS - Master Compilation Script
Orchestrates the execution of all compilation scripts.
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
from typing import Tuple


# Configure logging with UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("compilation.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure stdout for UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def print_banner(text: str, char: str = "="):
    """Print a formatted banner."""
    logger.info("\n" + char * 70)
    logger.info(f"  {text}")
    logger.info(char * 70 + "\n")


def run_script(script_name: str, description: str) -> Tuple[bool, float]:
    """
    Execute a Python script and return the result.
    
    Args:
        script_name: Name of the script to execute
        description: Description of the script
    
    Returns:
        Tuple with (success: bool, execution_time: float)
    """
    print_banner(f"PASO: {description}")
    logger.info(f"Executing: {script_name}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,  # Show output in real time
            timeout=1800  # 30 minutes timeout
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✓ {description} completed successfully")
            logger.info(f"  Execution time: {elapsed_time:.2f} seconds")
            return True, elapsed_time
        else:
            logger.error(f"✗ {description} failed with code {result.returncode}")
            return False, elapsed_time
            
    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        logger.error(f"✗ {description} exceeded time limit (30 minutes)")
        return False, elapsed_time
    except FileNotFoundError:
        logger.error(f"✗ Script not found: {script_name}")
        return False, 0
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"✗ Error executing {script_name}: {e}")
        return False, elapsed_time


def check_prerequisites() -> bool:
    """
    Verify that all prerequisites are installed.
    
    Returns:
        True if all requirements are satisfied, False otherwise
    """
    print_banner("PREREQUISITES CHECK")
    
    if not os.path.exists('check_requirements.py'):
        logger.error("Script check_requirements.py not found")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, 'check_requirements.py'],
            capture_output=False,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✓ All requirements are satisfied")
            return True
        else:
            logger.error("✗ Some requirements are not satisfied")
            logger.error("Please install the missing tools before continuing")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error checking requirements: {e}")
        return False


def generate_compilation_report(steps: list, total_time: float) -> None:
    """
    Generate a final compilation report.
    
    Args:
        steps: List of tuples (name, success, time)
        total_time: Total compilation time
    """
    print_banner("COMPILATION REPORT", "=")
    
    logger.info("Steps summary:")
    for name, success, exec_time in steps:
        symbol = "✓" if success else "✗"
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"  {symbol} {name:40} {status:10} ({exec_time:.2f}s)")
    
    logger.info(f"\nTotal compilation time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    
    all_success = all(success for _, success, _ in steps)
    
    if all_success:
        print_banner("✓ COMPILATION COMPLETED SUCCESSFULLY", "=")
        logger.info("The Conner POS executable has been generated correctly.")
        logger.info("\nInstaller location:")
        logger.info("  dist/Conner POS_Installer/")
        logger.info("\nTo install:")
        logger.info("  1. Go to dist/Conner POS_Installer/")
        logger.info("  2. Run install.bat as Administrator")
        logger.info("  3. Follow the on-screen instructions")
        logger.info("\nTo test without installing:")
        logger.info("  1. Go to dist/Conner POS/")
        logger.info("  2. Run Conner POS.exe")
        logger.info("  3. Abrir navegador en http://localhost:5000/dashboard")
    else:
        print_banner("✗ COMPILATION FAILED", "=")
        logger.error("One or more compilation steps failed.")
        logger.error("Review the error messages above for more details.")
        logger.error("Check compilation.log for detailed information.")


def create_compile_env_if_missing() -> bool:
    """
    Create .compile.env from .compile.env.example if it doesn't exist.
    
    Returns:
        True if exists or was created correctly, False otherwise
    """
    if os.path.exists('.compile.env'):
        logger.info("✓ .compile.env file found")
        return True
    
    logger.warning("✗ .compile.env file not found")
    
    if os.path.exists('.compile.env.example'):
        try:
            import shutil
            shutil.copy2('.compile.env.example', '.compile.env')
            logger.info("✓ .compile.env file created from .compile.env.example")
            logger.warning("⚠ Review and adjust configuration in .compile.env if necessary")
            return True
        except Exception as e:
            logger.error(f"✗ Error creating .compile.env: {e}")
            return False
    else:
        logger.error("✗ .compile.env.example file not found")
        return False


def main() -> int:
    """
    Main function of the master script.
    
    Returns:
        0 if everything was successful, 1 otherwise
    """
    start_time = time.time()
    compilation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print_banner("CONNER POS - FULL COMPILATION", "=")
    logger.info(f"Compilation date: {compilation_date}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    steps = []
    
    try:
        # Step 0: Create .compile.env if it doesn't exist
        if not create_compile_env_if_missing():
            logger.error("Could not create configuration file")
            return 1
        
        # Step 1: Check prerequisites
        if not check_prerequisites():
            logger.error("Prerequisites are not satisfied")
            logger.error("Run: python check_requirements.py")
            return 1
        
        # Step 2: Compile frontend
        success, exec_time = run_script(
            'compile_frontend.py',
            'Angular Frontend Compilation'
        )
        steps.append(('Frontend Compilation', success, exec_time))
        
        if not success:
            logger.error("Frontend compilation failed")
            generate_compilation_report(steps, time.time() - start_time)
            return 1
        
        # Step 3: Prepare backend
        success, exec_time = run_script(
            'prepare_backend.py',
            'Backend Preparation'
        )
        steps.append(('Backend Preparation', success, exec_time))
        
        if not success:
            logger.error("Backend preparation failed")
            generate_compilation_report(steps, time.time() - start_time)
            return 1
        
        # Step 4: Generate executable
        success, exec_time = run_script(
            'build_exe.py',
            'Executable Generation'
        )
        steps.append(('Executable Generation', success, exec_time))
        
        if not success:
            logger.error("Executable generation failed")
            generate_compilation_report(steps, time.time() - start_time)
            return 1
        
        # Generate final report
        total_time = time.time() - start_time
        generate_compilation_report(steps, total_time)
        
        return 0
        
    except KeyboardInterrupt:
        logger.error("\n✗ Compilation cancelled by user")
        total_time = time.time() - start_time
        if steps:
            generate_compilation_report(steps, total_time)
        return 1
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        total_time = time.time() - start_time
        if steps:
            generate_compilation_report(steps, total_time)
        return 1


if __name__ == '__main__':
    sys.exit(main())
