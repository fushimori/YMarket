# catalog_service / app / db / functions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from db.models import Product, Category
from db.schemas import ProductBase, Product as ProductSchema, CategorySchemas, ProductBase
from sqlalchemy.orm import selectinload
from metrics import db_metrics


# Получение всех продуктов с пагинацией
@db_metrics(operation="get_all_products")
async def get_all_products(db: AsyncSession, category: int = None, search: str = '', skip: int = 0, limit: int = 1000):
    if category:
        if search != '':
            result = await db.execute(
                select(Product).filter(Product.category_id == category).filter(
                    Product.name.ilike(f"%{search}%")).order_by(Product.name).offset(skip).limit(limit).options(selectinload(Product.images)))
        else:
            result = await db.execute(
                select(Product).filter(Product.category_id == category).order_by(Product.name).offset(skip).limit(
                    limit).options(selectinload(Product.images)))
    elif search != '':
        result = await db.execute(select(Product).filter(
            Product.name.ilike(f"%{search}%")).order_by(Product.name).offset(skip).limit(limit).options(selectinload(Product.images)))
    else:
        result = await db.execute(select(Product).order_by(Product.name).offset(skip).limit(limit).options(selectinload(Product.images)))
    products = result.scalars().all()
    products_list = [ProductBase.from_orm(product) for product in products]

    products_dict = [product.dict() for product in products_list]

    return products_dict

# Получение одного продукта
@db_metrics(operation="get_product_by_id")
async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.images))
        .filter(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if product is None:
        return None

    products_dict = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "category_id": product.category_id,
        "seller_id": product.seller_id,
        "category": {"id": product.category.id, "name": product.category.name} if product.category else None,
        "images": []  # Возвращаем пустой список вместо None
    }

    return products_dict

@db_metrics(operation="get_all_categories")
async def get_all_categories(db: AsyncSession):
    result = await db.execute(select(Category))
    categories = result.scalars().all()

    # Преобразуем SQLAlchemy объекты в Pydantic модели
    categories_list = [CategorySchemas.from_orm(category) for category in categories]

    categories_dict = [category.dict() for category in categories_list]

    return categories_dict

@db_metrics(operation="get_seller_by_id")
async def get_seller_by_id(db: AsyncSession, seller_id: int):
    pass
    # result = await db.execute(select(Seller).filter(Seller.id == seller_id))
    # seller = result.scalar_one_or_none()
    # seller_id_list = SellerSchemas.from_orm(seller)

    # seller_id_dict = seller_id_list.dict()
    # print("DEBUG CATALOG FUNCTION, get_product_by_id, products_dict", seller_id_dict)
    # return seller_id_dict

# Создание нового товара
@db_metrics(operation="create_product")
async def create_product(db: AsyncSession, name: str, description: str, price: float, stock: int, category_id: int, seller_id: int):
    if price < 0 or stock < 0:
        raise HTTPException(status_code=400, detail="Price and stock must be non-negative.")
    new_product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_id=category_id,
        seller_id=seller_id
    )
    db.add(new_product)
    await db.commit()  # Сохраняем в базу данных
    await db.refresh(new_product)  # Обновляем объект с последними данными из базы

    # Явно загружаем связанные отношения для response_model
    loaded_product = await db.execute(
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.images))
        .filter(Product.id == new_product.id)
    )
    return loaded_product.scalar_one_or_none()

# Обновление продукта
@db_metrics(operation="update_product")
async def update_product(db: AsyncSession, product_id: int, name: str, description: str, price: float, stock: int):
    # Получаем продукт по ID как SQLAlchemy-модель, с жадной загрузкой отношений
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.images))
        .filter(Product.id == product_id)
    )
    product_model = result.scalar_one_or_none()

    if not product_model:
        raise HTTPException(status_code=404, detail="Product not found")

    # Проверка на отрицательные значения для цены и количества
    if price < 0 or stock < 0:
        raise HTTPException(status_code=400, detail="Price and stock must be non-negative.")
    
    # Обновление данных продукта
    product_model.name = name
    product_model.description = description
    product_model.price = price
    product_model.stock = stock

    await db.commit()
    await db.refresh(product_model)

    # Преобразуем в словарь для возврата
    product_dict = {
        "id": product_model.id,
        "name": product_model.name,
        "description": product_model.description,
        "price": product_model.price,
        "stock": product_model.stock,
        "category_id": product_model.category_id,
        "seller_id": product_model.seller_id,
        "active": product_model.active,
        "category": {"id": product_model.category.id, "name": product_model.category.name} if product_model.category else None,
        "images": []  # Возвращаем пустой список вместо None
    }

    return product_dict


# Удаление товара
@db_metrics(operation="delete_product")
async def delete_product(db: AsyncSession, product_id: int):
    # Получаем продукт по ID как SQLAlchemy-модель, с жадной загрузкой отношений
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.images))
        .filter(Product.id == product_id)
    )
    product_model = result.scalar_one_or_none()

    if not product_model:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product_model)
    await db.commit()

    return product_id # Возвращаем ID удаленного товара
