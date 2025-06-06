# auth_service/app/auth_utils.py
import hashlib
import hmac
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """Хэширует пароль с использованием SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль, сравнивая с хэшем."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(data: dict):
    """Создает JWT токен с указанным временем истечения."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
