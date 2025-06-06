# auth_service/app/main.py
import json
from fastapi import Depends, HTTPException, status, FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from auth_utils import hash_password, verify_password, create_access_token
from db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db.functions import *
from db.init_db import init_db
from jwt import decode, DecodeError, ExpiredSignatureError
from db.schemas import UserBase, OrderItemBase, OrderBase, SellerRegister
import jwt
from fastapi.security import OAuth2PasswordBearer
from logging_decorator import log_to_kafka
from metrics import api_metrics, metrics_endpoint
from config.tracing import setup_tracing
from metrics.tracing_decorator import trace_function
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from http import HTTPStatus


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str):
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")

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
    user_details = await get_user_with_details(db, email)
    
    if not user_details:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")
    
    return user_details

@app.post("/register")
@log_to_kafka
@api_metrics()
@trace_function(name="register", include_request=True)
async def register(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    return await register_user_logic(db, data)

@app.post("/login")
@log_to_kafka
@api_metrics()
@trace_function(name="login", include_request=True)
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    return await login_user_logic(db, data)

@app.post("/create_order")
@log_to_kafka
@api_metrics()
@trace_function(name="create_order", include_request=True)
async def create_user_order(request: Request, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if token is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Authorization token is missing")
    user_id = verify_token(token)
    cart_data = await request.json()
    return await create_order_logic(db, user_id, cart_data)

@app.get("/")
@log_to_kafka
@api_metrics()
@trace_function(name="health_check", include_request=True)
async def health_check():
    """Эндпоинт проверки работоспособности."""
    return {"status": "auth_service running"}

@app.post("/register/seller")
@log_to_kafka
@api_metrics()
@trace_function(name="register_seller", include_request=True)
async def register_seller_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    return await register_seller_logic(db, data)

@app.get("/api/seller/{user_id}")
@log_to_kafka
@api_metrics()
@trace_function(name="get_seller", include_request=True)
async def get_seller_info(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить информацию о продавце по user_id."""
    seller = await get_seller_by_user_id(db, user_id)
    return {
        "user_id": seller.user_id,
        "shop_name": seller.shop_name,
        "inn": seller.inn,
        "description": seller.description
    }

@app.post("/profile/edit_user")
@log_to_kafka
@api_metrics()
@trace_function(name="edit_user_profile", include_request=True)
async def edit_user_profile(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    return await edit_user_profile_logic(db, data)

@app.post("/profile/edit_seller")
@log_to_kafka
@api_metrics()
@trace_function(name="edit_seller_profile", include_request=True)
async def edit_seller_profile(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    return await edit_seller_profile_logic(db, data)

@app.get("/api/users")
@log_to_kafka
@api_metrics()
@trace_function(name="get_users_for_admin", include_request=True)
async def get_users_for_admin(search: str = '', role: str = '', db: AsyncSession = Depends(get_db)):
    return await get_users_for_admin_logic(db, search, role)

@app.post("/admin_delete_user")
@log_to_kafka
@api_metrics()
@trace_function(name="admin_delete_user", include_request=True)
async def admin_delete_user(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    user_id = data.get("id")
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Missing or invalid token")
    jwt_token = token.split(" ", 1)[1]
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
    except Exception:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
    if role not in ("admin", "RoleEnum.admin"):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Only admin can delete users")
    return await admin_delete_user_logic(db, user_id)

@app.get("/admin/orders")
@log_to_kafka
@api_metrics()
@trace_function(name="admin_get_orders", include_request=True)
async def admin_get_orders(request: Request, search: str = '', status: str = '', db: AsyncSession = Depends(get_db)):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Missing or invalid token")
    jwt_token = token.split(" ", 1)[1]
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
    except Exception:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
    if role not in ("admin", "RoleEnum.admin"):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Only admin can view orders")
    orders_data = await admin_get_orders_logic(db, search, status)
    return JSONResponse(content=orders_data)

@app.post("/admin/update_order_status")
@log_to_kafka
@api_metrics()
@trace_function(name="admin_update_order_status", include_request=True)
async def admin_update_order_status(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    order_id = data.get("order_id")
    status = data.get("status")
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Missing or invalid token")
    jwt_token = token.split(" ", 1)[1]
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
    except Exception:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
    if role not in ("admin", "RoleEnum.admin"):
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Only admin can update order status")
    return await admin_update_order_status_logic(db, order_id, status)
