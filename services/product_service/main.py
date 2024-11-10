from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, constr, confloat, conint
from typing import List, Optional
import sqlite3
import os
from datetime import datetime

app = FastAPI(title="Product Service")

DB_PATH = "/data/databases/products.db"

class ProductBase(BaseModel):
    name: constr(min_length=1)
    description: Optional[str] = None
    price: confloat(gt=0)
    stock: conint(ge=0)

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

def get_db():
    """Create database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize database with tables and sample data"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add sample products if table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Gaming Laptop', 'High-performance gaming laptop', 999.99, 10),
            ('Wireless Mouse', 'Ergonomic wireless mouse', 29.99, 50),
            ('Mechanical Keyboard', 'RGB mechanical keyboard', 89.99, 30),
            ('27" Monitor', '4K Ultra HD Monitor', 299.99, 15),
            ('Laptop Backpack', 'Water-resistant laptop backpack', 49.99, 100)
        ]
        cursor.executemany(
            'INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)',
            sample_products
        )
        
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/products", response_model=List[Product])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """Get all products with optional search"""
    conn = get_db()
    cursor = conn.cursor()
    
    if search:
        cursor.execute(
            """SELECT * FROM products 
               WHERE name LIKE ? OR description LIKE ?
               LIMIT ? OFFSET ?""",
            (f"%{search}%", f"%{search}%", limit, skip)
        )
    else:
        cursor.execute(
            "SELECT * FROM products LIMIT ? OFFSET ?",
            (limit, skip)
        )
    
    products = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": p[0],
            "name": p[1],
            "description": p[2],
            "price": p[3],
            "stock": p[4],
            "created_at": p[5]
        }
        for p in products
    ]

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    """Get a specific product by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product[0],
        "name": product[1],
        "description": product[2],
        "price": product[3],
        "stock": product[4],
        "created_at": product[5]
    }

@app.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    """Create a new product"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO products (name, description, price, stock)
           VALUES (?, ?, ?, ?)""",
        (product.name, product.description, product.price, product.stock)
    )
    conn.commit()
    
    # Get created product
    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (cursor.lastrowid,)
    )
    new_product = cursor.fetchone()
    conn.close()
    
    return {
        "id": new_product[0],
        "name": new_product[1],
        "description": new_product[2],
        "price": new_product[3],
        "stock": new_product[4],
        "created_at": new_product[5]
    }

@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, product: ProductCreate):
    """Update a product"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        """UPDATE products 
           SET name = ?, description = ?, price = ?, stock = ?
           WHERE id = ?""",
        (product.name, product.description, product.price, product.stock, product_id)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    conn.commit()
    
    # Get updated product
    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )
    updated_product = cursor.fetchone()
    conn.close()
    
    return {
        "id": updated_product[0],
        "name": updated_product[1],
        "description": updated_product[2],
        "price": updated_product[3],
        "stock": updated_product[4],
        "created_at": updated_product[5]
    }

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    """Delete a product"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Product deleted successfully"}

@app.put("/products/{product_id}/stock")
async def update_stock(product_id: int, quantity: int):
    """Update product stock"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT stock FROM products WHERE id = ?",
        (product_id,)
    )
    current_stock = cursor.fetchone()
    
    if not current_stock:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_stock = current_stock[0] + quantity
    if new_stock < 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    cursor.execute(
        "UPDATE products SET stock = ? WHERE id = ?",
        (new_stock, product_id)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Stock updated successfully", "new_stock": new_stock}