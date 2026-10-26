"""
Servicio de integración con OpenAI.

Es el ÚNICO módulo del backend que importa el SDK de OpenAI y que conoce
la API Key. Ningún endpoint ni otro servicio debe llamar a OpenAI directamente.
"""

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from app.config.disease_classes import DISEASE_CLASSES
from app.core.config import settings

_client = (
    AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    if settings.OPENAI_API_KEY
    else None
)


DETECTION_SYSTEM_PROMPT_TEMPLATE = """Eres un asistente agrícola experto, especializado en ayudar a agricultores \
a entender los resultados de un sistema de visión artificial que detecta enfermedades en plantas de papa.

REGLAS QUE DEBES SEGUIR SIEMPRE:
1. Responde siempre en español, con lenguaje natural, claro y cercano a un agricultor sin formación técnica.
2. Explica los términos técnicos cuando los uses.
3. NUNCA inventes información que no conozcas con certeza.
4. NUNCA presentes la detección automática como un diagnóstico absolutamente seguro. \
Es una estimación de un modelo de visión por computadora, no una confirmación agronómica.
5. Ten en cuenta el porcentaje de confianza de la detección al formular tus respuestas: \
si la confianza es baja, comunica más incertidumbre.
6. Diferencia explícitamente entre "lo que detectó el modelo" y "lo que un ingeniero agrónomo confirmaría en campo".
7. Recomienda consultar a un técnico o ingeniero agrónomo cuando la situación lo amerite, \
especialmente ante confianza baja o síntomas severos.
8. SOBRE DOSIS DE PESTICIDAS, FUNGICIDAS O AGROQUÍMICOS:
   - Si tienes la herramienta de búsqueda web disponible y encuentras una dosis en una fuente real y \
verificable (etiqueta de un producto registrado, boletín oficial de un instituto de extensión agrícola, \
ministerio de agricultura), puedes citarla, indicando siempre la fuente y el nombre del producto exacto \
al que corresponde esa dosis.
   - Si NO tienes búsqueda web activada, o no encuentras una fuente confiable, NUNCA inventes una cifra \
de memoria. En su lugar, explica que la dosis depende del producto comercial específico y su concentración \
de ingrediente activo, y recomienda leer la etiqueta del producto o consultar a un técnico agrónomo \
certificado antes de aplicar cualquier agroquímico.
   - La dosis SIEMPRE depende del producto exacto (no solo de la enfermedad): nunca generalices una dosis \
de "fungicida" sin nombrar el producto y su fuente.
   - Si el usuario te pide OPCIONES de tratamiento, preséntalas como una lista numerada corta (2-3 \
opciones como máximo), cada una con: nombre del producto, para qué sirve, y la fuente donde verificaste \
su dosis recomendada en la etiqueta.
   - Si el usuario te da una cantidad (hectáreas, litros de agua, o número de plantas) y te pide cuánto \
aplicar en total, MUESTRA el cálculo paso a paso: (dosis indicada en la etiqueta del producto) × \
(cantidad que dio el usuario) = total. Nunca des solo el resultado final sin mostrar de dónde sale. \
Si la etiqueta da la dosis por litro de agua en vez de por hectárea (o viceversa), acláraselo al usuario \
en vez de mezclar unidades sin avisar.
9. NUNCA recomiendes un producto comercial específico que no hayas verificado en la búsqueda web; \
si lo mencionas, cita la fuente.
10. Evita cualquier afirmación que pueda ser peligrosa o llevar a un manejo incorrecto del cultivo.
11. Sé útil y práctico: prioriza consejos generales de manejo, prevención y buenas prácticas agrícolas \
(rotación de cultivos, manejo de riego, espaciado, eliminación de plantas afectadas) que no dependen de \
un producto comercial y que siempre son seguros de mencionar.
12. Deja claro cuándo una recomendación es tuya (del asistente) y cuándo un dato viene del modelo YOLO \
(la detección y su confianza); nunca presentes tus propias recomendaciones como si fueran parte de la detección.

CONTEXTO DE LA DETECCIÓN ACTUAL:
- Cultivo: {plant}
- Enfermedad detectada por el modelo: {disease}
- Confianza de la detección: {confidence:.0%}{crop_context}

Usa este contexto para responder las preguntas del usuario sin pedirle que repita esta información.
"""


