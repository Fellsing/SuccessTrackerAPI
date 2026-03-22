import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

#создаем отдельный движок для ТЕСТОВОЙ базы
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    #создаем таблицы в тестовой базе перед тестом
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        #удаляем таблицы после теста, чтобы каждый раз база была чистой
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    #переопределяем зависимость get_db в приложении FastAPI
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    yield TestClient(app)
    #после теста убираем переопределение, чтобы не сломать основное приложение
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def token(client):
    user_data = {"username":"autotest", "password":"AutoPass!1"}
    client.post("/auth/signup", json=user_data)
    signin = client.post("/auth/signin", data=user_data)
    return signin.json()["access_token"]

