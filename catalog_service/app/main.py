# catalog_service/app/main.py

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.schemas import ProductBase, Product as ProductSchema, CategorySchemas  # Импортируем Pydantic модель
from typing import List, AsyncGenerator
from db.functions import *
from db.init_db import init_db
from fastapi.middleware.cors import CORSMiddleware
from search.elastic import create_index, index_product, delete_product_from_index, search_products
import asyncio


async def lifespan(app: FastAPI) -> AsyncGenerator:
    await init_db()
    await asyncio.sleep(5)  # дать время на запуск Elasticsearch
    await create_index()
    
    # ✅ Индексируем все товары из базы после создания индекса
    async for db in get_db():
        products = await get_all_products(db)
        for product in products:
            await index_product(product)

    yield



app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Укажите адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/products")
async def read_products(
    searchquery: str = Query(default='', alias="search"),
    category: int = None,
    db: AsyncSession = Depends(get_db)
):
    if searchquery:  # Если пользователь вводит запрос
        products = await search_products(searchquery)
        if category is not None:
            products = [p for p in products if p["category_id"] == category]
        return products
    else:
        products = await get_all_products(db, category, "")
        return products



@app.get("/api/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    categories = await get_all_categories(db)
    # print("DEBUG CATALOG SERVICE: categories: ", categories)
    return categories

@app.get("/api/get_product")  # Указываем Pydantic модель для списка продуктов
async def get_product(id: int = None, db: AsyncSession = Depends(get_db)):
    print("DEBUG CATALOG SERVICE get_product: productid:", id)
    products = await get_product_by_id(db, id)
    print("DEBUG CATALOG SERVICE get_product: products: ", products)
    return products


@app.get("/api/get_seller")  # Указываем Pydantic модель для списка продуктов
async def get_seller(id: int = None, db: AsyncSession = Depends(get_db)):
    print("DEBUG CATALOG SERVICE get_seller: seller_id:", id)
    seller = await get_seller_by_id(db, id)
    print("DEBUG CATALOG SERVICE get_seller: products: ", seller)
    return seller


@app.get("/products/{product_id}", response_model=ProductSchema)  # Указываем Pydantic модель для одного товара
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=ProductSchema)
async def create_new_product(product: ProductBase, db: AsyncSession = Depends(get_db)):
    new_product = await create_product(
        db,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id,
        seller_id=product.seller_id
    )
    await index_product(new_product)  # Индексируем в Elasticsearch
    return new_product



@app.put("/products/{product_id}", response_model=ProductSchema)
async def update_existing_product(
    product_id: int, product: ProductBase, db: AsyncSession = Depends(get_db)
):
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



@app.delete("/products/{product_id}", response_model=ProductSchema)
async def delete_existing_product(product_id: int, db: AsyncSession = Depends(get_db)):
    deleted_product = await delete_product(db, product_id)
    if not deleted_product:
        raise HTTPException(status_code=404, detail="Product not found")
    await delete_product_from_index(product_id)  # Удаляем из Elasticsearch
    return deleted_product