GENERAL_SYSTEM_PROMPT_TEMPLATE = """Eres un asistente agrícola experto para PapaExpert, una app \
especializada en el cultivo de papa.

Esta conversación NO está asociada a ningún diagnóstico concreto: el usuario entró directamente al \
asistente desde el menú, sin analizar ninguna foto todavía.

Las enfermedades que el sistema de visión artificial de esta app puede detectar automáticamente son:
{disease_list}

REGLAS QUE DEBES SEGUIR SIEMPRE:
1. Responde siempre en español, con lenguaje natural, claro y cercano a un agricultor sin formación técnica.
2. Explica los términos técnicos cuando los uses.
3. NUNCA inventes información que no conozcas con certeza.
4. Si el usuario describe síntomas de su planta y te pregunta "qué tiene", ACLARA que tú no puedes \
analizar imágenes dentro de este chat — invítalo a usar la función "Diagnosticar cultivo" de la app \
para obtener un análisis real con el modelo YOLO. Puedes conversar sobre síntomas en términos generales, \
pero nunca presentes una opinión tuya sobre una foto que no has visto como si fuera un diagnóstico.
5. Si el usuario ya tiene un diagnóstico guardado en su historial y quiere hablar de ese caso específico, \
sugiérele abrir el chat desde esa detección en su historial — ahí el asistente ya conoce automáticamente \
la enfermedad, la confianza y el cultivo, sin que tenga que repetirlos.
6. Recomienda consultar a un técnico o ingeniero agrónomo cuando la situación lo amerite.
7. SOBRE DOSIS DE PESTICIDAS, FUNGICIDAS O AGROQUÍMICOS:
   - Si tienes búsqueda web disponible y encuentras una dosis en una fuente real y verificable (etiqueta \
de un producto registrado, boletín oficial de extensión agrícola), puedes citarla con su fuente y el \
nombre exacto del producto.
   - Si no tienes búsqueda web o no encuentras una fuente confiable, NUNCA inventes una cifra de memoria: \
explica que la dosis depende del producto comercial y su concentración, y recomienda leer la etiqueta o \
consultar a un técnico.
   - Si el usuario te pide opciones de tratamiento, preséntalas como una lista numerada corta (2-3), cada \
una con el nombre del producto y la fuente donde verificaste su dosis.
   - Si te da una cantidad (hectáreas, litros de agua, número de plantas) y pide el total a aplicar, \
muestra el cálculo paso a paso (dosis de la etiqueta × cantidad = total), nunca solo el resultado.
8. NUNCA recomiendes un producto comercial que no hayas verificado en la búsqueda web; si lo mencionas, \
cita la fuente.
9. Sé útil y práctico: prioriza consejos generales de manejo, prevención y buenas prácticas agrícolas.
"""


def _general_disease_list() -> str:
    """
    Arma la lista de enfermedades dinámicamente desde disease_classes.py:
    si agregas una enfermedad nueva ahí (al reentrenar YOLO), aparece aquí
    automáticamente, sin tocar este archivo.
    """
    names = sorted(
        {info.display_name for info in DISEASE_CLASSES.values() if info.display_name.strip().lower() != "sana"}
    )
    return "\n".join(f"- {name}" for name in names) if names else "- (sin clases configuradas todavía)"


def build_system_prompt(
    plant: str | None,
    disease: str | None,
    confidence: float | None,
    crop_name: str | None = None,
    crop_variety: str | None = None,
) -> dict:
    """
    disease=None significa conversación GENERAL (sin detección asociada):
    se usa un prompt distinto que no asume ningún diagnóstico concreto.
    """
    if disease is None:
        content = GENERAL_SYSTEM_PROMPT_TEMPLATE.format(disease_list=_general_disease_list())
        return {"role": "system", "content": content}

    crop_lines = []
    if crop_name:
        crop_lines.append(f"- Parcela/cultivo: {crop_name}")
    if crop_variety:
        crop_lines.append(f"- Variedad de papa: {crop_variety}")
    crop_context = ("\n" + "\n".join(crop_lines)) if crop_lines else ""

    content = DETECTION_SYSTEM_PROMPT_TEMPLATE.format(
        plant=plant, disease=disease, confidence=confidence, crop_context=crop_context
    )
    return {"role": "system", "content": content}


class OpenAIServiceError(Exception):
    """Error genérico al comunicarse con OpenAI, para que el caller lo traduzca a HTTP."""


def _get_client() -> AsyncOpenAI:
    if _client is None:
        raise OpenAIServiceError("El servicio de IA no tiene una API key configurada.")
    return _client


RESEARCH_PROMPT_TEMPLATE = """Eres un asistente agrícola. Busca en internet información actual y confiable \
sobre la siguiente enfermedad de la papa (patata) y resume lo más relevante para un agricultor:

Enfermedad: {disease}

Tu resumen debe:
- Estar en español, en lenguaje claro para un agricultor sin formación técnica.
- Tener entre 3 y 6 oraciones.
- Mencionar causas, síntomas y manejo general (sin inventar dosis de químicos ni recomendar productos específicos).
- Basarse en fuentes reales encontradas en tu búsqueda, no en tu conocimiento previo sin verificar.
"""


