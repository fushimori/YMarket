# cart_service/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from typing import List, AsyncGenerator
from db.schemas import CartItemBase, CartResponse
from db.functions import *
from db.init_db import init_db
import json
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from db.models import Cart, CartItem
import jwt
import requests



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


async def lifespan(app: FastAPI) -> AsyncGenerator:
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/cart/add")
async def add_to_cart(product_id: int = None, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user_id = verify_token(token)
    cart = await add_product_to_cart(db, user_id, product_id)
    print("DEBUG CART SERVICE add_to_cart, user_id:", user_id, "token:", token)# Получаем user_id из токена
    print("DEBUG CART SERVICE add_to_cart, cart:", cart)
    # Здесь логика добавления товара в корзину для user_id
    if cart:
        return {"success": True, "message": "Product added to cart"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add product to cart")

# убрать обращение к бд здесь
@app.get("/check_cart")
async def check_cart(product_id: int = None, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user_id = verify_token(token)  # Проверка токена
    print("DEBUG CART SERVICE check_cart, user_id: ", user_id)
    # Проверка, есть ли корзина у пользователя
    cart = await get_cart_by_user_id(db, user_id)
    print("DEBUG CART SERVICE check_cart, cart: ", cart)
    if not cart:
        return {"exists": False}

    # Проверка, есть ли товар в корзине
    cart_item = await db.execute(
        select(CartItem).filter(
            CartItem.product_id == product_id,
            CartItem.cart_id == cart.id
        )
    )
    cart_item = cart_item.scalar_one_or_none()
    print("DEBUG CART SERVICE check_cart, cart_item: ", cart_item)

    if cart_item:
        return {"exists": True}
    return {"exists": False}


@app.get("/cart/delete")
async def delete_from_cart(product_id: int = None, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user_id = verify_token(token)
    cart = await remove_product_from_cart(db, user_id, product_id)
    print("DEBUG CART SERVICE delete_from_cart, user_id:", user_id, "token:", token)# Получаем user_id из токена
    print("DEBUG CART SERVICE delete_from_cart, cart:", cart)
    # Здесь логика добавления товара в корзину для user_id
    if cart:
        return {"success": True, "message": "Product delete from cart"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete product from cart")




@app.get("/cart/createorder")
async def create_order(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        user_id = verify_token(token)
        cart_data = await get_cart_with_items(db, user_id)

        if not cart_data:
            return {"error": "Cart not found"}
        else:
            print("DEBUG CART SERVICE create_order, cart_data:", cart_data)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        order_response = requests.post(
            "http://auth_service:8001/create_order",
            headers=headers,
            json=cart_data
        )
        if order_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Order service error")

        order_id = order_response.json().get("order_id")

        # Шаг 1: Запрос к сервису оплаты
        # payment_response = requests.post(
        #     "http://localhost:8005/transactions/",
        #     json={
        #         "order_id": order_response["order_id"],  # Пример заказа (замените на реальный ID)
        #         "payment_method": "credit_card",  # или другой способ оплаты
        #         "amount": 100,  # Замените на сумму заказа
        #         "payment_reference": "some-reference-id"
        #     }
        # )
        # if payment_response.status_code != 200:
        #     raise HTTPException(status_code=502, detail="Payment service error")
        #
        # payment_result = payment_response.json()
        # if payment_result.get("status") != "COMPLETED":
        #     return JSONResponse(status_code=400, content={"message": "Payment failed"})

        # Шаг 2: Запрос к корзине для формирования заказа
        if order_id:
            await clear_user_cart(db, user_id)

        return {"message": "Order created successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cart/{user_id}")
async def get_cart(user_id: int, db: AsyncSession = Depends(get_db)):
    items = await get_cart_items(db, user_id)
    print("DEBUG: cart items: ", items)
    return items

# Добавление товара в корзину
@app.post("/cart/{user_id}", response_model=CartResponse)
async def add_to_cart(user_id: int, product: CartItemBase, db: AsyncSession = Depends(get_db)):
    cart = await add_product_to_cart(db, user_id, product.product_id, product.quantity)
    return cart

# Обновление количества товара в корзине
@app.put("/cart/{user_id}/{product_id}", response_model=CartResponse)
async def update_cart_item_quantity(user_id: int, product_id: int, quantity: int, db: AsyncSession = Depends(get_db)):
    cart = await update_product_quantity_in_cart(db, user_id, product_id, quantity)
    return cart

# # Удаление товара из корзины
# @app.delete("/cart/{user_id}/{product_id}", response_model=CartResponse)
# async def remove_from_cart(user_id: int, product_id: int, db: AsyncSession = Depends(get_db)):
#     cart = await remove_product_from_cart(db, user_id, product_id)
#     return cart

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "cart_service running"}
