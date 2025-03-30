#!/usr/bin/env python3
"""
Setup script for MCP Graph API.
This script helps with initial configuration of the MCP server.
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def check_python_version():
    """Check if Python version is compatible."""
    required_version = (3, 9)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required.")
        print(f"Current Python version: {current_version[0]}.{current_version[1]}.{current_version[2]}")
        sys.exit(1)
    
    print(f"✅ Python version {current_version[0]}.{current_version[1]}.{current_version[2]} is compatible.")

def check_uv_installed():
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        print("✅ uv is installed.")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ uv is not installed.")
        print("Please install uv using the instructions at: https://github.com/astral-sh/uv")
        return False

def setup_environment():
    """Set up the Python virtual environment."""
    if not Path(".venv").exists():
        print("Creating virtual environment with uv...")
        subprocess.run(["uv", "venv"], check=True)
        print("✅ Virtual environment created.")
    else:
        print("✅ Virtual environment already exists.")
    
    print("Installing dependencies...")
    subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], check=True)
    print("✅ Dependencies installed.")

def setup_env_file():
    """Set up the .env file."""
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("Creating .env file from template...")
            shutil.copy(".env.example", ".env")
            print("✅ .env file created from template.")
            print("Please edit the .env file with your Azure app credentials.")
        else:
            print("❌ .env.example template not found.")
            print("Please create a .env file with your Azure app credentials.")
    else:
        print("✅ .env file already exists.")

def main():
    """Main setup function."""
    print("Starting MCP Graph API setup...")
    
    # Check requirements
    check_python_version()
    if not check_uv_installed():
        return
    
    # Setup environment and files
    setup_environment()
    setup_env_file()
    
    print("\nSetup completed!")
    print("\nNext steps:")
    print("1. Edit the .env file with your Azure app credentials")
    print("2. Run 'python main.py' to start the MCP server")
    print("3. Configure Claude Desktop to connect to the MCP server")
    print("\nSee SETUP.md for detailed instructions.")

if __name__ == "__main__":
    main() 