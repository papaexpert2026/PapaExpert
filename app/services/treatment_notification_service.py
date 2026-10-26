"""Envía recordatorios FCM para tratamientos guardados en Firestore."""

import logging
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, firestore, messaging
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.config import settings

logger = logging.getLogger(__name__)


def _firestore_client():
    if not firebase_admin._apps:
        credential = (
            credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            if settings.FIREBASE_SERVICE_ACCOUNT_PATH
            else None
        )
        firebase_admin.initialize_app(
            credential=credential,
            options={"projectId": settings.FIREBASE_PROJECT_ID},
        )
    return firestore.client()


def _as_utc(value) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _send_to_user(user_ref, title: str, body: str, treatment_id: str) -> bool:
    sent = False
    devices = user_ref.collection("notification_devices").stream()
    for device in devices:
        token = (device.to_dict() or {}).get("token")
        if not token:
            continue
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={"screen": "/alerts", "treatment_id": treatment_id},
            token=token,
        )
        try:
            messaging.send(message)
            sent = True
        except Exception as exc:
            if type(exc).__name__ == "UnregisteredError":
                device.reference.delete()
                continue
            logger.exception("No se pudo enviar un recordatorio FCM a un dispositivo.")
    return sent


def process_due_treatment_notifications() -> int:
    """Envía avisos vencidos y avanza las fechas sin duplicar por ciclo."""
    db = _firestore_client()
    now = datetime.now(timezone.utc)
    sent_count = 0

    for user_document in db.collection("users").stream():
        user_ref = user_document.reference
        plans = user_ref.collection("treatments").where(filter=FieldFilter("status", "==", "active")).stream()
        for plan_document in plans:
            plan = plan_document.to_dict() or {}
            plan_ref = plan_document.reference
            treatment_id = plan_document.id
            end_at = _as_utc(plan.get("end_at"))

            if end_at is not None and end_at <= now:
                if plan.get("end_notification_sent"):
                    continue
                sent = _send_to_user(
                    user_ref,
                    "Revisa tu tratamiento",
                    f"Terminó el periodo de {plan.get('treatment') or 'tratamiento'}. Revisa el cultivo y actualiza el seguimiento.",
                    treatment_id,
                )
                if sent:
                    plan_ref.update({
                        "status": "awaiting_review",
                        "end_notification_sent": True,
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    })
                    sent_count += 1
                continue

            next_at = _as_utc(plan.get("next_at"))
            if next_at is None or next_at > now:
                continue

            product_name = plan.get("product_name") or plan.get("treatment") or "tu tratamiento"
            disease_name = plan.get("disease") or "tu cultivo"
            quantity_note = ""
            product_amount = plan.get("product_amount")
            product_unit = plan.get("product_unit") or ""
            hectares = plan.get("hectares")
            water_liters = plan.get("total_water_liters")
            if product_amount is not None and hectares is not None:
                quantity_note = (
                    f" Dosis calculada: {product_amount:.2f} {product_unit}"
                    f" para {hectares:.2f} ha"
                )
                if water_liters is not None:
                    quantity_note += f" en {water_liters:.0f} L de agua"
            sent = _send_to_user(
                user_ref,
                "Hora de aplicar el tratamiento",
                f"Toca aplicar {product_name} para {disease_name}.{quantity_note}",
                treatment_id,
            )
            if not sent:
                continue

            interval_days = max(1, min(int(plan.get("interval_days") or 1), 365))
            following = next_at + timedelta(days=interval_days)
            while following <= now:
                following += timedelta(days=interval_days)
            plan_ref.update({
                "next_at": following if end_at is None or following <= end_at else None,
                "last_notification_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            sent_count += 1

    return sent_count
