from pathlib import Path

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from app.core.config import settings


def _init() -> None:
    if not firebase_admin._apps:
        service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
        cred = (
            credentials.Certificate(service_account_path)
            if service_account_path and Path(service_account_path).is_file()
            else None
        )
        firebase_admin.initialize_app(
            credential=cred,
            options={"projectId": settings.FIREBASE_PROJECT_ID},
        )


def verify_firebase_token(id_token: str) -> dict:
    _init()
    return firebase_auth.verify_id_token(id_token)
