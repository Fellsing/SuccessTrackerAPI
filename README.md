# Success Tracker API

RESTful API для отслеживания личных достижений и управления категориями успехов. Проект построен на современном стеке Python с акцентом на безопасность, типизацию и контейнеризацию.

## Стек технологий

* **Framework:** FastAPI 
* **Database:** PostgreSQL [cite: 2]
* **ORM:** SQLAlchemy 2.0
* **Migrations:** Alembic 
* **Validation:** Pydantic v2
* **Security:** JWT (OAuth2 with Password flow)
* **Dependency Management:** Poetry 
* **Containerization:** Docker & Docker Compose 

## Основные возможности

* Система аутентификации и авторизации пользователей на базе JWT.
* Управление категориями успехов с автоматической валидацией имен (запрет спецсимволов, форматирование регистра).
* CRUD операции для записи достижений с фильтрацией по владельцу.
* Валидация входящих данных на уровне схем Pydantic (обработка лишних пробелов, проверка типов и диапазонов значений).
* Глобальная обработка исключений (Exception Handling) для единообразных ответов API.
* Автоматическое выполнение миграций базы данных при запуске приложения в контейнере.
* **Экспорт данных**: Генерация отчетов в форматах CSV (с поддержкой Google Sheets) и PDF (с поддержкой кириллицы).

## Установка и запуск

### Требования
* Docker
* Docker Compose

### Запуск приложения
1. Клонируйте репозиторий:
   ```bash
   git clone [https://github.com/Fellsing/SuccessTrackerAPI.git](https://github.com/Fellsing/SuccessTrackerAPI.git)
   cd SuccessTrackerAPI
2. Создайте файл `.env` на основе примера:
   ```bash
   cp .env.example .env
3. Запустите проект через Docker Compose:
    ```bash
    docker-compose up --build
    После запуска API будет доступно по адресу: http://localhost:8000.
    Интерактивная документация Swagger UI: http://localhost:8000/docs.
4. **Шрифты для PDF**: Для корректного отображения кириллицы в PDF, убедитесь, что файл шрифта находится по пути:
   `fonts/TIMES.ttf`

### Управление базой данных
* Миграции применяются автоматически при старте контейнера app. Если необходимо выполнить команды Alembic вручную:
* Применить миграции: docker-compose exec app alembic upgrade head
* Создать новую миграцию: docker-compose exec app alembic revision --autogenerate -m "description"