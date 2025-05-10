# cart_service/app/db/init_db.py
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import engine, Base
from db.models import Cart, CartItem

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
