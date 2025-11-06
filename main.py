#!/usr/bin/env python3
"""
Fishing Points Application

This script automatically handles virtual environment setup and dependency installation
before running the main application logic.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
import resources.source.nc as nc


def is_venv_active():
    """Check if a virtual environment is currently active."""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )


def create_venv(venv_path):
    """Create a new virtual environment."""
    print(f"Creating virtual environment at {venv_path}...")
    try:
        venv.create(venv_path, with_pip=True)
        print("✓ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating virtual environment: {e}")
        return False


def get_venv_python_path(venv_path):
    """Get the Python executable path within the virtual environment."""
    if os.name == 'nt':  # Windows
        return venv_path / 'Scripts' / 'python.exe'
    else:  # Unix/Linux/macOS
        return venv_path / 'bin' / 'python'


def get_venv_pip_path(venv_path):
    """Get the pip executable path within the virtual environment."""
    if os.name == 'nt':  # Windows
        return venv_path / 'Scripts' / 'pip.exe'
    else:  # Unix/Linux/macOS
        return venv_path / 'bin' / 'pip'


def install_requirements(venv_path, requirements_file):
    """Install packages from requirements.txt using the virtual environment's pip."""
    if not requirements_file.exists():
        print(f"✓ No requirements.txt found at {requirements_file}")
        return True
    
    # Check if requirements.txt is empty
    if requirements_file.stat().st_size == 0:
        print("✓ requirements.txt is empty, no packages to install")
        return True
    
    pip_path = get_venv_pip_path(venv_path)
    
    print(f"Installing requirements from {requirements_file}...")
    try:
        result = subprocess.run([
            str(pip_path), 'install', '-r', str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✓ Requirements installed successfully")
        if result.stdout:
            print("Installation output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing requirements: {e}")
        if e.stderr:
            print("Error details:")
            print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"✗ Pip not found at {pip_path}")
        return False


def install_requirements_current_env(requirements_file):
    """Install packages from requirements.txt using the current environment's pip."""
    if not requirements_file.exists():
        print(f"✓ No requirements.txt found at {requirements_file}")
        return True
    
    # Check if requirements.txt is empty
    if requirements_file.stat().st_size == 0:
        print("✓ requirements.txt is empty, no packages to install")
        return True
    
    print(f"Installing/updating requirements from {requirements_file}...")
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
    """Set up the Python environment (virtual env + dependencies)."""
    project_root = Path(__file__).parent
    venv_path = project_root / 'venv'
    requirements_file = project_root / 'requirements.txt'
    
    print("=== Python Environment Setup ===")
    
    # Check if we're already in a virtual environment
    if is_venv_active():
        print("✓ Virtual environment is already active")
        
        # Install/update requirements from requirements.txt
        if not install_requirements_current_env(requirements_file):
            return False
        
        return True
    
    # Check if virtual environment exists
    if not venv_path.exists():
        print(f"Virtual environment not found at {venv_path}")
        if not create_venv(venv_path):
            return False
    else:
        print(f"✓ Virtual environment found at {venv_path}")
    
    # Install requirements
    if not install_requirements(venv_path, requirements_file):
        return False
    
    # Provide instructions for activation
    if os.name == 'nt':  # Windows
        activate_script = venv_path / 'Scripts' / 'activate.bat'
        activation_cmd = f"call {activate_script}"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / 'bin' / 'activate'
        activation_cmd = f"source {activate_script}"
    
    print("\n=== Next Steps ===")
    print("To activate the virtual environment manually, run:")
    print(f"  {activation_cmd}")
    print("\nOr run this script again from within the activated environment.")
    
    return True


def main():
    """Main application logic."""
    print("\n=== Fishing Points Application ===")
    
    # Setup environment first
    if not setup_environment():
        print("✗ Environment setup failed. Exiting.")
        sys.exit(1)
    
    # If we're not in a virtual environment yet, restart the script with the venv Python
    if not is_venv_active():
        project_root = Path(__file__).parent
        venv_path = project_root / 'venv'
        venv_python = get_venv_python_path(venv_path)
        
        if venv_python.exists():
            print(f"\nRestarting script with virtual environment Python...")
            try:
                # Re-execute this script using the virtual environment's Python
                subprocess.run([str(venv_python), str(__file__)], check=True)
                return
            except subprocess.CalledProcessError as e:
                print(f"✗ Error running script with virtual environment: {e}")
                sys.exit(1)
        else:
            print(f"✗ Virtual environment Python not found at {venv_python}")
            sys.exit(1)
    
    # Your main application code goes here
    print("✓ Environment is ready!")
    print("🎣 Welcome to Fishing Points!")
    
    # Run the North Carolina fishing points scraper
    print(f"\n=== Running NC Fishing Points Scraper ===")
    try:
        # Import after environment is set up
        fishing_locations = nc.scraper()
        
        if fishing_locations:
            print(f"\n🎯 Successfully scraped {len(fishing_locations)} fishing locations!")
            print("Sample locations:")
            for i, location in enumerate(fishing_locations[:3]):  # Show first 3
                print(f"  {i+1}. {location.get('name', 'Unknown')} - {location.get('latitude', 'N/A')}, {location.get('longitude', 'N/A')}")
            if len(fishing_locations) > 3:
                print(f"  ... and {len(fishing_locations) - 3} more locations")
        else:
            print("\n❌ No fishing locations were found.")
            
    except Exception as e:
        print(f"✗ Error running scraper: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
