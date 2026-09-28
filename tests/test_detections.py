from app.repositories.detection_repository import DetectionRepository


def _get_user_id(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()["data"]["id"]


def test_list_detections_empty_by_default(client, auth_headers):
    response = client.get("/api/v1/detections", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 0


def test_list_detections_returns_created_detection(client, auth_headers, db_session):
    user_id = _get_user_id(client, auth_headers)
    DetectionRepository(db_session).create(
        user_id=user_id,
        plant="papa",
        disease="Tizón tardío",
        confidence=0.94,
        image_path="uploads/test.jpg",
    )

    response = client.get("/api/v1/detections", headers=auth_headers)
    body = response.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["disease"] == "Tizón tardío"


def test_get_detection_not_found_returns_404(client, auth_headers):
    response = client.get("/api/v1/detections/9999", headers=auth_headers)
    assert response.status_code == 404


def test_predictions_without_auth_returns_401(client):
    response = client.post("/api/v1/predictions", files={"file": ("x.jpg", b"fake", "image/jpeg")})
    assert response.status_code == 401


def test_predictions_rejects_invalid_file_type(client, auth_headers):
    response = client.post(
        "/api/v1/predictions",
        files={"file": ("archivo.txt", b"no es una imagen", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 422
