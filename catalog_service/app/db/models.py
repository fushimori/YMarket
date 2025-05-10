# catalog_service/app/db/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)  # Количество в наличии
    active = Column(Boolean, default=True)  # Признак активного товара
    category_id = Column(Integer, ForeignKey("categories.id"))  # Связь с категорией товара
    seller_id = Column(Integer, ForeignKey("sellers.id"))  # Продавец товара

    # Связи
    category = relationship("Category", back_populates="products")
    seller = relationship("Seller", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    questions = relationship("Question", back_populates="product")
    # related_products = relationship("Product", secondary="related_products", back_populates="related_products")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)

    # Связь с товарами
    products = relationship("Product", back_populates="category")

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Связь с товарами
    products = relationship("Product", back_populates="seller")

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    image_url = Column(String, nullable=False)

    # Связь с товаром
    product = relationship("Product", back_populates="images")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)

    # Связь с товаром
    product = relationship("Product", back_populates="reviews")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    question = Column(String, nullable=False)
    answer = Column(String, nullable=True)

    # Связь с товаром
    product = relationship("Product", back_populates="questions")

class RelatedProduct(Base):
    __tablename__ = "related_products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    related_product_id = Column(Integer, ForeignKey("products.id"))

    # Связь с товарами
    product = relationship("Product", foreign_keys=[product_id])
    related_product = relationship("Product", foreign_keys=[related_product_id])


