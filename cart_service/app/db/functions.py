# cart_service/app/db/functions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from db.models import Cart, CartItem
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import text, delete
from metrics import db_metrics
import httpx
import requests
from http import HTTPStatus
import jwt
import os

@db_metrics(operation="get_cart_items")
async def get_cart_items(db: AsyncSession, user_id: int):
    """
    Получить товары из корзины пользователя.
    """
    cart_result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    cart = cart_result.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_items_result = await db.execute(select(CartItem).filter(CartItem.cart_id == cart.id))
    cart_items = cart_items_result.scalars().all()

    items = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in cart_items
    ]

    return items


@db_metrics(operation="get_cart_by_user_id")
async def get_cart_by_user_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    return result.scalar_one_or_none()


@db_metrics(operation="add_product_to_cart")
async def add_product_to_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int = 1):

    cart = await get_cart_by_user_id(db, user_id)
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    cart_item = await db.execute(select(CartItem).filter(CartItem.product_id == product_id, CartItem.cart_id == cart.id))
    cart_item = cart_item.scalar_one_or_none()

    if cart_item:
        cart_item.quantity += quantity
    else:
        new_item = CartItem(product_id=product_id, quantity=quantity, cart_id=cart.id)
        db.add(new_item)
    
    await db.commit()
    return cart


@db_metrics(operation="get_cart_with_items")
async def get_cart_with_items(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items))  
    )
    cart = result.scalar_one_or_none()

    if not cart:
        return None

    cart_dict = {
        "id": cart.id,
        "user_id": cart.user_id,
        "cart_items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
            }
            for item in cart.items
        ]
    }

    return cart_dict


@db_metrics(operation="clear_user_cart")
async def clear_user_cart(db: AsyncSession, user_id: int):
    """Функция для очистки корзины пользователя"""
    cart = await db.execute(select(Cart).filter(Cart.user_id == user_id))
    cart = cart.scalar_one_or_none()

    if cart:
        await db.execute(delete(CartItem).filter(CartItem.cart_id == cart.id))
        await db.commit()  # Сохраняем изменения в базе данных

# Удаление товара из корзины
@db_metrics(operation="remove_product_from_cart")
async def remove_product_from_cart(db: AsyncSession, user_id: int, product_id: int):
    cart = await get_cart_by_user_id(db, user_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart_item = await db.execute(select(CartItem).filter(CartItem.product_id == product_id, CartItem.cart_id == cart.id))
    cart_item = cart_item.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Product not found in the cart")

    await db.delete(cart_item)
    await db.commit()
    return cart

@db_metrics(operation="update_product_quantity_in_cart")
async def update_product_quantity_in_cart(db: AsyncSession, user_id: int, product_id: int, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")

    cart = await get_cart_by_user_id(db, user_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://catalog_service:8003/api/get_product?id={product_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Product not found in catalog")
        product = resp.json()
        stock = product.get("stock", 0)
        if quantity > stock:
            raise HTTPException(status_code=400, detail=f"Максимальное количество для заказа: {stock}")

    cart_item = await db.execute(select(CartItem).filter(CartItem.product_id == product_id, CartItem.cart_id == cart.id))
    cart_item = cart_item.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Product not found in the cart")

    cart_item.quantity = quantity
    await db.commit()
    return cart

@db_metrics(operation="get_all_cart_items")
async def get_all_cart_items(db: AsyncSession, user_id: int):
    cart = await get_cart_by_user_id(db, user_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    return cart.items

async def create_order_logic(token: str, db: AsyncSession):
    from db.functions import get_cart_with_items, clear_user_cart
    from db.models import CartItem
    user_id = None
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")

    cart_data = await get_cart_with_items(db, user_id)
    if not cart_data:
        return {"error": "Cart not found"}

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
    if order_id:
        for item in cart_data["cart_items"]:
            try:
                requests.post(
                    "http://catalog_service:8003/api/products/decrement_stock",
                    json={"product_id": item["product_id"], "quantity": item["quantity"]},
                    timeout=3
                )
            except Exception as e:
                print(f"Ошибка уменьшения stock для товара {item['product_id']}: {e}")
        await clear_user_cart(db, user_id)
    return {"message": "Order created successfully"}
