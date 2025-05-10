# catalog_service/app/db/database.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('CATALOG_DB_USER')}:{os.getenv('CATALOG_DB_PASSWORD')}"
    f"@{os.getenv('CATALOG_DB_HOST')}:{os.getenv('CATALOG_DB_PORT')}/{os.getenv('CATALOG_DB_NAME')}"
)

# Настройка асинхронного движка
engine = create_async_engine(DATABASE_URL, echo=True)

# Асинхронная фабрика сессий
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()

# Генератор сессий
async def get_db():
    async with SessionLocal() as session:
        yield session
