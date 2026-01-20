FROM python:3.12-slim

WORKDIR /app

COPY ./app /app

RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
