FROM python:3.14.2

WORKDIR /app

#установка Poetry
RUN pip install --no-cache-dir poetry

RUN poetry config virtualenvs.create false

#копирование зависимостей
COPY pyproject.toml poetry.lock* ./

#установка зависимости без библиотек для тестов (--only main)
RUN poetry install --no-interaction --no-ansi --only main --no-root

#копирование всего остального кода
COPY . .

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]