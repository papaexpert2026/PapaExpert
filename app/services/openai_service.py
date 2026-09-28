"""
Servicio de integración con OpenAI.

Es el ÚNICO módulo del backend que importa el SDK de OpenAI y que conoce
la API Key. Ningún endpoint ni otro servicio debe llamar a OpenAI directamente.
"""

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from app.core.config import settings

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


SYSTEM_PROMPT_TEMPLATE = """Eres un asistente agrícola experto, especializado en ayudar a agricultores \
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
8. NUNCA inventes dosis específicas de pesticidas, fungicidas o agroquímicos.
9. NUNCA recomiendes productos comerciales específicos no verificados.
10. Evita cualquier afirmación que pueda ser peligrosa o llevar a un manejo incorrecto del cultivo.
11. Sé útil y práctico: prioriza consejos generales de manejo, prevención y buenas prácticas agrícolas.

CONTEXTO DE LA DETECCIÓN ACTUAL:
- Cultivo: {plant}
- Enfermedad detectada por el modelo: {disease}
- Confianza de la detección: {confidence:.0%}

Usa este contexto para responder las preguntas del usuario sin pedirle que repita esta información.
"""


def build_system_prompt(plant: str, disease: str, confidence: float) -> dict:
    content = SYSTEM_PROMPT_TEMPLATE.format(plant=plant, disease=disease, confidence=confidence)
    return {"role": "system", "content": content}


class OpenAIServiceError(Exception):
    """Error genérico al comunicarse con OpenAI, para que el caller lo traduzca a HTTP."""


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
        response = await _client.responses.create(
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
    plant: str,
    disease: str,
    confidence: float,
    question: str,
    history: list[dict],
) -> tuple[str, list[dict]]:
    """
    Igual que ask_assistant, pero permite que el modelo busque en internet
    si lo considera necesario para responder la pregunta. Retorna
    (respuesta_en_texto, lista_de_fuentes_citadas).
    """
    system_message = build_system_prompt(plant, disease, confidence)

    # La Responses API recibe el historial como una lista de turnos con
    # 'role' y 'content' de texto simple, igual que Chat Completions.
    conversation_input = [system_message] + history + [{"role": "user", "content": question}]

    try:
        response = await _client.responses.create(
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
    plant: str,
    disease: str,
    confidence: float,
    question: str,
    history: list[dict],
) -> str:
    """
    Envía la pregunta del usuario a OpenAI junto con el contexto de la
    detección y el historial de la conversación, y retorna la respuesta en texto.

    history: lista de dicts [{"role": "user"|"assistant", "content": str}, ...]
    """
    system_message = build_system_prompt(plant, disease, confidence)
    messages = [system_message] + history + [{"role": "user", "content": question}]

    try:
        response = await _client.chat.completions.create(
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
