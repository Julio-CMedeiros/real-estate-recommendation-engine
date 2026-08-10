FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY recommendation_engine ./recommendation_engine
COPY api ./api
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
