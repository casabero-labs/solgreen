FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD solgreen health-check --db-url "${SOLGREEN_DATABASE_URL}" || exit 1

CMD ["sh", "-c", "solgreen deploy-schema --db-url \"${SOLGREEN_DATABASE_URL}\" && solgreen health-check --db-url \"${SOLGREEN_DATABASE_URL}\" && tail -f /dev/null"]
