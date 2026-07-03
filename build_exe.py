#!/usr/bin/env python3
"""
Conner POS - Executable Generation Script
Generates the PyInstaller .spec file and compiles the executable.
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv


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


def build_and_copy_frontend() -> bool:
    """
    Build Angular frontend and copy to backend static folder.
    Also fixes base href in templates/index.html.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 70)
    logger.info("BUILDING ANGULAR FRONTEND")
    logger.info("=" * 70)
    
    frontend_dir = os.path.join('..', 'conner-front-1.2')
    
    if not os.path.exists(frontend_dir):
        logger.error(f"Frontend directory not found: {frontend_dir}")
        return False
    
    try:
        # Build Angular app using npm (works better with PATH)
        logger.info("Building Angular application...")
        result = subprocess.run(
            ['npm', 'run', 'build'],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
            shell=True  # Use shell to find npm in PATH
        )
        
        if result.returncode != 0:
            logger.error("Angular build failed")
            logger.error(f"Error output: {result.stderr}")
            return False
        
        logger.info("✓ Angular build completed successfully")
        
        # Copy static files
        logger.info("Copying static files to backend...")
        dist_browser = os.path.join(frontend_dir, 'dist', 'conner-front-1.2', 'browser')
        backend_static = os.path.join('static', 'browser')
        
        if os.path.exists(backend_static):
            shutil.rmtree(backend_static)
        
        shutil.copytree(dist_browser, backend_static)
        logger.info("✓ Static files copied")
        
        # Copy and fix index.html
        logger.info("Copying and fixing index.html...")
        index_source = os.path.join(dist_browser, 'index.html')
        index_dest = os.path.join('templates', 'index.html')
        
        with open(index_source, 'r', encoding='utf-8') as f:
            index_content = f.read()
        
        # Fix base href
        index_content = index_content.replace('<base href="/">', '<base href="/page/">')
        
        with open(index_dest, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        logger.info("✓ index.html copied and base href fixed to /page/")
        
        # Verify
        with open(index_dest, 'r', encoding='utf-8') as f:
            verify_content = f.read()
            if '<base href="/page/">' in verify_content:
                logger.info("✓ Base href verified: /page/")
            else:
                logger.warning("⚠ Base href verification failed")
        
        # Check i18n files
        i18n_path = os.path.join(backend_static, 'i18n')
        if os.path.exists(i18n_path):
            i18n_files = [f for f in os.listdir(i18n_path) if f.endswith('.json')]
            logger.info(f"✓ i18n files found: {len(i18n_files)}")
        else:
            logger.warning("⚠ i18n directory not found")
        
        logger.info("=" * 70)
        logger.info("✓ FRONTEND BUILD AND COPY COMPLETED")
        logger.info("=" * 70)
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("✗ Angular build timeout (>10 minutes)")
        return False
    except FileNotFoundError:
        logger.error("✗ Angular CLI (ng) not found")
        logger.error("Install Angular CLI with: npm install -g @angular/cli")
        return False
    except Exception as e:
        logger.error(f"✗ Error building frontend: {e}")
        return False


def verify_network_config() -> None:
    """
    Verify and display network configuration of the server.
    """
    logger.info("=" * 70)
    logger.info("NETWORK CONFIGURATION")
    logger.info("=" * 70)
    
    # Load .env
    load_dotenv()
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "5000")
    
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    
    if host == "127.0.0.1":
        logger.warning("⚠ WARNING: Backend configured for localhost only")
        logger.warning("  Other computers won't be able to connect")
        logger.warning("  Change HOST to 0.0.0.0 in .env for network access")
    elif host == "0.0.0.0":
        logger.info("✓ Backend configured for network access")
        
        # Get local IP
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"✓ Local IP detected: {local_ip}")
            logger.info(f"  Access from other computers: http://{local_ip}:{port}/")
        except Exception as e:
            logger.warning(f"⚠ Could not detect local IP: {e}")
    
    logger.info("=" * 70)


def load_compile_config() -> dict:
    """
    Load configuration from .compile.env
    
    Returns:
        Dictionary with configuration
    """
    logger.info("Loading configuration from .compile.env...")
    
    if not os.path.exists('.compile.env'):
        logger.error(".compile.env file not found")
        sys.exit(1)
    
    load_dotenv('.compile.env')
    
    config = {
        'exe_name': os.getenv('EXE_NAME', 'Conner POS'),
        'pyinstaller_options': os.getenv('PYINSTALLER_OPTIONS', '--onedir --windowed'),
        'icon_path': os.getenv('ICON_PATH'),
        'use_upx': os.getenv('USE_UPX', 'true').lower() == 'true',
        'clean_temp_files': os.getenv('CLEAN_TEMP_FILES', 'true').lower() == 'true',
    }
    
    logger.info(f"Configuration loaded: {config}")
    return config


