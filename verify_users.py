import sqlite3
from pathlib import Path

def check_users():
    data_dir = Path.cwd() / 'data' / 'databases'
    conn = sqlite3.connect(data_dir / 'users.db')
    cursor = conn.cursor()
    
    print("Checking users table:")
    cursor.execute("SELECT id, username, email, is_admin FROM users")
    users = cursor.fetchall()
    
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Is Admin: {user[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_users()