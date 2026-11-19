FROM python:3.12-slim

ARG CACHEBUST=5

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir bcrypt==4.1.3 && pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
