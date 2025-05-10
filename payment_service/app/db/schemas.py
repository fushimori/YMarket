# payment_service/app/db/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

# Схемы для Transaction
class TransactionBase(BaseModel):
    order_id: int
    payment_method: str
    amount: Decimal
    status: str

class TransactionResponse(TransactionBase):
    id: int
    payment_reference: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

# Схема для создания транзакции 
class TransactionCreate(BaseModel):
    order_id: int
    payment_method: str
    amount: Decimal
    payment_reference: str  # Поле payment_reference нужно передавать при создании

# Схемы для PaymentMethod
class PaymentMethodBase(BaseModel):
    method_name: str

class PaymentMethodResponse(PaymentMethodBase):
    id: int

    class Config:
        orm_mode = True

# Схема для создания метода оплаты (идентична базовой схеме)
class PaymentMethodCreate(PaymentMethodBase):
    pass  # Все поля из PaymentMethodBase

# Схемы для Refund
class RefundBase(BaseModel):
    transaction_id: int
    amount: Decimal
    status: str

class RefundResponse(RefundBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

# Схема для создания возврата
class RefundCreate(BaseModel):
    transaction_id: int
    amount: Decimal