def _extract_web_search_output(response) -> tuple[str, list[dict]]:
    """
    Extrae el texto final y las fuentes citadas de una respuesta de la
    Responses API que usó la herramienta web_search.

    Se implementa de forma defensiva (getattr con default) porque la forma
    exacta de los objetos del SDK puede variar entre versiones menores.
    """
    content = getattr(response, "output_text", "") or ""

    sources: list[dict] = []
    seen_urls: set[str] = set()

    for item in getattr(response, "output", None) or []:
        if getattr(item, "type", None) != "message":
            continue
        for part in getattr(item, "content", None) or []:
            for annotation in getattr(part, "annotations", None) or []:
                if getattr(annotation, "type", None) != "url_citation":
                    continue
                url = getattr(annotation, "url", None)
                title = getattr(annotation, "title", None) or url
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    sources.append({"title": title, "url": url})

    return content.strip(), sources


async def research_disease(plant: str, disease: str) -> tuple[str, list[dict]]:
    """
    Busca en internet información actualizada sobre una enfermedad detectada.
    Retorna (resumen_en_texto, lista_de_fuentes).
    """
    try:
        response = await _get_client().responses.create(
            model=settings.OPENAI_MODEL,
            tools=[{"type": "web_search"}],
            input=RESEARCH_PROMPT_TEMPLATE.format(disease=f"{disease} en plantas de {plant}"),
        )
    except RateLimitError as exc:
        raise OpenAIServiceError("Se alcanzó el límite de uso del servicio de IA. Intenta nuevamente en unos minutos.") from exc
    except APIConnectionError as exc:
        raise OpenAIServiceError("No se pudo conectar con el servicio de inteligencia artificial.") from exc
    except APIError as exc:
        raise OpenAIServiceError("El servicio de inteligencia artificial no está disponible en este momento.") from exc

    content, sources = _extract_web_search_output(response)
    if not content:
        raise OpenAIServiceError("No se pudo generar un resumen de investigación en este momento.")
    return content, sources


async def ask_assistant_with_web_search(
    plant: str | None,
    disease: str | None,
    confidence: float | None,
    question: str,
    history: list[dict],
    crop_name: str | None = None,
    crop_variety: str | None = None,
) -> tuple[str, list[dict]]:
    """
    Igual que ask_assistant, pero permite que el modelo busque en internet
    si lo considera necesario (por ejemplo, para citar una dosis real de un
    producto en vez de inventarla). Retorna (respuesta, fuentes_citadas).
    """
    system_message = build_system_prompt(plant, disease, confidence, crop_name, crop_variety)

    # La Responses API recibe el historial como una lista de turnos con
    # 'role' y 'content' de texto simple, igual que Chat Completions.
    conversation_input = [system_message] + history + [{"role": "user", "content": question}]

    try:
        response = await _get_client().responses.create(
            model=settings.OPENAI_MODEL,
            tools=[{"type": "web_search"}],
            input=conversation_input,
        )
    except RateLimitError as exc:
        raise OpenAIServiceError("Se alcanzó el límite de uso del servicio de IA. Intenta nuevamente en unos minutos.") from exc
    except APIConnectionError as exc:
        raise OpenAIServiceError("No se pudo conectar con el servicio de inteligencia artificial.") from exc
    except APIError as exc:
        raise OpenAIServiceError("El servicio de inteligencia artificial no está disponible en este momento.") from exc

    content, sources = _extract_web_search_output(response)
    if not content:
        raise OpenAIServiceError("El asistente no generó una respuesta. Intenta reformular tu pregunta.")
    return content, sources


async def ask_assistant(
    plant: str | None,
    disease: str | None,
    confidence: float | None,
    question: str,
    history: list[dict],
    crop_name: str | None = None,
    crop_variety: str | None = None,
) -> str:
    """
    Envía la pregunta del usuario a OpenAI junto con el contexto de la
    detección (si la hay) y el historial de la conversación, y retorna la
    respuesta en texto.

    history: lista de dicts [{"role": "user"|"assistant", "content": str}, ...]
    """
    system_message = build_system_prompt(plant, disease, confidence, crop_name, crop_variety)
    messages = [system_message] + history + [{"role": "user", "content": question}]

    try:
        response = await _get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=600,
        )
    except RateLimitError as exc:
        raise OpenAIServiceError("Se alcanzó el límite de uso del servicio de IA. Intenta nuevamente en unos minutos.") from exc
    except APIConnectionError as exc:
        raise OpenAIServiceError("No se pudo conectar con el servicio de inteligencia artificial.") from exc
    except APIError as exc:
        raise OpenAIServiceError("El servicio de inteligencia artificial no está disponible en este momento.") from exc

    answer = response.choices[0].message.content
    if not answer:
        raise OpenAIServiceError("El asistente no generó una respuesta. Intenta reformular tu pregunta.")
    return answer.strip()
