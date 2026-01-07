#!/usr/bin/env python3
"""
Setup Verification Script
Checks if all required files are present and configured correctly
"""

import sys
from pathlib import Path

def check_file(filepath, required=True):
    """Check if file exists"""
    path = Path(filepath)
    exists = path.exists()
    status = "✓" if exists else ("✗" if required else "○")
    req_str = "(required)" if required else "(optional)"
    print(f"{status} {filepath} {req_str}")
    return exists

def check_python_imports():
    """Check if required Python packages are installed"""
    print("\nChecking Python packages:")
    packages = {
        "requests": True,
        "geopy": True,
        "tkinter": True,
    }
    
    all_present = True
    for package, required in packages.items():
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            status = "✗" if required else "○"
            print(f"{status} {package} NOT installed {'(required)' if required else '(optional)'}")
            if required:
                all_present = False
    
    return all_present

def check_version_consistency():
    """Check if version numbers are consistent"""
    print("\nChecking version consistency:")
    
    try:
        with open("Weather.py", "r", encoding="utf-8") as f:
            weather_content = f.read()
            
        # Extract version from Weather.py
        version_line = [line for line in weather_content.split('\n') if 'VERSION = ' in line]
        if version_line:
            version = version_line[0].split('"')[1]
            print(f"✓ Weather.py version: {version}")
            return True
        else:
            print("✗ Could not find VERSION in Weather.py")
            return False
            
    except Exception as e:
        print(f"✗ Error checking version: {e}")
        return False

def check_github_repo():
    """Check if GitHub repo is configured"""
    print("\nChecking GitHub configuration:")
    
    try:
        with open("Weather.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if 'GITHUB_REPO = "Rog294super/Weather-App"' in content:
            print("✓ GitHub repository configured: Rog294super/Weather-App")
            return True
        else:
            print("✗ GitHub repository not properly configured")
            return False
            
    except Exception as e:
        print(f"✗ Error checking GitHub config: {e}")
        return False

def main():
    print("=" * 60)
    print("Weather Application - Setup Verification")
    print("=" * 60)
    
    # Check required files
    print("\nChecking required files:")
    required_files = [
        "Weather.py",
        "file_handler.py",
        "requirements.txt",
        "README.md",
        "LICENSE",
        ".gitignore"
    ]
    
    optional_files = [
        "icon.ico",
        "config.json",
        "Weather.spec",
        "Weather_Installer.spec",
        "compiler.bat"
    ]
    
    all_required_present = True
    for file in required_files:
        if not check_file(file, required=True):
            all_required_present = False
    
    print("\nChecking optional files:")
    for file in optional_files:
        check_file(file, required=False)
    
    # Check Updater directory
    print("\nChecking Updater directory:")
    updater_files = [
        "Updater/updater_final.cpp",
        "Updater/compile_updater.bat"
    ]
    
    for file in updater_files:
        check_file(file, required=False)
    
    # Check Python packages
    packages_ok = check_python_imports()
    
    # Check version consistency
    version_ok = check_version_consistency()
    
    # Check GitHub configuration
    github_ok = check_github_repo()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if all_required_present and packages_ok and version_ok and github_ok:
        print("✓ All checks passed! Ready to build.")
        print("\nNext steps:")
        print("1. Run compiler.bat to build the application")
        print("2. Test the built executable")
        print("3. Create a GitHub release with the built files")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nTo install missing packages:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
