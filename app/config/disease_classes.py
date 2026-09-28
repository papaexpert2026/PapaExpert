"""
Configuración de clases de enfermedades detectables por el modelo YOLO.

Estas clases YA SON LAS REALES, entrenadas con el dataset "potato-plants-diseases"
de Roboflow Universe (https://universe.roboflow.com/project-u0r7n/potato-plants-diseases).

IMPORTANTE: el orden y los class_id (0, 1, 2) deben coincidir EXACTAMENTE con el
campo 'names' de tu archivo data.yaml usado al entrenar. Si vuelves a entrenar
con otro dataset u otra versión, revisa data.yaml y actualiza esto si cambia el orden.

Cómo agregar un cultivo nuevo en el futuro:
Cuando tengas más de un cultivo, cambia esta estructura a un diccionario
anidado por cultivo, por ejemplo:
    DISEASE_CLASSES = {
        "papa": { 0: DiseaseInfo(...), ... },
        "tomate": { 0: DiseaseInfo(...), ... },
    }
y el YOLOService recibiría qué modelo/cultivo usar. Por ahora, con un solo
cultivo (papa), se mantiene plano para simplicidad.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DiseaseInfo:
    class_id: int
    class_name: str
    display_name: str
    description: str
    recommendation: str


DISEASE_CLASSES: dict[int, DiseaseInfo] = {
    0: DiseaseInfo(
        class_id=0,
        class_name="Potato___Early_blight",
        display_name="Tizón temprano",
        description="Enfermedad fúngica causada por Alternaria solani, que produce manchas concéntricas oscuras en las hojas.",
        recommendation="Se recomienda evaluación agronómica y posible manejo con fungicidas específicos.",
    ),
    1: DiseaseInfo(
        class_id=1,
        class_name="Potato___Late_blight",
        display_name="Tizón tardío",
        description="Enfermedad causada por Phytophthora infestans, de alta capacidad destructiva, con manchas húmedas de color marrón oscuro.",
        recommendation="Requiere atención prioritaria; se recomienda contactar a un técnico agrícola lo antes posible.",
    ),
    2: DiseaseInfo(
        class_id=2,
        class_name="Potato___healthy",
        display_name="Sana",
        description="No se detectaron signos visibles de enfermedad en la hoja.",
        recommendation="Continúa con el monitoreo regular del cultivo.",
    ),
}


def get_disease_info(class_id: int) -> DiseaseInfo:
    """
    Retorna la información de una clase de enfermedad por su class_id.
    Si el class_id no está configurado, retorna un valor genérico en vez
    de fallar, para no romper la respuesta de la API ante clases no mapeadas.
    """
    return DISEASE_CLASSES.get(
        class_id,
        DiseaseInfo(
            class_id=class_id,
            class_name=f"unknown_{class_id}",
            display_name="Desconocida",
            description="Clase detectada sin información configurada.",
            recommendation="Consulta a un técnico agrícola para una evaluación precisa.",
        ),
    )
