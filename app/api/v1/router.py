"""
Router agregador de la API v1.

Cada nuevo grupo de endpoints (predictions, chat, detections, auth)
se registra aquí a medida que se implementa en las siguientes fases.
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth_routes,
    chat_routes,
    crop_routes,
    detection_routes,
    health_routes,
    prediction_routes,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_routes.router)
api_router.include_router(auth_routes.router)
api_router.include_router(prediction_routes.router)
api_router.include_router(detection_routes.router)
api_router.include_router(chat_routes.router)
api_router.include_router(crop_routes.router)
