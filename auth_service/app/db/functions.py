# auth_service/app/db/functions.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from db.models import User, Wishlist, Order, OrderItem
from db.schemas import UserBase, OrderItemBase, OrderBase
from sqlalchemy.orm import selectinload
from metrics import db_metrics

# Функция для получения всех пользователей
@db_metrics(operation="get_all_users")
async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

# Функция для получения пользователя по ID
@db_metrics(operation="get_user_by_id")
async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

@db_metrics(operation="get_user_by_email")
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

@db_metrics(operation="get_user_with_details")
async def get_user_with_details(db: AsyncSession, email: str):
    """
    Получить информацию о пользователе, включая список желаемого и заказы, в формате JSON.
    """
    # Запрос для получения пользователя
    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Запрос для получения списка желаемого пользователя
    wishlist_result = await db.execute(select(Wishlist).filter(Wishlist.user_id == user.id))
    wishlist = wishlist_result.scalars().all()

    # Запрос для получения заказов пользователя
    orders_result = await db.execute(select(Order).filter(Order.user_id == user.id))
    orders = orders_result.scalars().all()

    # Для каждого заказа получаем его элементы
    orders_with_items = []
    for order in orders:
        order_items_result = await db.execute(select(OrderItem).filter(OrderItem.order_id == order.id))
        order_items = order_items_result.scalars().all()
        orders_with_items.append({
            "order_id": order.id,
            "status": order.status,
            "items": [
                {"product_id": item.product_id, "quantity": item.quantity}
                for item in order_items
            ]
        })

    # Формируем итоговый JSON
    user_data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "wishlist": [
            {"product_id": item.product_id} for item in wishlist
        ],
        "orders": orders_with_items
    }

    return user_data

# Функция для создания нового пользователя
@db_metrics(operation="create_user")
async def create_user(db: AsyncSession, user_data: dict):
    print("DEBUG: auth function create_user, user_data:", user_data)
    db_user = User(
        email=user_data['email'],
        hashed_password=user_data['hashed_password'],
        is_active=user_data['is_active']
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Функция для обновления данных пользователя
@db_metrics(operation="update_user")
async def update_user(db: AsyncSession, user_id: int, user_data: UserBase):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.email = user_data.email
    db_user.hashed_password = user_data.hashed_password
    db_user.is_active = user_data.is_active
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Функция для удаления пользователя
@db_metrics(operation="delete_user")
async def delete_user(db: AsyncSession, user_id: int):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(db_user)
    await db.commit()
    return db_user

# Функция для добавления товара в список отложенных
@db_metrics(operation="add_to_wishlist")
async def add_to_wishlist(db: AsyncSession, user_id: int, product_id: int):
    # Проверка существования пользователя
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверка, не добавлен ли уже товар
    db_wishlist = await db.execute(select(Wishlist).filter(Wishlist.user_id == user_id, Wishlist.product_id == product_id))
    existing_item = db_wishlist.scalar_one_or_none()
    if existing_item:
        raise HTTPException(status_code=400, detail="Product already in wishlist")
    
    new_wishlist_item = Wishlist(user_id=user_id, product_id=product_id)
    db.add(new_wishlist_item)
    await db.commit()
    await db.refresh(new_wishlist_item)
    return new_wishlist_item

# Функция для удаления товара из списка отложенных
@db_metrics(operation="remove_from_wishlist")
async def remove_from_wishlist(db: AsyncSession, user_id: int, product_id: int):
    db_wishlist = await db.execute(select(Wishlist).filter(Wishlist.user_id == user_id, Wishlist.product_id == product_id))
    wishlist_item = db_wishlist.scalar_one_or_none()
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    await db.delete(wishlist_item)
    await db.commit()
    return wishlist_item

# Функция для создания нового заказа
@db_metrics(operation="create_order")
async def create_order(db: AsyncSession, user_id: int, order_data: OrderBase, order_items: list[OrderItemBase]):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Создаем заказ
    new_order = Order(user_id=user_id, status=order_data.status)
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    # Добавляем элементы в заказ
    for item in order_items:
        order_item = OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity)
        db.add(order_item)
    
    await db.commit()
    await db.refresh(new_order)
    return new_order

# Функция для получения всех заказов пользователя
@db_metrics(operation="get_user_orders")
async def get_user_orders(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Order).filter(Order.user_id == user_id).offset(skip).limit(limit))
    return result.scalars().all()

# Функция для получения заказов с их элементами
@db_metrics(operation="get_order_with_items")
async def get_order_with_items(db: AsyncSession, order_id: int):
    result = await db.execute(
        select(Order)
        .filter(Order.id == order_id)
        .options(selectinload(Order.order_items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
