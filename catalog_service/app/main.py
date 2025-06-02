# catalog_service/app/main.py

from fastapi import FastAPI, Depends, HTTPException, Query, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.schemas import ProductBase, Product as ProductSchema, CategorySchemas, ProductCreate  # Импортируем Pydantic модель и ProductCreate
from typing import List, AsyncGenerator
from db.functions import *
from db.init_db import init_db
from fastapi.middleware.cors import CORSMiddleware
from logging_decorator import log_to_kafka
from metrics import metrics_endpoint, api_metrics
from config.tracing import setup_tracing
from metrics.tracing_decorator import trace_function
from search.elastic import create_index, index_product, delete_product_from_index, search_products

from fastapi.security import OAuth2PasswordBearer
import jwt

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

# Инициализация трейсинга
tracer = setup_tracing(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://main_service:8000", "http://localhost:8003"],  # Укажите адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/metrics")
@trace_function(name="get_metrics", include_request=True)
async def metrics():
    """
    Эндпоинт для Prometheus метрик
    """
    return await metrics_endpoint()

@app.get("/api/products")  # Указываем Pydantic модель для списка продуктов
@log_to_kafka
@api_metrics()
@trace_function(name="read_products", include_request=True)
async def read_products(
    searchquery: str = Query(default='', alias="search"),
    category: int = None,
    seller: int = None,
    db: AsyncSession = Depends(get_db)
):
# print("DEBUG CATALOG SERVICE: seller:", seller, "category:", category)
    if searchquery:  # Если пользователь вводит запрос
        products = await search_products(searchquery)
        if category is not None:
            products = [p for p in products if p["category_id"] == category]
        if seller is not None:
            products = [p for p in products if p["seller_id"] == seller]
        return products
    else:
        products = await get_all_products(db, category, "")
        if seller is not None:
            products = [p for p in products if p["seller_id"] == seller]
        return products


@app.get("/api/categories")
@log_to_kafka
@api_metrics()
@trace_function(name="get_categories", include_request=True)
async def get_categories(db: AsyncSession = Depends(get_db)):
    categories = await get_all_categories(db)
    # print("DEBUG CATALOG SERVICE: categories: ", categories)
    return categories

@app.get("/api/get_product")  # Указываем Pydantic модель для списка продуктов
@log_to_kafka
@api_metrics()
@trace_function(name="get_product", include_request=True)
async def get_product(id: int = None, db: AsyncSession = Depends(get_db)):
    print("DEBUG CATALOG SERVICE get_product: productid:", id)
    product = await get_product_by_id(db, id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    print("DEBUG CATALOG SERVICE get_product: products: ", product)
    return product


@app.get("/api/get_seller")  # Указываем Pydantic модель для списка продуктов
@log_to_kafka
@api_metrics()
@trace_function(name="get_seller", include_request=True)
async def get_seller(id: int = None, db: AsyncSession = Depends(get_db)):
    print("DEBUG CATALOG SERVICE get_seller: seller_id:", id)
    seller = await get_seller_by_id(db, id)
    print("DEBUG CATALOG SERVICE get_seller: products: ", seller)
    return seller


@app.get("/products/{product_id}", response_model=ProductSchema)  # Указываем Pydantic модель для одного товара
@log_to_kafka
@api_metrics()
@trace_function(name="read_product", include_request=True)
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=ProductSchema)
@log_to_kafka
@api_metrics()
@trace_function(name="create_new_product", include_request=True)
async def create_new_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    # Извлекаем параметры из объекта ProductCreate
    new_product = await create_product(
        db,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id,
        seller_id=product.seller_id
    )
    # Преобразуем SQLAlchemy-модель в Pydantic-схему, затем в словарь для индексации
    product_for_indexing = ProductSchema.from_orm(new_product).dict()
    await index_product(product_for_indexing) # Индексируем в Elasticsearch
    return new_product



@app.put("/edit_product/{product_id}", response_model=ProductSchema)
@log_to_kafka
@api_metrics()
@trace_function(name="update_existing_product", include_request=True)
async def update_existing_product(
    product_id: int, product: ProductBase, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    user_id = verify_token(token)

    existing_product = await get_product_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")

    if existing_product['seller_id'] != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to update this product")

    # Передаем параметры из объекта product в функцию update_product
    updated_product = await update_product(
        db,
        product_id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock
    )
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    await index_product(updated_product)  # Переиндексируем
    return updated_product


@app.delete("/products/{product_id}")  # Указываем Pydantic модель для ответа
@log_to_kafka
@api_metrics()
@trace_function(name="delete_existing_product", include_request=True)
async def delete_existing_product(product_id: int, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user_id = verify_token(token)

    existing_product = await get_product_by_id(db, product_id)
    if not existing_product:

        raise HTTPException(status_code=404, detail="Product not found")

    if existing_product['seller_id'] != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this product")

    deleted_product_id = await delete_product(db, product_id)
    if not deleted_product_id:
        raise HTTPException(status_code=500, detail="Failed to delete product")
    
    return {"message": f"Product with ID {deleted_product_id} deleted successfully"}
