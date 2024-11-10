import os
from pathlib import Path
import shutil

def reset_databases():
    """Remove and reinitialize all databases"""
    db_dir = Path(__file__).parent.parent / 'databases'
    
    # Remove existing databases
    if db_dir.exists():
        shutil.rmtree(db_dir)
        print("Existing databases removed")
    
    # Run setup script
    setup_script = Path(__file__).parent.parent / 'setup_databases.py'
    if setup_script.exists():
        os.system(f'python {setup_script}')
        print("Databases reinitialized")
    else:
        print("Error: setup_databases.py not found!")

if __name__ == "__main__":
    reset_databases()