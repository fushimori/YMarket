# cart_service/app/db/schemas.py
from pydantic import BaseModel
from typing import List

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItemResponse(CartItemBase):
    id: int
    class Config:
        orm_mode = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    
    class Config:
        orm_mode = True