def generate_spec_file(config: dict) -> str:
    """
    Generate the PyInstaller .spec file.
    
    Args:
        config: Dictionary with configuration
    
    Returns:
        Path to the generated .spec file
    """
    logger.info("Generating PyInstaller .spec file...")
    
    exe_name = config['exe_name']
    icon_path = config['icon_path']
    use_upx = config['use_upx']
    
    # Prepare icon line
    icon_line = f"icon='{icon_path}'" if icon_path and os.path.exists(icon_path) else "icon=None"
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# Conner POS - PyInstaller Specification File
# Auto-generated by build_exe.py

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('translations', 'translations'),
        ('config', 'config'),
        ('app', 'app'),
        ('.env', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask.templating',
        'flask_sqlalchemy',
        'flask_jwt_extended',
        'flask_socketio',
        'flask_cors',
        'gevent',
        'gevent.monkey',
        'gevent._gevent_c_abstract_linkable',
        'gevent._gevent_cevent',
        'gevent._gevent_c_greenlet_primitives',
        'gevent._gevent_c_hub_local',
        'gevent._gevent_c_ident',
        'gevent._gevent_c_imap',
        'gevent._gevent_c_loop',
        'gevent._gevent_c_semaphore',
        'gevent._gevent_c_tracer',
        'gevent._gevent_c_waiter',
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'bcrypt',
        'PIL',
        'PIL._imaging',
        'num2words',
        'barcode',
        'barcode.writer',
        'python_dotenv',
        'engineio',
        'engineio.async_drivers.gevent',
        'socketio',
        'werkzeug',
        'werkzeug.security',
        'jinja2',
        'click',
        'itsdangerous',
        'greenlet',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={str(use_upx)},
    console=True,  # Enable console window for logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx={str(use_upx)},
    upx_exclude=[],
    name='{exe_name}',
)
"""
    
    spec_filename = 'conner.spec'
    
    try:
        with open(spec_filename, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        logger.info(f"✓ .spec file generated: {spec_filename}")
        return spec_filename
    except Exception as e:
        logger.error(f"✗ Error generating .spec file: {e}")
        sys.exit(1)


def run_pyinstaller(spec_file: str) -> bool:
    """
    Execute PyInstaller with the .spec file.
    
    Args:
        spec_file: Path to the .spec file
    
    Returns:
        True if compilation was successful, False otherwise
    """
    logger.info("Starting compilation with PyInstaller...")
    logger.info("This may take several minutes...")
    
    try:
        cmd = ['pyinstaller', '--clean', spec_file]
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos de timeout
        )
        
        if result.returncode == 0:
            logger.info("✓ PyInstaller compilation completed successfully")
            
            # Show last lines of output
            output_lines = result.stdout.strip().split('\n')
            logger.info("Last lines of output:")
            for line in output_lines[-10:]:
                logger.info(f"  {line}")
            
            return True
        else:
            logger.error("✗ Error in PyInstaller compilation")
            logger.error(f"Exit code: {result.returncode}")
            logger.error("Error output:")
            for line in result.stderr.strip().split('\n'):
                logger.error(f"  {line}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ PyInstaller compilation timeout (>30 minutes)")
        return False
    except FileNotFoundError:
        logger.error("✗ PyInstaller not found")
        logger.error("Install PyInstaller with: pip install pyinstaller")
        return False
    except Exception as e:
        logger.error(f"✗ Error executing PyInstaller: {e}")
        return False


def verify_executable(exe_name: str) -> bool:
    """
    Verify that the executable was generated correctly.
    
    Args:
        exe_name: Name of the executable
    
    Returns:
        True if the executable exists, False otherwise
    """
    logger.info("Verifying generated executable...")
    
    exe_path = os.path.join('dist', exe_name, f'{exe_name}.exe')
    
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        logger.info(f"✓ Executable generated: {exe_path}")
        logger.info(f"  Size: {file_size:.2f} MB")
        return True
    else:
        logger.error(f"✗ Executable not found: {exe_path}")
        return False


def clean_temp_files() -> None:
    """
    Clean temporary compilation files.
    """
    logger.info("Cleaning temporary files...")
    
    temp_dirs = ['build']
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"✓ Temporary directory removed: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠ Could not remove {temp_dir}: {e}")


def create_installer_structure(exe_name: str) -> bool:
    """
    Create installer structure with installation scripts.
    
    Args:
        exe_name: Name of the executable
    
    Returns:
        True if created successfully, False otherwise
    """
    logger.info("Creating installer structure...")
    
    dist_path = os.path.join('dist', exe_name)
    
    if not os.path.exists(dist_path):
        logger.error(f"Distribution folder not found: {dist_path}")
        return False
    
    # Create installation script
    install_bat = f"""@echo off
echo ========================================
echo Instalando Conner POS...
echo ========================================

