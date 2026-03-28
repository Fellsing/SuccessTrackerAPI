import pytest
from main import app
from fastapi.testclient import TestClient


#client = TestClient(app)


def test_register_user(client):
    response = client.post("/auth/signup", json={"username":"testuserr", "password":"Testpassword1!"})
    assert response.status_code==201
    assert response.json()["message"]=="Пользователь успешно зарегистрирован"



def test_login_user(client):
    client.post("/auth/signup", json={"username":"testuserr", "password":"Testpassword1!"})
    response = client.post("/auth/signin", data={"username":"testuserr", "password":"Testpassword1!"})
    assert response.status_code==200
    assert "access_token" in response.json()
    assert response.json()["token_type"]=="bearer"



def test_failed_login_user(client):
    client.post("/auth/signup", json={"username":"testuserr", "password":"Testpassword1!"})
    response = client.post("/auth/signin", data={"username":"testuserr", "password":"FAILTestpassword1!"})
    assert response.status_code==401
    assert response.json()["detail"]=="Неверное имя пользователя или пароль"



def test_add_success(client, token):
    response = client.post("/successes/add_success", json={
  "header": "string",
  "description": "string",
  "priority": 1,
  "category_name": "string"
}, headers={"Authorization":f"Bearer {token}"})
    assert response.status_code==200
    assert response.json()["id"]==1

def test_delete_success(client, token):
    add_response = client.post("/successes/add_success", json={
  "header": "string",
  "description": "string",
  "priority": 1,
  "category_name": "string"
}, headers={"Authorization":f"Bearer {token}"})
    response = client.delete(f'/successes/delete_successes/{add_response.json()["id"]}', headers={"Authorization":f"Bearer {token}"})
    assert response.status_code==200



def test_search_success(client, token):
    add_response = client.post("/successes/add_success", json={
  "header": "string",
  "description": "string",
  "priority": 1,
  "category_name": "string"
}, headers={"Authorization":f"Bearer {token}"})
    response = client.get(f'/successes/successess/search/', params = {"search_query":add_response.json()["header"][:3]}, headers={"Authorization":f"Bearer {token}"})
    assert response.status_code==200