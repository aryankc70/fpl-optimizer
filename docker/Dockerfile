FROM python:3.11-slim

WORKDIR /app

# System deps needed for psycopg2 and LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY models/ ./models/
COPY scripts/ ./scripts/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "fpl_optimizer.api.main:app", "--host", "0.0.0.0", "--port", "8000"]