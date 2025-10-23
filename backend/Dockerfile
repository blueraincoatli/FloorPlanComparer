# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.5.0 AS builder

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock backend/

RUN uv sync --project backend --frozen --no-dev


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/backend/.venv $VIRTUAL_ENV
COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
