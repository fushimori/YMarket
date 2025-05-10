# catalog_service/app/db/init_db.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.database import engine, Base
from db.models import Product, Category, Seller, ProductImage, Review, Question, RelatedProduct

async def init_db():
    async with engine.begin() as conn:
        # Создание всех таблиц
        await conn.run_sync(Base.metadata.create_all)

