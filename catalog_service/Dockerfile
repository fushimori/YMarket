# Используем официальный образ Python
FROM python:3.10-slim


WORKDIR /app

COPY ./app /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# # Открываем порт 8003
# EXPOSE 8000

# Запуск FastAPI приложения через Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
