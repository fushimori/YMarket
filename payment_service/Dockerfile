# Используем официальный образ Python
FROM python:3.10-slim


WORKDIR /app

COPY ./app /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Запуск FastAPI приложения через Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
