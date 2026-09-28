from unittest.mock import AsyncMock, patch

from app.repositories.detection_repository import DetectionRepository


def _get_user_id(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()["data"]["id"]


def _create_detection(db_session, user_id):
    return DetectionRepository(db_session).create(
        user_id=user_id,
        plant="papa",
        disease="Tizón tardío",
        confidence=0.94,
        image_path="uploads/test.jpg",
    )


def test_create_chat_session_for_nonexistent_detection_returns_404(client, auth_headers):
    response = client.post("/api/v1/chat/sessions", json={"detection_id": 9999}, headers=auth_headers)
    assert response.status_code == 404


def test_full_chat_flow_uses_detection_context_automatically(client, auth_headers, db_session):
    user_id = _get_user_id(client, auth_headers)
    detection = _create_detection(db_session, user_id)

    session_resp = client.post(
        "/api/v1/chat/sessions", json={"detection_id": detection.id}, headers=auth_headers
    )
    assert session_resp.status_code == 200
    session_id = session_resp.json()["data"]["id"]

    with patch(
        "app.services.chat_service.ask_assistant",
        new=AsyncMock(return_value="Respuesta simulada del asistente."),
    ) as mocked_ask:
        chat_resp = client.post(
            "/api/v1/chat",
            json={"session_id": session_id, "question": "¿Cómo puedo controlarlo?"},
            headers=auth_headers,
        )

    assert chat_resp.status_code == 200
    body = chat_resp.json()
    assert body["data"]["answer"] == "Respuesta simulada del asistente."

    # Verificamos que el servicio recibió la enfermedad detectada automáticamente,
    # sin que el usuario la haya escrito en su pregunta.
    _, kwargs = mocked_ask.call_args
    assert kwargs["disease"] == "Tizón tardío"
    assert kwargs["plant"] == "papa"


def test_chat_with_openai_error_returns_503(client, auth_headers, db_session):
    from app.services.openai_service import OpenAIServiceError

    user_id = _get_user_id(client, auth_headers)
    detection = _create_detection(db_session, user_id)

    session_id = client.post(
        "/api/v1/chat/sessions", json={"detection_id": detection.id}, headers=auth_headers
    ).json()["data"]["id"]

    with patch(
        "app.services.chat_service.ask_assistant",
        new=AsyncMock(side_effect=OpenAIServiceError("El servicio de inteligencia artificial no está disponible.")),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"session_id": session_id, "question": "¿Es grave?"},
            headers=auth_headers,
        )

    assert response.status_code == 503
