import subprocess
import sys

def check_package(package_name):
    try:
        __import__(package_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name} is missing")
        return False

def verify_installations():
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'requests',
        'numpy',
        'pandas',
        'streamlit',
        'plotly',
        'python-jose',
        'passlib',
        'sqlalchemy'
    ]
    
    all_installed = True
    for package in required_packages:
        if not check_package(package.replace('-', '_')):
            all_installed = False
    
    return all_installed

if __name__ == "__main__":
    print("Verifying package installations...")
    if verify_installations():
        print("\nAll packages are installed correctly!")
    else:
        print("\nSome packages are missing. Please install required packages.")
        sys.exit(1)