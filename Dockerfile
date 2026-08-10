FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY recommendation_engine ./recommendation_engine
COPY api ./api

RUN pip install --no-cache-dir .

RUN mkdir -p /data

ENV REC_ENGINE_DB_PATH=/data/demo.db

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
