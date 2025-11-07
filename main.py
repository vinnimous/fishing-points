#!/usr/bin/env python3
"""
Fishing Points Application - Main Entry Point

This application automatically manages Python environment setup and dependency
installation before executing the North Carolina fishing points scraper.

Features:
- Cross-platform virtual environment management (Windows/Linux/macOS)
- Automatic dependency installation from requirements.txt
- Smart environment detection and activation
- Comprehensive error handling and user guidance
- Seamless integration with CI/CD pipelines

The application follows best practices for Python project automation:
1. Detects existing virtual environments
2. Creates new venv if none exists
3. Installs/updates dependencies as needed  
4. Executes scraper with proper environment

Author: NC Fishing Points Scraper
Version: 2.0
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
import resources.source.nc as nc


def is_venv_active():
    """
    Detect if a Python virtual environment is currently active.
    
    Checks for virtual environment indicators in the Python system
    to determine activation status across different venv implementations.
    
    Returns:
        bool: True if virtual environment is active, False otherwise
    """
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )


def create_venv(venv_path):
    """
    Create a new Python virtual environment at the specified path.
    
    Uses Python's built-in venv module to create an isolated environment
    with pip included for dependency management.
    
    Args:
        venv_path (Path): Path where virtual environment should be created
        
    Returns:
        bool: True if creation successful, False if error occurred
    """
    print(f"🔧 Creating virtual environment at {venv_path}...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✓ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating virtual environment: {e}")
        return False


def get_venv_python_path(venv_path):
    """
    Get the Python executable path within a virtual environment.
    
    Handles cross-platform path differences between Windows and Unix systems.
    
    Args:
        venv_path (Path): Path to virtual environment directory
        
    Returns:
        Path: Path to Python executable within the virtual environment
    """
    if os.name == 'nt':  # Windows
        return venv_path / 'Scripts' / 'python.exe'
    else:  # Unix/Linux/macOS
        return venv_path / 'bin' / 'python'


def get_venv_pip_path(venv_path):
    """
    Get the pip executable path within a virtual environment.
    
    Handles cross-platform path differences for pip executable location.
    
    Args:
        venv_path (Path): Path to virtual environment directory
        
    Returns:
        Path: Path to pip executable within the virtual environment
    """
    if os.name == 'nt':  # Windows
        return venv_path / 'Scripts' / 'pip.exe'
    else:  # Unix/Linux/macOS
        return venv_path / 'bin' / 'pip'


def install_requirements(venv_path, requirements_file):
    """
    Install Python packages from requirements.txt using virtual environment pip.
    
    Handles dependency installation within an isolated virtual environment,
    providing detailed error reporting and validation.
    
    Args:
        venv_path (Path): Path to virtual environment directory
        requirements_file (Path): Path to requirements.txt file
        
    Returns:
        bool: True if installation successful or no requirements, False on error
    """
    if not requirements_file.exists():
        print(f"✓ No requirements.txt found at {requirements_file}")
        return True
    
    # Validate requirements file is not empty
    if requirements_file.stat().st_size == 0:
        print("✓ requirements.txt is empty, no packages to install")
        return True
    
    pip_path = get_venv_pip_path(venv_path)
    
    print(f"📦 Installing requirements from {requirements_file}...")
    try:
        result = subprocess.run([
            str(pip_path), 'install', '-r', str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✓ Requirements installed successfully")
        if result.stdout and result.stdout.strip():
            print("📋 Installation summary:")
            # Show only important lines, filter out verbose pip output
            important_lines = [line for line in result.stdout.split('\n') 
                             if 'Successfully installed' in line or 'Requirement already satisfied' in line]
            for line in important_lines[:3]:  # Show first 3 important lines
                print(f"  {line}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing requirements: {e}")
        if e.stderr:
            print("Error details:")
            print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"✗ Pip executable not found at {pip_path}")
        return False


def install_requirements_current_env(requirements_file):
    """
    Install packages from requirements.txt using current environment's pip.
    
    Used when already within an active virtual environment or when
    installing globally. Provides upgrade capability for existing packages.
    
    Args:
        requirements_file (Path): Path to requirements.txt file
        
    Returns:
        bool: True if installation successful, False on error
    """
    if not requirements_file.exists():
        print(f"✓ No requirements.txt found at {requirements_file}")
        return True
    
    # Validate requirements file is not empty
    if requirements_file.stat().st_size == 0:
        print("✓ requirements.txt is empty, no packages to install")
        return True
    
    print(f"📦 Installing/updating requirements from {requirements_file}...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✓ Requirements installed/updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing requirements: {e}")
        if e.stderr:
            print("Error details:")
            print(e.stderr)
        return False


def setup_environment():
    """
    Comprehensive Python environment setup and dependency management.
    
    This function orchestrates the complete environment preparation process:
    1. Detects existing virtual environment activation
    2. Creates new virtual environment if needed
    3. Installs/updates project dependencies
    4. Provides user guidance for manual activation if required
    
    Designed to work seamlessly in both development and CI/CD contexts.
    
    Returns:
        bool: True if environment setup successful, False on critical errors
    """
    project_root = Path(__file__).parent
    venv_path = project_root / 'venv'
    requirements_file = project_root / 'requirements.txt'
    
    print("=== Python Environment Setup ===")
    
    # Scenario 1: Already in an active virtual environment
    if is_venv_active():
        print("✓ Virtual environment is already active")
        print("🔄 Checking for dependency updates...")
        
        # Install/update requirements from requirements.txt
        if not install_requirements_current_env(requirements_file):
            print("⚠ Dependency installation failed, but continuing...")
            return False
        
        print("✅ Environment ready!")
        return True
    
    # Scenario 2: Virtual environment needs to be created or activated
    if not venv_path.exists():
        print(f"🔍 Virtual environment not found at {venv_path}")
        if not create_venv(venv_path):
            return False
    else:
        print(f"✓ Virtual environment found at {venv_path}")
    
    # Install/update dependencies in the virtual environment
    print("🔄 Setting up project dependencies...")
    if not install_requirements(venv_path, requirements_file):
        print("⚠ Dependency installation failed")
        return False
    
    # Provide cross-platform activation instructions
    if os.name == 'nt':  # Windows
        activate_script = venv_path / 'Scripts' / 'activate.bat'
        activation_cmd = f"call {activate_script}"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / 'bin' / 'activate'
        activation_cmd = f"source {activate_script}"
    
    print("\n=== Environment Ready ===")
    print("💡 To manually activate the virtual environment:")
    print(f"   {activation_cmd}")
    print("\n🚀 Re-run this script to automatically use the virtual environment")
    
    return True


def main():
    """
    Main application orchestration and execution logic.
    
    Coordinates the complete application workflow:
    1. Environment setup and validation
    2. Virtual environment activation (if needed)
    3. Scraper execution with error handling
    4. Results summary and user feedback
    
    Handles both development and production execution contexts
    with appropriate error codes for automation.
    """
    print("\n=== 🎣 NC Fishing Points Application ===")
    print("🌊 Marine GPS waypoint generator for North Carolina waters")
    
    # Phase 1: Environment preparation
    if not setup_environment():
        print("💥 Environment setup failed - cannot continue")
        print("🔧 Check Python installation and permissions")
        sys.exit(1)
    
    # Phase 2: Virtual environment activation (if needed)
    if not is_venv_active():
        project_root = Path(__file__).parent
        venv_path = project_root / 'venv'
        venv_python = get_venv_python_path(venv_path)
        
        if venv_python.exists():
            print(f"\n🔄 Restarting with virtual environment Python...")
            try:
                # Re-execute this script using the virtual environment's Python
                subprocess.run([str(venv_python), str(__file__)], check=True)
                return
            except subprocess.CalledProcessError as e:
                print(f"💥 Error executing with virtual environment: {e}")
                sys.exit(1)
        else:
            print(f"💥 Virtual environment Python not found at {venv_python}")
            print("🔧 Try deleting the venv folder and running again")
            sys.exit(1)
    
    # Phase 3: Application execution
    print("✅ Environment ready - all dependencies loaded")
    print("� Initializing North Carolina fishing points scraper")
    
    try:
        # Execute scraper with comprehensive error handling
        print(f"\n=== 🌊 Scraping NC Fishing Locations ===")
        fishing_locations = nc.scraper()
        
        if fishing_locations:
            print(f"\n📍 Total locations extracted: {len(fishing_locations)}")
        else:
            print("\n⚠️ No fishing locations were extracted")
            print("🔍 This may indicate website changes or connectivity issues")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Critical error during scraping: {e}")
        print("🐛 This may be a bug - check logs and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
