# auth_service/app/main.py
import json
from fastapi import Depends, HTTPException, status, FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from auth_utils import hash_password, verify_password, create_access_token
from db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from db.functions import *
from db.init_db import init_db
from db.schemas import UserBase, OrderItemBase, OrderBase, SellerRegister
import jwt
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, ExpiredSignatureError, decode

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# FastAPI Application
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application lifespan for initializing the database
@app.on_event("startup")
async def app_startup():
    await init_db()

@app.get("/get_user_id")
async def get_user_id(email: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email)
    return {"user_id": user.id}

@app.get("/role")
async def get_role(email: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email)
    return {"role": user.role}

@app.get("/profile")
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
async def health_check():
    """Эндпоинт проверки работоспособности."""
    return {"status": "auth_service running"}

@app.post("/register")
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

@app.post("/register/seller")
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
async def get_seller_info(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить информацию о продавце по user_id."""
    seller = await get_seller_by_user_id(db, user_id)
    return {
        "user_id": seller.user_id,
        "shop_name": seller.shop_name,
        "inn": seller.inn,
        "description": seller.description
    }
