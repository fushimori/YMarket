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


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

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
            token = create_access_token({"sub": email, "id": user.id, "role": str(user.role)})
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


@app.post("/register/seller")
@log_to_kafka
@api_metrics()
@trace_function(name="register_seller", include_request=True)
async def register_seller_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """Регистрация продавца (seller)."""
    try:
        data = await request.json()
        password = data.get("password")
        if not password:
            raise HTTPException(status_code=400, detail="Password is required")
        hashed_password = hash_password(password)
        seller_data = SellerRegister(
            email=data.get("email"),
            password=hashed_password,
            shop_name=data.get("shop_name"),
            inn=data.get("inn"),
            description=data.get("description")
        )
        user, seller = await register_seller(db, seller_data)
        return {"status": "success", "message": f"Seller {user.email} successfully registered", "user_id": user.id, "seller_id": seller.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    email = data.get("email")
    loyalty_card_number = data.get("loyalty_card_number")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Добавляем/обновляем поле loyalty_card_number (если оно есть в модели)
    if hasattr(user, "loyalty_card_number"):
        user.loyalty_card_number = loyalty_card_number
    else:
        # Если поля нет, можно добавить динамически (или проигнорировать)
        pass
    await db.commit()
    await db.refresh(user)
    return {"success": True}

@app.post("/profile/edit_seller")
@log_to_kafka
@api_metrics()
@trace_function(name="edit_seller_profile", include_request=True)
async def edit_seller_profile(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    shop_name = data.get("shop_name")
    inn = data.get("inn")
    description = data.get("description")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    seller_result = await db.execute(select(Seller).filter(Seller.user_id == user.id))
    seller = seller_result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    seller.shop_name = shop_name
    seller.inn = inn
    seller.description = description
    await db.commit()
    await db.refresh(seller)
    return {"success": True}

@app.get("/api/users")
@log_to_kafka
@api_metrics()
@trace_function(name="get_users_for_admin", include_request=True)
async def get_users_for_admin(search: str = '', role: str = '', db: AsyncSession = Depends(get_db)):
    query = select(User)
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    if role:
        query = query.filter(User.role == role)
    result = await db.execute(query)
    users = result.scalars().all()
    users_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "role": str(user.role),
            "is_active": user.is_active
        }
        if user.role == 'seller':
            seller_result = await db.execute(select(Seller).filter(Seller.user_id == user.id))
            seller = seller_result.scalar_one_or_none()
            if seller:
                user_dict["seller_info"] = {
                    "shop_name": seller.shop_name
                }
        users_data.append(user_dict)
    return users_data

@app.post("/admin_delete_user")
@log_to_kafka
@api_metrics()
@trace_function(name="admin_delete_user", include_request=True)
async def admin_delete_user(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    user_id = data.get("id")
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    jwt_token = token.split(" ", 1)[1]
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if role not in ("admin", "RoleEnum.admin"):
        raise HTTPException(status_code=403, detail="Only admin can delete users")
    await delete_user(db, user_id)
    return {"success": True}

@app.get("/admin/orders")
@log_to_kafka
@api_metrics()
@trace_function(name="admin_get_orders", include_request=True)
async def admin_get_orders(request: Request, search: str = '', status: str = '', db: AsyncSession = Depends(get_db)):
    # Проверка роли админа по токену
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    jwt_token = token.split(" ", 1)[1]
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if role not in ("admin", "RoleEnum.admin"):
        raise HTTPException(status_code=403, detail="Only admin can view orders")

    # Получаем все заказы с пользователями и товарами
    query = select(Order).options(selectinload(Order.order_items), selectinload(Order.user))
    if status:
        query = query.filter(Order.status == status)
    result = await db.execute(query)
    orders = result.scalars().all()

    # Фильтрация по email пользователя (если search)
    orders_data = []
    for order in orders:
        user_email = order.user.email if order.user else ""
        if search and search.lower() not in user_email.lower():
            continue
        items = []
        for item in order.order_items:
            items.append({
                "product_id": item.product_id,
                "quantity": item.quantity
            })
        orders_data.append({
            "order_id": order.id,
            "status": order.status,
            "user_email": user_email,
            "items": items
        })
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
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    jwt_token = token.split(" ", 1)[1]
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if role not in ("admin", "RoleEnum.admin"):
        raise HTTPException(status_code=403, detail="Only admin can update order status")
    # Обновляем статус заказа
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    await db.commit()
    await db.refresh(order)
    return {"success": True}
