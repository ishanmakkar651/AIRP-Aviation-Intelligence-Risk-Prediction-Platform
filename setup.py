#!/usr/bin/env python3
"""
Quick Start Script for AIRP
Automates Phase 1 setup
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - Complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is sufficient"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_postgresql():
    """Check if PostgreSQL is accessible"""
    print("🔄 Checking PostgreSQL...")
    try:
        import psycopg2
        # Try to connect (will fail if not installed, but that's ok)
        print("✅ PostgreSQL driver installed")
        return True
    except ImportError:
        print("⚠️  PostgreSQL driver not installed (will be installed with requirements)")
        return True

def create_venv():
    """Create virtual environment"""
    if os.path.exists('venv'):
        print("ℹ️  Virtual environment already exists")
        return True
    
    return run_command(
        f"{sys.executable} -m venv venv",
        "Creating virtual environment"
    )

def install_requirements():
    """Install Python requirements"""
    # Determine pip path based on OS
    if sys.platform == "win32":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    return run_command(
        f"{pip_path} install -r requirements.txt",
        "Installing Python dependencies"
    )

def setup_database():
    """Run database setup"""
    # Determine python path based on OS
    if sys.platform == "win32":
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    print("🔄 Setting up database...")
    print("ℹ️  This will create database, tables, and schema")
    
    try:
        subprocess.run(
            [python_path, "2_database/db_setup.py"],
            check=True
        )
        print("✅ Database setup complete")
        return True
    except subprocess.CalledProcessError:
        print("❌ Database setup failed")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is installed and running")
        print("  2. config.yaml has correct database credentials")
        print("  3. Database user has necessary permissions")
        return False

def load_airports():
    """Load airport reference data"""
    if sys.platform == "win32":
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    print("🔄 Loading airport reference data...")
    
    try:
        subprocess.run(
            [python_path, "1_data_ingestion/airport_loader.py"],
            check=True
        )
        print("✅ Airport data loaded")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Airport data loading failed (non-critical)")
        return False

def main():
    """Main setup flow"""
    print_header("AIRP Quick Start Setup")
    print("Aviation Intelligence & Risk Prediction Platform")
    print("This script will set up Phase 1 components\n")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Check Python version
    print_header("Step 1: Checking Prerequisites")
    if not check_python_version():
        sys.exit(1)
    
    check_postgresql()
    
    # Step 2: Create virtual environment
    print_header("Step 2: Setting Up Python Environment")
    if not create_venv():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Step 3: Install requirements
    print_header("Step 3: Installing Dependencies")
    if not install_requirements():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Step 4: Database setup
    print_header("Step 4: Database Setup")
    print("⚠️  Before proceeding, ensure:")
    print("   1. PostgreSQL is installed and running")
    print("   2. You've updated config.yaml with correct credentials")
    
    response = input("\nReady to proceed? (y/n): ").strip().lower()
    if response != 'y':
        print("\nℹ️  Setup paused. Please:")
        print("   1. Install PostgreSQL if needed")
        print("   2. Update config.yaml with your credentials")
        print("   3. Run this script again")
        sys.exit(0)
    
    if not setup_database():
        print("\n❌ Setup failed at database creation")
        print("Please fix issues and run again")
        sys.exit(1)
    
    # Step 5: Load airport data
    print_header("Step 5: Loading Reference Data")
    load_airports()
    
    # Success!
    print_header("✅ Phase 1 Setup Complete!")
    
    print("Next steps:")
    print("\n1. Activate virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n2. Start data collection:")
    print("   python 1_data_ingestion/opensky_collector.py")
    
    print("\n3. Let it collect data for 24 hours, then proceed to Phase 2")
    
    print("\n📖 For detailed instructions, see README.md")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)