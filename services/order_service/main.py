from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, conint
from typing import List
import sqlite3
import os
import requests
from datetime import datetime

app = FastAPI(title="Order Service")

DB_PATH = "/data/databases/orders.db"
PRODUCT_SERVICE_URL = "http://product-service:8000"

class OrderItem(BaseModel):
    product_id: int
    quantity: conint(gt=0)

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItem]

class Order(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItem]

def get_db():
    """Create database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
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

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/orders", response_model=Order)
async def create_order(order: OrderCreate):
    """Create a new order"""
    conn = get_db()
    cursor = conn.cursor()
    total_amount = 0
    
    # Verify products and calculate total
    for item in order.items:
        try:
            response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{item.product_id}")
            product = response.json()
            
            if item.quantity > product["stock"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product['name']}"
                )
            
            # Update product stock
            requests.put(
                f"{PRODUCT_SERVICE_URL}/products/{item.product_id}/stock",
                params={"quantity": -item.quantity}
            )
            
            total_amount += product["price"] * item.quantity
            
        except requests.RequestException:
            raise HTTPException(
                status_code=500,
                detail="Error communicating with product service"
            )
    
    # Create order
    cursor.execute(
        """INSERT INTO orders (user_id, total_amount, status)
           VALUES (?, ?, ?)""",
        (order.user_id, total_amount, "pending")
    )
    order_id = cursor.lastrowid
    
    # Create order items
    for item in order.items:
        product = requests.get(
            f"{PRODUCT_SERVICE_URL}/products/{item.product_id}"
        ).json()
        
        cursor.execute(
            """INSERT INTO order_items 
               (order_id, product_id, quantity, price_per_unit)
               VALUES (?, ?, ?, ?)""",
            (order_id, item.product_id, item.quantity, product["price"])
        )
    
    conn.commit()
    
    # Get created order
    cursor.execute(
        """SELECT o.*, oi.product_id, oi.quantity
           FROM orders o
           JOIN order_items oi ON o.id = oi.order_id
           WHERE o.id = ?""",
        (order_id,)
    )
    order_data = cursor.fetchall()
    conn.close()
    
    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": order_data[0][0],
        "user_id": order_data[0][1],
        "total_amount": order_data[0][2],
        "status": order_data[0][3],
        "created_at": order_data[0][4],
        "items": [
            {"product_id": row[5], "quantity": row[6]}
            for row in order_data
        ]
    }

@app.get("/orders/{user_id}", response_model=List[Order])
async def get_user_orders(user_id: int):
    """Get all orders for a user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT o.*, oi.product_id, oi.quantity
           FROM orders o
           JOIN order_items oi ON o.id = oi.order_id
           WHERE o.user_id = ?
           ORDER BY o.created_at DESC""",
        (user_id,)
    )
    orders_data = cursor.fetchall()
    conn.close()
    
    # Group order items by order_id
    orders = {}
    for row in orders_data:
        order_id = row[0]
        if order_id not in orders:
            orders[order_id] = {
                "id": row[0],
                "user_id": row[1],
                "total_amount": row[2],
                "status": row[3],
                "created_at": row[4],
                "items": []
            }
        orders[order_id]["items"].append({
            "product_id": row[5],
            "quantity": row[6]
        })
    
    return list(orders.values())

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str):
    """Update order status"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Order status updated successfully"}