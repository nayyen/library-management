FROM python:3.12-slim

WORKDIR /app

# psycopg[binary] bundles its own libpq — no system deps needed
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy application code (layer cache: code changes won't re-run pip install)
COPY app/ ./app/
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
