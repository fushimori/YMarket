FROM python:3.11-slim

WORKDIR /app

COPY ./app /app
COPY ./app/tests /app/tests
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"] 