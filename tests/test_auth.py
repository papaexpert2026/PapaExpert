def test_register_creates_user_and_returns_token(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "nuevo@papaexpert.com", "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]


def test_register_duplicate_email_fails(client):
    payload = {"email": "dup@papaexpert.com", "password": "password123"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


def test_login_with_wrong_password_returns_401(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "user@papaexpert.com", "password": "password123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@papaexpert.com", "password": "incorrecta"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_register_with_invalid_email_returns_friendly_message(client):
    """
    Caso real reportado: un email sin punto antes del dominio (gmailcom en vez
    de gmail.com) debe devolver el mismo formato JSON consistente de la API,
    con un mensaje legible en español, no el detalle crudo de Pydantic.
    """
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "usuario@gmailcom", "password": "password123"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"
    assert "detail" not in body
