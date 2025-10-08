# Stage 1: Build the virtual environment
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install poetry
COPY ../../pyproject.toml ../../poetry.lock ./
RUN poetry install --no-root --no-dev

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /app/.venv /.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY ./player_service ./player_service
EXPOSE 8000

CMD ["uvicorn", "player_service.main:app", "--host", "0.0.0.0", "--port", "8000"]