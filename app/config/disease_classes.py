"""
Configuración de clases de enfermedades detectables por el modelo YOLO.

Este archivo debe coincidir EXACTAMENTE con las clases y su orden
definidos en el campo 'names' del data.yaml utilizado para entrenar
el modelo YOLO.

Clases esperadas:
- oidio
- punta_morada
- risotonia
- sana
- tizon_tardio
- tizon_temprano

IMPORTANTE:
Verifica los class_id con el archivo data.yaml de tu modelo.
Si utilizas otro modelo o dataset, actualiza esta configuración.
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
    2: DiseaseInfo(
        class_id=2,
        class_name="oidio",
        display_name="Oídio",
        description=(
            "Enfermedad asociada a hongos que puede manifestarse como "
            "un recubrimiento blanquecino o pulverulento sobre la superficie "
            "de las hojas. Los síntomas deben confirmarse mediante "
            "una evaluación de la planta."
        ),
        recommendation=(
            "Revisa las hojas afectadas y vigila la propagación de los "
            "síntomas. Consulta a un técnico agrícola para confirmar "
            "el diagnóstico y determinar el tratamiento apropiado."
        ),
    ),

    3: DiseaseInfo(
        class_id=3,
        class_name="punta_morada",
        display_name="Punta morada",
        description=(
            "Problema fitosanitario de la papa que puede producir "
            "coloración morada en las hojas superiores, enrollamiento "
            "y alteraciones en el crecimiento. Puede estar relacionado "
            "con fitoplasmas transmitidos por insectos vectores; "
            "los síntomas visuales por sí solos no confirman la causa."
        ),
        recommendation=(
            "Inspecciona las plantas afectadas y revisa la presencia "
            "de insectos vectores. Solicita una evaluación agronómica "
            "para confirmar la causa y recibir recomendaciones de manejo."
        ),
    ),

    4: DiseaseInfo(
        class_id=4,
        class_name="rizoctonia",
        display_name="Rizoctoniasis",
        description=(
            "Enfermedad causada generalmente por el hongo Rhizoctonia solani. "
            "Puede provocar lesiones en tallos y brotes, problemas de "
            "emergencia y esclerocios oscuros sobre los tubérculos. "
            "Los síntomas dependen de la parte de la planta afectada."
        ),
        recommendation=(
            "Inspecciona tallos, brotes y tubérculos. Consulta a un técnico "
            "agrícola para confirmar la enfermedad y evaluar medidas "
            "de manejo, incluida la selección de semilla sana."
        ),
    ),

    5: DiseaseInfo(
        class_id=5,
        class_name="sana",
        display_name="Sana",
        description=(
            "El modelo clasifica la muestra como una planta sana, "
            "sin identificar los síntomas correspondientes a las otras "
            "clases entrenadas. Esto no garantiza que la planta esté "
            "libre de todas las enfermedades."
        ),
        recommendation=(
            "Continúa con el monitoreo regular del cultivo, mantén "
            "buenas prácticas agrícolas y revisa periódicamente "
            "las hojas, los tallos y los tubérculos."
        ),
    ),

    0: DiseaseInfo(
        class_id=0,
        class_name="tizon_tardio",
        display_name="Tizón tardío",
        description=(
            "Enfermedad causada por Phytophthora infestans, capaz de "
            "propagarse rápidamente en condiciones favorables. Puede "
            "producir lesiones oscuras y húmedas en las hojas, "
            "a veces acompañadas de crecimiento blanquecino en el envés."
        ),
        recommendation=(
            "Inspecciona el cultivo y solicita asistencia técnica "
            "lo antes posible si sospechas de tizón tardío. Evita "
            "trasladar material vegetal posiblemente infectado y "
            "aplica medidas de control únicamente con orientación técnica."
        ),
    ),

    1: DiseaseInfo(
        class_id=1,
        class_name="tizon_temprano",
        display_name="Tizón temprano",
        description=(
            "Enfermedad generalmente causada por Alternaria solani. "
            "Puede producir manchas oscuras en las hojas, frecuentemente "
            "con anillos concéntricos y amarillamiento alrededor "
            "de las lesiones."
        ),
        recommendation=(
            "Retira los restos vegetales enfermos cuando corresponda, "
            "evita condiciones que favorezcan la humedad prolongada "
            "del follaje y consulta a un técnico agrícola para definir "
            "las medidas de manejo adecuadas."
        ),
    ),
}


def get_disease_info(class_id: int) -> DiseaseInfo:
    """
    Retorna la información asociada al class_id detectado por YOLO.

    Si la clase no está configurada, devuelve información genérica
    para evitar que la API falle por un identificador desconocido.
    """
    return DISEASE_CLASSES.get(
        class_id,
        DiseaseInfo(
            class_id=class_id,
            class_name=f"unknown_{class_id}",
            display_name="Desconocida",
            description=(
                "El modelo detectó una clase que no está configurada "
                "en el catálogo de enfermedades."
            ),
            recommendation=(
                "Verifica el orden de clases del modelo y consulta "
                "a un técnico agrícola para evaluar la muestra."
            ),
        ),
    )
