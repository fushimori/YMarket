# auth_service/app/db/schemas.py
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from datetime import datetime

# Enum для ролей пользователя
class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"
    moderator = "moderator"
    seller = "seller"

# Схема пользователя
class UserBase(BaseModel):
    email: str
    is_active: bool = True
    loyalty_card_number: Optional[str] = None  # Карта лояльности

    class Config:
        orm_mode = True

class User(UserBase):
    id: int
    role: RoleEnum  # Роль пользователя

    class Config:
        orm_mode = True

# Схема отложенных товаров
class WishlistBase(BaseModel):
    product_id: int

    class Config:
        orm_mode = True

class Wishlist(WishlistBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

# Схема заказа
class OrderBase(BaseModel):
    status: str = "pending"
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Order(OrderBase):
    id: int
    user_id: int
    order_items: List["OrderItem"] = []

    class Config:
        orm_mode = True

# Схема для элементов заказа
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

    class Config:
        orm_mode = True

class OrderItem(OrderItemBase):
    id: int
    order_id: int

    class Config:
        orm_mode = True
