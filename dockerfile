FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock /usr/src/app/

RUN pip install --no-cache-dir poetry

RUN poetry install --no-dev --no-interaction --no-ansi

# may be should to remove this COPY
COPY . /usr/src/app/
