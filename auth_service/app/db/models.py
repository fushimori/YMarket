# auth_service/app/db/models.py
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import relationship
from db.database import Base
from enum import Enum as PyEnum
from datetime import datetime

# Enum для ролей пользователя
class RoleEnum(str, PyEnum):
    user = "user"  # Обычный пользователь
    admin = "admin"  # Администратор
    moderator = "moderator"  # Модератор
    seller = "seller"  # Продавец

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)  # Активен ли пользователь
    role = Column(Enum(RoleEnum), default=RoleEnum.user)  # Роль пользователя
    # loyalty_card_number = Column(String, unique=True, nullable=True, default="")  # Номер карты лояльности (если есть)

    # Связь с отложенными товарами
    wishlist = relationship("Wishlist", back_populates="user")

    # Связь с заказами
    orders = relationship("Order", back_populates="user")

# Модель отложенных товаров
class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, nullable=False)

    # Связи
    user = relationship("User", back_populates="wishlist")

# Модель заказов
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())  # Дата создания заказа
    status = Column(String, default="pending")  # Статус заказа

    # Связи
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")

# Модель элементов в заказе
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer,nullable=False)
    quantity = Column(Integer, default=1)  # Количество товара

    #  Связи
    order = relationship("Order", back_populates="order_items")
    # product = relationship("Product", back_populates="order_items")

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    shop_name = Column(String, nullable=False)
    inn = Column(String, nullable=True)
    description = Column(String, nullable=True)

    user = relationship("User")
