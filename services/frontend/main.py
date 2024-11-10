import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

# Configure Streamlit page settings
st.set_page_config(
    page_title="E-Commerce Platform",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Service URLs - use environment variables or defaults
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")

# Session State Initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'cart' not in st.session_state:
    st.session_state.cart = {}

def login_user(username: str, password: str) -> bool:
    """Authenticate user and store token"""
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            # Get user details
            user_response = requests.get(
                f"{USER_SERVICE_URL}/users/me",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            if user_response.status_code == 200:
                user_data = user_response.json()
                st.session_state.user_id = user_data["id"]
            return True
        return False
    except requests.RequestException:
        return False

def register_user(username: str, password: str, email: str) -> bool:
    """Register new user"""
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/register",
            json={"username": username, "password": password, "email": email}
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_products(search: str = None):
    """Fetch products from product service"""
    try:
        params = {"search": search} if search else {}
        response = requests.get(f"{PRODUCT_SERVICE_URL}/products", params=params)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []

def create_order(items: list):
    """Create new order"""
    try:
        response = requests.post(
            f"{ORDER_SERVICE_URL}/orders",
            json={
                "user_id": st.session_state.user_id,
                "items": items
            },
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

def show_login_page():
    """Display login/register page"""
    st.title("Welcome to E-Commerce Platform")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit and username and password:
                if login_user(username, password):
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            email = st.text_input("Email")
            submit = st.form_submit_button("Register")
            
            if submit and new_username and new_password:
                if register_user(new_username, new_password, email):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Registration failed")

def show_product_page():
    """Display product listing page"""
    st.title("Products")
    
    # Search bar
    search = st.text_input("Search products")
    
    # Get products
    products = get_products(search)
    
    # Display products in grid
    cols = st.columns(3)
    for idx, product in enumerate(products):
        with cols[idx % 3]:
            st.subheader(product["name"])
            st.write(f"Price: ${product['price']:.2f}")
            st.write(f"Stock: {product['stock']}")
            if product["description"]:
                st.write(product["description"])
            
            quantity = st.number_input(
                f"Quantity for {product['name']}",
                min_value=0,
                max_value=product["stock"],
                key=f"qty_{product['id']}"
            )
            
            if st.button("Add to Cart", key=f"add_{product['id']}"):
                if quantity > 0:
                    st.session_state.cart[product["id"]] = {
                        "name": product["name"],
                        "price": product["price"],
                        "quantity": quantity
                    }
                    st.success(f"Added {quantity} {product['name']} to cart!")

def show_cart_page():
    """Display shopping cart page"""
    st.title("Shopping Cart")
    
    if not st.session_state.cart:
        st.write("Your cart is empty")
        return
    
    # Display cart items
    cart_items = []
    total = 0
    
    for product_id, item in st.session_state.cart.items():
        subtotal = item["price"] * item["quantity"]
        cart_items.append({
            "Product": item["name"],
            "Quantity": item["quantity"],
            "Price": f"${item['price']:.2f}",
            "Subtotal": f"${subtotal:.2f}"
        })
        total += subtotal
    
    st.table(pd.DataFrame(cart_items))
    st.subheader(f"Total: ${total:.2f}")
    
    # Checkout button
    if st.button("Checkout"):
        order_items = [
            {
                "product_id": int(pid),
                "quantity": item["quantity"]
            }
            for pid, item in st.session_state.cart.items()
        ]
        
        if create_order(order_items):
            st.success("Order placed successfully!")
            st.session_state.cart = {}
            st.experimental_rerun()
        else:
            st.error("Failed to place order")

def show_orders_page():
    """Display order history page"""
    st.title("Order History")
    
    try:
        response = requests.get(
            f"{ORDER_SERVICE_URL}/orders/{st.session_state.user_id}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        
        if response.status_code == 200:
            orders = response.json()
            
            for order in orders:
                with st.expander(
                    f"Order #{order['id']} - {order['created_at']} - "
                    f"${order['total_amount']:.2f}"
                ):
                    st.write(f"Status: {order['status']}")
                    items_df = pd.DataFrame([
                        {
                            "Product ID": item["product_id"],
                            "Quantity": item["quantity"]
                        }
                        for item in order["items"]
                    ])
                    st.table(items_df)
        else:
            st.error("Failed to fetch orders")
            
    except requests.RequestException:
        st.error("Error connecting to order service")

def main():
    """Main application"""
    # Sidebar navigation
    if st.session_state.token:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to",
            ["Products", "Cart", "Orders"]
        )
        
        if st.sidebar.button("Logout"):
            st.session_state.token = None
            st.session_state.user_id = None
            st.session_state.cart = {}
            st.experimental_rerun()
        
        # Display cart summary in sidebar
        if st.session_state.cart:
            st.sidebar.subheader("Cart Summary")
            total = sum(
                item["price"] * item["quantity"]
                for item in st.session_state.cart.values()
            )
            st.sidebar.write(f"Total: ${total:.2f}")
        
        # Show selected page
        if page == "Products":
            show_product_page()
        elif page == "Cart":
            show_cart_page()
        elif page == "Orders":
            show_orders_page()
    else:
        show_login_page()

if __name__ == "__main__":
    main()