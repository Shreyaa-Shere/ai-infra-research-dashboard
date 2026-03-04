FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY . .
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -e ".[dev]"

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
