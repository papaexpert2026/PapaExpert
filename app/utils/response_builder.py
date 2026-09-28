"""
Helper para construir respuestas JSON consistentes en toda la API.

Formato estándar:
{ "success": bool, "data": ..., "message": str, "error_code": str | None }
"""

from typing import Any


def success_response(data: Any = None, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message, "error_code": None}


def error_response(message: str, error_code: str, data: Any = None) -> dict:
    return {"success": False, "data": data, "message": message, "error_code": error_code}
