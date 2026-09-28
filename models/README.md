# Modelo YOLO

Coloca aquí tu modelo entrenado con el nombre exacto:

    best.pt

Ruta completa esperada (configurable en `.env` vía `YOLO_MODEL_PATH`):

    backend/models/best.pt

Este archivo NO se sube a Git (ver `.gitignore`) porque suele pesar
varias decenas o cientos de MB.

Una vez que lo coloques aquí, actualiza `backend/app/config/disease_classes.py`
con las clases REALES con las que entrenaste el modelo (deben coincidir en
orden e índice con las clases usadas en el entrenamiento de YOLO).
