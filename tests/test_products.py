import pytest

PRODUCT = {"name": "Keyboard", "description": "USB", "price": 25.5, "quantity": 3}


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_products(client):
    assert client.get("/products").json() == []
    product = client.post("/products", json=PRODUCT).json()
    response = client.get("/products")
    assert response.status_code == 200
    assert response.json() == [product]


def test_create_product(client):
    response = client.post("/products", json=PRODUCT)
    assert response.status_code == 201
    assert response.json() == {"id": 1, **PRODUCT}


def test_get_product(client):
    product = client.post("/products", json=PRODUCT).json()
    response = client.get(f"/products/{product['id']}")
    assert response.status_code == 200
    assert response.json() == product


def test_delete_product(client):
    product = client.post("/products", json=PRODUCT).json()
    response = client.delete(f"/products/{product['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/products/{product['id']}").status_code == 404
    assert client.get("/products").json() == []
    assert client.post("/products", json=PRODUCT).json()["id"] > product["id"]


@pytest.mark.parametrize("method", ["get", "delete"])
def test_missing_product(client, method):
    response = getattr(client, method)("/products/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


@pytest.mark.parametrize("payload", [
    {}, {**PRODUCT, "name": "   "}, {**PRODUCT, "price": 0},
    {**PRODUCT, "price": -1}, {**PRODUCT, "price": "invalid"},
    {**PRODUCT, "quantity": -1}, {**PRODUCT, "quantity": 1.5},
    {**PRODUCT, "quantity": True}, {**PRODUCT, "unknown": 1},
    {**PRODUCT, "name": "x" * 101}, {**PRODUCT, "description": "x" * 1001},
    {**PRODUCT, "price": "NaN"}, {**PRODUCT, "price": "Infinity"},
])
def test_invalid_product(client, payload):
    assert client.post("/products", json=payload).status_code == 422
    assert client.get("/products").json() == []


@pytest.mark.parametrize("id", ["abc", "0", "-1"])
@pytest.mark.parametrize("method", ["get", "delete"])
def test_invalid_id(client, id, method):
    assert getattr(client, method)(f"/products/{id}").status_code == 422


def test_swagger(client):
    assert client.get("/docs").status_code == 200
    assert "/products" in client.get("/openapi.json").json()["paths"]
