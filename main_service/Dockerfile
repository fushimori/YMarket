FROM python:3.10-slim

WORKDIR /app

COPY ./app /app
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
