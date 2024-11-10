import sqlite3
import os
from pathlib import Path
from passlib.context import CryptContext

def create_database_directory():
    """Create the data/databases directory if it doesn't exist"""
    # Create data directory in project root
    current_dir = Path.cwd()
    db_dir = current_dir / 'data' / 'databases'
    db_dir.mkdir(parents=True, exist_ok=True)
    print(f"Database directory created at: {db_dir}")
    return db_dir

def init_databases():
    """Initialize all databases with their schemas and sample data"""
    try:
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        db_dir = create_database_directory()
        
        # Initialize Users Database
        print("Initializing users database...")
        users_db_path = db_dir / 'users.db'
        conn = sqlite3.connect(users_db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample users if table is empty
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            sample_users = [
                ('admin', 'admin123', 'admin@example.com', 1),  # Admin user
                ('user1', 'pass123', 'user1@example.com', 0),   # Regular user
                ('test_user', 'test123', 'test@example.com', 0) # Test user
            ]
            
            c.executemany('''
                INSERT INTO users (username, password, email, is_admin)
                VALUES (?, ?, ?, ?)
            ''', sample_users)
        
        conn.commit()
        conn.close()
        print("Users database initialized successfully!")
        
        # Initialize Products Database
        print("Initializing products database...")
        products_db_path = db_dir / 'products.db'
        conn = sqlite3.connect(products_db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample products if table is empty
        c.execute("SELECT COUNT(*) FROM products")
        if c.fetchone()[0] == 0:
            sample_products = [
                ('Gaming Laptop', 'High-performance gaming laptop', 999.99, 10),
                ('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 50),
                ('Mechanical Keyboard', 'RGB mechanical keyboard', 89.99, 30),
                ('27" Monitor', '4K Ultra HD Monitor', 299.99, 15),
                ('Laptop Backpack', 'Water-resistant laptop backpack', 49.99, 100)
            ]
            
            c.executemany('''
                INSERT INTO products (name, description, price, stock)
                VALUES (?, ?, ?, ?)
            ''', sample_products)
        
        conn.commit()
        conn.close()
        print("Products database initialized successfully!")
        
        # Initialize Orders Database
        print("Initializing orders database...")
        orders_db_path = db_dir / 'orders.db'
        conn = sqlite3.connect(orders_db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_unit REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Orders database initialized successfully!")
        
        # Set appropriate permissions
        for db_file in db_dir.glob('*.db'):
            os.chmod(db_file, 0o666)
        
        print("\nAll databases initialized successfully!")
        print(f"Database files location: {db_dir}")
        
    except Exception as e:
        print(f"Error initializing databases: {e}")
        raise

def verify_databases():
    """Verify that all databases were created successfully"""
    db_dir = Path.cwd() / 'data' / 'databases'
    required_dbs = ['users.db', 'products.db', 'orders.db']
    
    print("\nVerifying databases:")
    for db in required_dbs:
        db_path = db_dir / db
        if db_path.exists():
            size = db_path.stat().st_size
            print(f"✓ {db} exists (size: {size} bytes)")
        else:
            print(f"✗ {db} is missing!")

if __name__ == "__main__":
    try:
        print("Starting database initialization...")
        init_databases()
        verify_databases()
    except Exception as e:
        print(f"\nError during setup: {e}")