REM Crear carpeta de instalación
set INSTALL_DIR=%ProgramFiles%\\Conner POS
mkdir "%INSTALL_DIR%" 2>nul

REM Copiar archivos
echo Copiando archivos...
xcopy /E /I /Y "{exe_name}" "%INSTALL_DIR%"

REM Crear acceso directo en el escritorio
echo Creando acceso directo en el escritorio...
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%userprofile%\\Desktop\\Conner POS.lnk');$s.TargetPath='%INSTALL_DIR%\\{exe_name}.exe';$s.Save()"

REM Crear acceso directo en el menú inicio
echo Creando acceso directo en el menú inicio...
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%appdata%\\Microsoft\\Windows\\Start Menu\\Programs\\Conner POS.lnk');$s.TargetPath='%INSTALL_DIR%\\{exe_name}.exe';$s.Save()"

echo.
echo ========================================
echo Instalación completada exitosamente.
echo ========================================
echo.
echo Puedes ejecutar Conner POS desde:
echo - Acceso directo en el escritorio
echo - Menú Inicio
echo - %INSTALL_DIR%\\{exe_name}.exe
echo.
pause
"""
    
    # Create uninstallation script
    uninstall_bat = f"""@echo off
echo ========================================
echo Desinstalando Conner POS...
echo ========================================

set INSTALL_DIR=%ProgramFiles%\\Conner POS

REM Eliminar accesos directos
echo Eliminando accesos directos...
del "%userprofile%\\Desktop\\Conner POS.lnk" 2>nul
del "%appdata%\\Microsoft\\Windows\\Start Menu\\Programs\\Conner POS.lnk" 2>nul

REM Eliminar carpeta de instalación
echo Eliminando archivos de programa...
rmdir /S /Q "%INSTALL_DIR%" 2>nul

echo.
echo ========================================
echo Desinstalación completada.
echo ========================================
echo.
echo NOTA: Los datos de la base de datos no se eliminaron.
echo Si deseas eliminarlos, borra manualmente la carpeta:
echo %INSTALL_DIR%\\db
echo.
pause
"""
    
    # Crear script de configuración de firewall
    firewall_bat = """@echo off
echo ========================================
echo Configurando Firewall para Conner POS
echo ========================================
echo.

