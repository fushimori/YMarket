# payment_service/app/main.py
import random
import time
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.schemas import (
    TransactionCreate,
    TransactionResponse,
    RefundCreate,
    RefundResponse,
)
from typing import List, AsyncGenerator
from db.functions import (
    create_transaction,
    get_transaction_by_id,
    update_transaction_status,
    create_refund,
    update_refund_status,
    get_refunds_by_transaction_id,
)
from db.init_db import init_db
from db.models import TransactionStatus

# Инициализация базы данных
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Мок-функция для имитации оплаты
async def mock_payment_processing(transaction: TransactionCreate) -> bool:
    """
    Мок-функция для имитации процесса оплаты.
    Возвращает True если оплата успешна, False если неудачна.
    """
    # time.sleep(2)  # Имитация задержки при обработке транзакции
    # return random.choice([True, False])  # Случайный успех или неудача
    return True

@app.post("/transactions/", response_model=TransactionResponse)
async def create_transaction_endpoint(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создание новой транзакции.
    """
    new_transaction = await create_transaction(
        db=db,
        order_id=transaction.order_id,
        payment_method=transaction.payment_method,
        amount=transaction.amount,
        payment_reference=transaction.payment_reference
    )
    
    # Используем мок-функцию для имитации успешной или неуспешной оплаты
    payment_successful = await mock_payment_processing(transaction)
    
    # Обновляем статус транзакции в базе данных в зависимости от результата
    if payment_successful:
        await update_transaction_status(db, new_transaction.id, TransactionStatus.COMPLETED)
        new_transaction.status = TransactionStatus.COMPLETED
    else:
        await update_transaction_status(db, new_transaction.id, TransactionStatus.FAILED)
        new_transaction.status = TransactionStatus.FAILED
    
    # Возвращаем информацию о транзакции с обновленным статусом
    return new_transaction

@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_endpoint(
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение транзакции по ID.
    """
    return await get_transaction_by_id(db, transaction_id)

@app.patch("/transactions/{transaction_id}/status", response_model=TransactionResponse)
async def update_transaction_status_endpoint(
    transaction_id: int,
    status: TransactionStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление статуса транзакции.
    """
    return await update_transaction_status(db, transaction_id, status)


@app.post("/refunds/", response_model=RefundResponse)
async def create_refund_endpoint(
    refund: RefundCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создание запроса на возврат.
    """
    return await create_refund(
        db=db,
        transaction_id=refund.transaction_id,
        amount=refund.amount
    )

@app.get("/refunds/{transaction_id}", response_model=List[RefundResponse])
async def get_refunds_by_transaction_id_endpoint(
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение всех возвратов по ID транзакции.
    """
    return await get_refunds_by_transaction_id(db, transaction_id)

@app.patch("/refunds/{refund_id}/status", response_model=RefundResponse)
async def update_refund_status_endpoint(
    refund_id: int,
    status: TransactionStatus,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление статуса возврата.
    """
    return await update_refund_status(db, refund_id, status)
