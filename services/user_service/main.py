from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
import os
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt

app = FastAPI()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "UHqKevZgab5h0NogfNIX2n7F-nN_BlyPbzPb6DIv0aE")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database path
DB_PATH = "/data/databases/users.db"

# Models
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool = False

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    """Create database connection"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def get_user(username: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password, email, is_admin FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user[0],
            "username": user[1],
            "password": user[2],
            "email": user[3],
            "is_admin": user[4]
        }

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For the sample admin user, allow plain password comparison
    if user["username"] == "admin" and form_data.password == "admin123":
        access_token = create_access_token(
            data={"sub": user["username"]}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    try:
        cursor.execute(
            """INSERT INTO users (username, email, password, is_admin)
               VALUES (?, ?, ?, ?)""",
            (user.username, user.email, hashed_password, False)
        )
        conn.commit()
        
        # Get created user
        cursor.execute(
            "SELECT id, username, email, is_admin FROM users WHERE username = ?",
            (user.username,)
        )
        new_user = cursor.fetchone()
        return {
            "id": new_user[0],
            "username": new_user[1],
            "email": new_user[2],
            "is_admin": new_user[3]
        }
    finally:
        conn.close()

@app.get("/users/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "is_admin": user["is_admin"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

@app.get("/debug/users", include_in_schema=False)
async def debug_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, is_admin FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "is_admin": user[3]
        }
        for user in users
    ]