REM Verificar privilegios de administrador
net session >nul 2>&1
if %%errorLevel%% neq 0 (
    echo ERROR: Este script requiere privilegios de administrador.
    echo.
    echo Por favor:
    echo 1. Haz clic derecho en este archivo
    echo 2. Selecciona "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo Eliminando regla anterior si existe...
netsh advfirewall firewall delete rule name="Conner POS - Flask Server" >nul 2>&1

echo Creando regla de firewall para el puerto 5000...
netsh advfirewall firewall add rule name="Conner POS - Flask Server" dir=in action=allow protocol=TCP localport=5000 profile=any

if %%errorLevel%% equ 0 (
    echo.
    echo ========================================
    echo CONFIGURACION EXITOSA
    echo ========================================
    echo.
    echo El servidor Flask ahora es accesible desde otros equipos en la red local.
    echo.
    echo PROXIMOS PASOS:
    echo.
    echo 1. Inicia el servidor Conner POS
    echo.
    echo 2. Obten tu IP local ejecutando: ipconfig
    echo    Busca "Direccion IPv4" (ejemplo: 192.168.1.126^)
    echo.
    echo 3. Desde otros equipos en la red, accede a:
    echo    http://[TU_IP]:5000/
    echo.
    echo    Ejemplo: http://192.168.1.126:5000/
    echo.
) else (
    echo.
    echo ERROR: No se pudo crear la regla de firewall.
    echo.
)

pause
"""
    
    # Crear README
    readme_txt = """CONNER POS - Sistema de Punto de Venta
=======================================

INSTALACIÓN
-----------
1. Ejecutar install.bat como Administrador
2. Seguir las instrucciones en pantalla
3. El acceso directo se creará en el escritorio
4. IMPORTANTE: Ejecutar setup_firewall.bat como Administrador
   (Necesario para acceso desde otros equipos en la red)

PRIMER USO
----------
1. Ejecutar "Conner POS" desde el escritorio
2. La base de datos se creará automáticamente en el primer arranque
3. Acceder desde el navegador a: http://localhost:5000/dashboard
4. Credenciales por defecto:
   - Usuario: admin
   - Contraseña: admin

IMPORTANTE: Cambia las credenciales por defecto después del primer inicio.

ACCESO DESDE OTROS EQUIPOS
---------------------------
1. Obtener la IP del servidor (donde está instalado Conner POS)
   - Abrir CMD y ejecutar: ipconfig
   - Buscar "Dirección IPv4"
2. En otros equipos de la red local, abrir navegador y acceder a:
   http://[IP_DEL_SERVIDOR]:5000/dashboard

Ejemplo: http://192.168.1.100:5000/dashboard

CONFIGURACIÓN DEL FIREWALL (IMPORTANTE)
----------------------------------------
Para acceder desde otros equipos en la red local:

OPCIÓN 1 - Script Automático (Recomendado):
1. Ejecutar setup_firewall.bat como Administrador
2. Seguir las instrucciones en pantalla

OPCIÓN 2 - Configuración Manual:
1. Abrir "Firewall de Windows Defender"
2. Clic en "Configuración avanzada"
3. Clic en "Reglas de entrada" > "Nueva regla"
4. Seleccionar "Puerto" > Siguiente
5. TCP, puerto específico: 5000 > Siguiente
6. Permitir la conexión > Siguiente
7. Aplicar a todos los perfiles > Siguiente
8. Nombre: "Conner POS - Flask Server" > Finalizar

NOTA: Sin esta configuración, solo podrás acceder desde localhost.

DESINSTALACIÓN
--------------
1. Ejecutar uninstall.bat como Administrador
2. Los datos de la base de datos se conservan por seguridad
3. Para eliminar datos, borrar manualmente la carpeta de instalación

SOPORTE TÉCNICO
---------------
Para más información y documentación completa:
https://docs.google.com/document/d/14uFWKk8CKpCPhdW8aYYKkdY7IRwmmGYA2K6tv9guP_Q/edit

REQUISITOS DEL SISTEMA
----------------------
- Windows 10 o superior
- 4 GB de RAM mínimo
- 500 MB de espacio en disco
- Conexión de red local (para acceso desde múltiples equipos)

NOTAS IMPORTANTES
-----------------
- Este sistema está diseñado para uso en red local únicamente
- No exponer el servidor a Internet sin medidas de seguridad adicionales
- Realizar copias de seguridad periódicas de la carpeta db/
- El puerto 5000 debe estar disponible en el servidor

VERSIÓN
-------
Conner POS v1.2
Compilado: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

© 2024 - Todos los derechos reservados
"""
    
    try:
        # Save scripts in dist folder
        installer_dir = os.path.join('dist', f'{exe_name}_Installer')
        os.makedirs(installer_dir, exist_ok=True)
        
        # Copy executable folder
        shutil.copytree(dist_path, os.path.join(installer_dir, exe_name), dirs_exist_ok=True)
        
        # Save scripts
        with open(os.path.join(installer_dir, 'install.bat'), 'w', encoding='utf-8') as f:
            f.write(install_bat)
        
        with open(os.path.join(installer_dir, 'uninstall.bat'), 'w', encoding='utf-8') as f:
            f.write(uninstall_bat)
        
        with open(os.path.join(installer_dir, 'README.txt'), 'w', encoding='utf-8') as f:
            f.write(readme_txt)
        
        with open(os.path.join(installer_dir, 'setup_firewall.bat'), 'w', encoding='utf-8') as f:
            f.write(firewall_bat)
        
        logger.info(f"✓ Installer structure created: {installer_dir}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error creating installer structure: {e}")
        return False


def main() -> int:
    """
    Main script function.
    
    Returns:
        0 if everything was successful, 1 otherwise
    """
    logger.info("=" * 70)
    logger.info("EXECUTABLE GENERATION - CONNER POS")
    logger.info("=" * 70)
    
    try:
        # 0. Verify network configuration
        verify_network_config()
        
        # 1. Build and copy frontend first
        logger.info("\nStep 1: Building Angular frontend...")
        if not build_and_copy_frontend():
            logger.error("Frontend build failed. Aborting compilation.")
            return 1
        
        # 2. Load configuration
        config = load_compile_config()
        
        # 3. Generate .spec file
        spec_file = generate_spec_file(config)
        
        # 4. Execute PyInstaller
        if not run_pyinstaller(spec_file):
            logger.error("Compilation error")
            return 1
        
        # 5. Verify executable
        if not verify_executable(config['exe_name']):
            logger.error("Executable was not generated correctly")
            return 1
        
        # 6. Create installer structure
        if not create_installer_structure(config['exe_name']):
            logger.warning("Could not create installer structure")
        
        # 7. Clean temporary files
        if config['clean_temp_files']:
            clean_temp_files()
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ EXECUTABLE GENERATED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"Executable: dist/{config['exe_name']}/{config['exe_name']}.exe")
        logger.info(f"Installer: dist/{config['exe_name']}_Installer/")
        logger.info("\nTo install:")
        logger.info(f"1. Go to dist/{config['exe_name']}_Installer/")
        logger.info("2. Run install.bat as Administrator")
        logger.info("3. Follow the on-screen instructions")
        
        return 0
        
    except KeyboardInterrupt:
        logger.error("\n✗ Compilation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
