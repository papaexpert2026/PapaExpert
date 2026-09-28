from unittest.mock import AsyncMock, patch

from app.repositories.detection_repository import DetectionRepository


def _get_user_id(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()["data"]["id"]


def _create_detection(db_session, user_id, disease="Tizón tardío"):
    return DetectionRepository(db_session).create(
        user_id=user_id,
        plant="papa",
        disease=disease,
        confidence=0.94,
        image_path="uploads/test.jpg",
    )


def test_research_not_found_detection_returns_404(client, auth_headers):
    response = client.get("/api/v1/detections/9999/research", headers=auth_headers)
    assert response.status_code == 404


def test_research_calls_openai_and_caches_result(client, auth_headers, db_session):
    user_id = _get_user_id(client, auth_headers)
    detection = _create_detection(db_session, user_id)

    fake_result = (
        "El tizón tardío es causado por Phytophthora infestans...",
        [{"title": "Guía FAO", "url": "https://fao.org/tizon-tardio"}],
    )

    with patch(
        "app.services.research_service.research_disease",
        new=AsyncMock(return_value=fake_result),
    ) as mocked_research:
        response = client.get(f"/api/v1/detections/{detection.id}/research", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["from_cache"] is False
    assert body["sources"][0]["url"] == "https://fao.org/tizon-tardio"
    mocked_research.assert_awaited_once()

    # Segunda llamada: debe venir de la caché, SIN volver a llamar a OpenAI.
    with patch(
        "app.services.research_service.research_disease",
        new=AsyncMock(return_value=fake_result),
    ) as mocked_research_second_call:
        response2 = client.get(f"/api/v1/detections/{detection.id}/research", headers=auth_headers)

    assert response2.status_code == 200
    assert response2.json()["data"]["from_cache"] is True
    mocked_research_second_call.assert_not_awaited()


def test_chat_with_web_search_returns_sources(client, auth_headers, db_session):
    user_id = _get_user_id(client, auth_headers)
    detection = _create_detection(db_session, user_id)

    session_id = client.post(
        "/api/v1/chat/sessions", json={"detection_id": detection.id}, headers=auth_headers
    ).json()["data"]["id"]

    fake_answer = (
        "Según fuentes recientes, el tizón tardío se maneja con...",
        [{"title": "INIA", "url": "https://inia.cl/tizon"}],
    )

    with patch(
        "app.services.chat_service.ask_assistant_with_web_search",
        new=AsyncMock(return_value=fake_answer),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"session_id": session_id, "question": "¿Hay novedades sobre esta enfermedad?", "use_web_search": True},
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["sources"][0]["url"] == "https://inia.cl/tizon"

    # El mensaje guardado en el historial debe conservar las fuentes.
    messages = client.get(
        f"/api/v1/chat/sessions/{session_id}/messages", headers=auth_headers
    ).json()["data"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    assert assistant_messages[-1]["sources"][0]["url"] == "https://inia.cl/tizon"


def test_chat_without_web_search_has_no_sources(client, auth_headers, db_session):
    user_id = _get_user_id(client, auth_headers)
    detection = _create_detection(db_session, user_id)

    session_id = client.post(
        "/api/v1/chat/sessions", json={"detection_id": detection.id}, headers=auth_headers
    ).json()["data"]["id"]

    with patch(
        "app.services.chat_service.ask_assistant",
        new=AsyncMock(return_value="Respuesta normal sin búsqueda web."),
    ):
        response = client.post(
            "/api/v1/chat",
            json={"session_id": session_id, "question": "¿Cómo la controlo?"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json()["data"]["sources"] is None
