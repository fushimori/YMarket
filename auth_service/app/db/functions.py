# auth_service/app/db/functions.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from db.models import User, Wishlist, Order, OrderItem, Seller
from db.schemas import UserBase, OrderItemBase, OrderBase, SellerRegister
from sqlalchemy.orm import selectinload
from metrics import db_metrics
from http import HTTPStatus

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
    Получить информацию о пользователе, включая список желаемого и заказы, а для продавца — seller_info.
    """
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        # "wishlist": [
        #     {"product_id": item.product_id} for item in wishlist
        # ],
        # "orders": orders_with_items,
        # "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
    }

    if user_data["role"] == "seller":
        seller_result = await db.execute(select(Seller).filter(Seller.user_id == user.id))
        seller = seller_result.scalar_one_or_none()
        if seller:
            user_data["seller_info"] = {
                "shop_name": seller.shop_name,
                "inn": seller.inn,
                "description": seller.description
            }
        else:
            user_data["seller_info"] = None
    else:
        wishlist_result = await db.execute(select(Wishlist).filter(Wishlist.user_id == user.id))
        wishlist = wishlist_result.scalars().all()
        orders_result = await db.execute(select(Order).filter(Order.user_id == user.id))
        orders = orders_result.scalars().all()
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
        user_data["wishlist"] = [
            {"product_id": item.product_id} for item in wishlist
        ]
        user_data["orders"] = orders_with_items

    return user_data

# Функция для создания нового пользователя
@db_metrics(operation="create_user")
async def create_user(db: AsyncSession, user_data: dict):
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

# Функция для создания продавца
@db_metrics(operation="create_seller")
async def create_seller(db: AsyncSession, user_id: int, seller_data: dict):
    db_seller = Seller(
        user_id=user_id,
        shop_name=seller_data['shop_name'],
        inn=seller_data.get('inn'),
        description=seller_data.get('description')
    )
    db.add(db_seller)
    await db.commit()
    await db.refresh(db_seller)
    return db_seller

# Функция для регистрации продавца
@db_metrics(operation="register_seller")
async def register_seller(db: AsyncSession, seller_data: SellerRegister):
    # print("DEBUG: auth function register_seller, seller_data:", seller_data)
    existing_user = await get_user_by_email(db, seller_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User {seller_data.email} already exists")
    db_user = User(
        email=seller_data.email,
        hashed_password=seller_data.password,  # Уже хешированный пароль
        is_active=True,
        role='seller'
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    db_seller = Seller(
        user_id=db_user.id,
        shop_name=seller_data.shop_name,
        inn=seller_data.inn,
        description=seller_data.description
    )
    db.add(db_seller)
    await db.commit()
    await db.refresh(db_seller)
    return db_user, db_seller

@db_metrics(operation="get_seller_by_user_id")
async def get_seller_by_user_id(db: AsyncSession, user_id: int):
    seller_result = await db.execute(select(Seller).filter(Seller.user_id == user_id))
    seller = seller_result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Seller not found")
    return seller

async def register_user_logic(db: AsyncSession, data: dict):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Email and password are required")
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"User {email} already exists")
    from auth_utils import hash_password
    hashed_password = hash_password(password)
    new_user = await create_user(db, {"email": email, "hashed_password": hashed_password, "is_active": True})
    return {"status": "success", "message": f"User {email} successfully registered"}

async def login_user_logic(db: AsyncSession, data: dict):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Email and password are required")
    user = await get_user_by_email(db, email)
    from auth_utils import verify_password, create_access_token
    if user and verify_password(password, user.hashed_password):
        token = create_access_token({"sub": email, "id": user.id, "role": str(user.role)})
        return {"status": "success", "message": "Login successful", "token": token}
    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid email or password")

async def create_order_logic(db: AsyncSession, user_id: int, cart_data: dict):
    from db.schemas import OrderBase, OrderItemBase
    order_data = OrderBase(status="pending")
    order_items = [OrderItemBase(product_id=item["product_id"], quantity=item["quantity"]) for item in cart_data["cart_items"]]
    new_order = await create_order(db, user_id, order_data, order_items)
    return {"order_id": new_order.id}

async def edit_user_profile_logic(db: AsyncSession, data: dict):
    email = data.get("email")
    loyalty_card_number = data.get("loyalty_card_number")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")
    if hasattr(user, "loyalty_card_number"):
        user.loyalty_card_number = loyalty_card_number
    await db.commit()
    await db.refresh(user)
    return {"success": True}

async def edit_seller_profile_logic(db: AsyncSession, data: dict):
    email = data.get("email")
    shop_name = data.get("shop_name")
    inn = data.get("inn")
    description = data.get("description")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")
    seller_result = await db.execute(select(Seller).filter(Seller.user_id == user.id))
    seller = seller_result.scalar_one_or_none()
    if not seller:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Seller not found")
    seller.shop_name = shop_name
    seller.inn = inn
    seller.description = description
    await db.commit()
    await db.refresh(seller)
    return {"success": True}

async def admin_delete_user_logic(db: AsyncSession, user_id: int):
    await delete_user(db, user_id)
    return {"success": True}

async def admin_get_orders_logic(db: AsyncSession, search: str, status: str):
    from sqlalchemy.orm import selectinload
    query = select(Order).options(selectinload(Order.order_items), selectinload(Order.user))
    if status:
        query = query.filter(Order.status == status)
    result = await db.execute(query)
    orders = result.scalars().all()
    orders_data = []
    for order in orders:
        user_email = order.user.email if order.user else ""
        if search and search.lower() not in user_email.lower():
            continue
        items = []
        for item in order.order_items:
            items.append({"product_id": item.product_id, "quantity": item.quantity})
        orders_data.append({"order_id": order.id, "status": order.status, "user_email": user_email, "items": items})
    return orders_data

async def admin_update_order_status_logic(db: AsyncSession, order_id: int, status: str):
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Order not found")
    order.status = status
    await db.commit()
    await db.refresh(order)
    return {"success": True}

async def get_users_for_admin_logic(db: AsyncSession, search: str = '', role: str = ''):
    from db.models import User, Seller
    from sqlalchemy.future import select
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
                user_dict["seller_info"] = {"shop_name": seller.shop_name}
        users_data.append(user_dict)
    return users_data

async def register_seller_logic(db: AsyncSession, data: dict):
    from auth_utils import hash_password
    from db.schemas import SellerRegister
    password = data.get("password")
    if not password:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Password is required")
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
