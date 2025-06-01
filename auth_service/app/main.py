# auth_service/app/main.py
import json
from fastapi import Depends, HTTPException, status, FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from auth_utils import hash_password, verify_password, create_access_token
from db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db.functions import *
from db.init_db import init_db
from db.schemas import UserBase, OrderItemBase, OrderBase
from jwt import decode, DecodeError, ExpiredSignatureError
from fastapi.security import OAuth2PasswordBearer
from logging_decorator import log_to_kafka
from metrics import api_metrics, metrics_endpoint
from config.tracing import setup_tracing
from metrics.tracing_decorator import trace_function


SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str):
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# FastAPI Application
app = FastAPI()

# Инициализация трейсинга
tracer = setup_tracing(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application lifespan for initializing the database
@app.on_event("startup")
@trace_function(name="startup_event")
async def app_startup():
    await init_db()

@app.get("/metrics")
@trace_function(name="get_metrics", include_request=True)
async def get_metrics():
    """Эндпоинт для Prometheus"""
    return await metrics_endpoint()

@app.get("/get_user_id")
@log_to_kafka
@api_metrics()
@trace_function(name="get_user_id", include_request=True)
async def get_user_id(email: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email)
    return {"user_id": user.id}

@app.get("/role")
@log_to_kafka
@api_metrics()
@trace_function(name="get_role", include_request=True)
async def get_role(email: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email)
    return {"role": user.role}

@app.get("/profile")
@log_to_kafka
@api_metrics()
@trace_function(name="get_profile", include_request=True)
async def get_profile(email: str, db: AsyncSession = Depends(get_db)):
    """Получить профиль текущего пользователя по email."""
    print(f"DEBUG: Fetching profile for user {email}")
    
    user_details = await get_user_with_details(db, email)
    
    if not user_details:
        print(f"ERROR: User {email} not found in database.")
        raise HTTPException(status_code=404, detail="User not found")
    
    print(f"DEBUG: Profile data for user {email}: {user_details}")
    return user_details

@app.post("/create_order")
@log_to_kafka
@api_metrics()
@trace_function(name="create_order", include_request=True)
async def create_user_order(request: Request, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    print("DEBUG AUTH SERVICE create_user_order" )
    try:
        if token is None:
            raise HTTPException(status_code=400, detail="Authorization token is missing")

        user_id = verify_token(token)
        print("DEBUG AUTH SERVICE create_user_order, user_id", user_id)

        cart_data = await request.json()
        print("DEBUG AUTH SERVICE create_user_order, cart_data", cart_data)
        
        order_data = OrderBase(status="pending")
        order_items = [OrderItemBase(product_id=item["product_id"], quantity=item["quantity"])
                       for item in cart_data["cart_items"]]

        new_order = await create_order(db, user_id, order_data, order_items)

        return {"order_id": new_order.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
@log_to_kafka
@api_metrics()
@trace_function(name="health_check", include_request=True)
async def health_check():
    """Эндпоинт проверки работоспособности."""
    return {"status": "auth_service running"}

@app.post("/register")
@log_to_kafka
@api_metrics()
@trace_function(name="register", include_request=True)
async def register(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle user registration."""
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        existing_user = await get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=400, detail=f"User {email} already exists")

        hashed_password = hash_password(password)
        new_user = await create_user(db, {"email": email, "hashed_password": hashed_password, "is_active": True})
        
        return {"status": "success", "message": f"User {email} successfully registered"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
@log_to_kafka
@api_metrics()
@trace_function(name="login", include_request=True)
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle user login."""
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        user = await get_user_by_email(db, email)

        if user and verify_password(password, user.hashed_password):
            token = create_access_token({"sub": email, "id": user.id})
            return {
                "status": "success",
                "message": "Login successful",
                "token": token,
            }
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
