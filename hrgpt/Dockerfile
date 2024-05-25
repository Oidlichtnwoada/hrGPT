FROM python:3.12.3-slim-bookworm

RUN pip install poetry==1.8.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    TZ="UTC"

WORKDIR /
COPY hrgpt hrgpt/

WORKDIR /hrgpt
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

WORKDIR /hrgpt
ENTRYPOINT [".venv/bin/python", "-m", "hrgpt.server.server"]
