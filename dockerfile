FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock /usr/src/app/

RUN pip install --no-cache-dir poetry

RUN poetry install --no-dev --no-interaction --no-ansi

# may be should to remove this COPY
COPY . /usr/src/app/
