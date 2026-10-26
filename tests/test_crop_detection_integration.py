"""
Tests de la integración Cultivo <-> Diagnóstico (PASO 3 del plan PAPA EXPERT).
"""

from unittest.mock import AsyncMock, patch

from app.repositories.detection_repository import DetectionRepository


def _get_user_id(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()["data"]["id"]


def _create_crop(client, headers, name="Parcela San José"):
    payload = {"name": name, "variety": "Superchola", "planting_date": "2026-08-10"}
    return client.post("/api/v1/crops", json=payload, headers=headers).json()["data"]


def test_predictions_with_crop_id_from_other_user_returns_404(client, auth_headers, db_session):
    # Cultivo de un usuario random inexistente (id absurdo) -> 404, no 500.
    response = client.post(
        "/api/v1/predictions",
        files={"file": ("x.jpg", b"fake", "image/jpeg")},
        data={"crop_id": "99999"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_detection_created_directly_can_carry_crop_id(client, auth_headers, db_session):
    """
    No podemos correr YOLO real en los tests, así que probamos la asociación
    creando la detección directamente por repositorio (como hace
    PredictionService internamente) y verificando que se lea bien por la API.
    """
    user_id = _get_user_id(client, auth_headers)
    crop = _create_crop(client, auth_headers)

    detection = DetectionRepository(db_session).create(
        user_id=user_id,
        plant="papa",
        disease="Tizón tardío",
        confidence=0.94,
        image_path="uploads/test.jpg",
        crop_id=crop["id"],
    )

    response = client.get(f"/api/v1/detections/{detection.id}", headers=auth_headers)
    body = response.json()["data"]
    assert body["crop_id"] == crop["id"]
    assert body["crop_name"] == "Parcela San José"
    assert body["crop_variety"] == "Superchola"


def test_old_detection_without_crop_still_works(client, auth_headers, db_session):
    """Los diagnósticos antiguos sin cultivo (crop_id=None) no deben romperse."""
    user_id = _get_user_id(client, auth_headers)
    detection = DetectionRepository(db_session).create(
        user_id=user_id,
        plant="papa",
        disease="Sana",
        confidence=0.99,
        image_path="uploads/old.jpg",
    )

    response = client.get(f"/api/v1/detections/{detection.id}", headers=auth_headers)
    body = response.json()["data"]
    assert body["crop_id"] is None
    assert body["crop_name"] is None


def test_crop_detections_summary_endpoint(client, auth_headers, db_session):
    user_id = _get_user_id(client, auth_headers)
    crop = _create_crop(client, auth_headers)
    repo = DetectionRepository(db_session)

    repo.create(user_id=user_id, plant="papa", disease="Sana", confidence=0.9, image_path="a.jpg", crop_id=crop["id"])
    repo.create(user_id=user_id, plant="papa", disease="Tizón tardío", confidence=0.94, image_path="b.jpg", crop_id=crop["id"])

    response = client.get(f"/api/v1/crops/{crop['id']}/detections", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total"] == 2
    assert body["last_disease"] == "Tizón tardío"  # la más reciente


def test_crop_detections_summary_not_found_for_other_users_crop(client, auth_headers):
    response = client.get("/api/v1/crops/99999/detections", headers=auth_headers)
    assert response.status_code == 404


def test_chat_prompt_includes_crop_context_when_available(client, auth_headers, db_session):
    """
    Verifica que, cuando la detección tiene cultivo, el servicio de OpenAI
    reciba el nombre del cultivo y la variedad (sin llamar a OpenAI real).
    """
    user_id = _get_user_id(client, auth_headers)
    crop = _create_crop(client, auth_headers)
    detection = DetectionRepository(db_session).create(
        user_id=user_id,
        plant="papa",
        disease="Tizón tardío",
        confidence=0.94,
        image_path="uploads/test.jpg",
        crop_id=crop["id"],
    )

    session_id = client.post(
        "/api/v1/chat/sessions", json={"detection_id": detection.id}, headers=auth_headers
    ).json()["data"]["id"]

    with patch(
        "app.services.chat_service.ask_assistant",
        new=AsyncMock(return_value="Respuesta simulada."),
    ) as mocked_ask:
        client.post(
            "/api/v1/chat",
            json={"session_id": session_id, "question": "¿Qué debo hacer?"},
            headers=auth_headers,
        )

    _, kwargs = mocked_ask.call_args
    assert kwargs["crop_name"] == "Parcela San José"
    assert kwargs["crop_variety"] == "Superchola"


def test_create_crop_with_status(client, auth_headers):
    payload = {
        "name": "Lote El Rosal",
        "variety": "Capiro",
        "planting_date": "2026-01-01",
        "status": "flowering",
    }
    response = client.post("/api/v1/crops", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "flowering"
