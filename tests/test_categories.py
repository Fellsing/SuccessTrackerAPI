def test_add_category(client, token):
    response = client.post(
        "/categories/categories",
        json={"category_name": "спорт"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["category_name"] == "Спорт"


def test_get_categories(client, token):
    client.post(
        "/categories/categories",
        json={"category_name": "спорт"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/categories/categories",
        json={"category_name": "учеба"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/categories/categories_list", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()[0]["category_name"] == "Спорт"
    assert response.json()[1]["category_name"] == "Учеба"



def test_add_category_invalid_symbols(client, token):
    response = client.post("/categories/categories", json={"category_name":"!!!#!#!#!#jfkfgdk"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code==422
