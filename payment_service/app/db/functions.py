# payment_service/app/db/functions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException
from db.models import Transaction, Refund, TransactionStatus

# Получение транзакции по ID
async def get_transaction_by_id(db: AsyncSession, transaction_id: int):
    result = await db.execute(select(Transaction).filter(Transaction.id == transaction_id))
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

# Создание новой транзакции
async def create_transaction(db: AsyncSession, order_id: int, payment_method: str, amount: float, payment_reference: str):
    transaction = Transaction(
        order_id=order_id,
        payment_method=payment_method,
        amount=amount,
        payment_reference=payment_reference,
        status=TransactionStatus.PENDING
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction

# Обновление статуса транзакции
async def update_transaction_status(db: AsyncSession, transaction_id: int, status: TransactionStatus):
    transaction = await get_transaction_by_id(db, transaction_id)
    transaction.status = status
    await db.commit()
    await db.refresh(transaction)
    return transaction


# Создание запроса на возврат
async def create_refund(db: AsyncSession, transaction_id: int, amount: float):
    transaction = await get_transaction_by_id(db, transaction_id)

    # Проверка, что сумма возврата не превышает сумму транзакции
    if amount > transaction.amount:
        raise HTTPException(status_code=400, detail="Refund amount exceeds transaction amount")
    
    refund = Refund(
        transaction_id=transaction.id,
        amount=amount,
        status=TransactionStatus.PENDING
    )
    db.add(refund)
    await db.commit()
    await db.refresh(refund)
    return refund

# Обновление статуса возврата
async def update_refund_status(db: AsyncSession, refund_id: int, status: TransactionStatus):
    result = await db.execute(select(Refund).filter(Refund.id == refund_id))
    refund = result.scalar_one_or_none()
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    refund.status = status
    await db.commit()
    await db.refresh(refund)
    return refund

# Получение всех возвратов по транзакции
async def get_refunds_by_transaction_id(db: AsyncSession, transaction_id: int):
    result = await db.execute(select(Refund).filter(Refund.transaction_id == transaction_id))
    return result.scalars().all()
