"""Utilidades comunes de los handlers: validación y respuestas HTTP."""
import functools
import json
import logging
import uuid

from decimalencoder import DecimalEncoder
from todoList import TodoNotFoundError

MAX_TEXT_LENGTH = 1000

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ValidationError(Exception):
    """La petición contiene datos no válidos (HTTP 400)."""


def response(status_code, body=None):
    """Construye la respuesta en el formato que espera API Gateway."""
    result = {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
    }
    if body is not None:
        result["body"] = json.dumps(body, cls=DecimalEncoder)
    return result


def api_handler(func):
    """Convierte las excepciones de un handler en respuestas HTTP.

    Los errores inesperados se registran en CloudWatch, pero al cliente solo
    se le devuelve un mensaje genérico, sin detalles internos.
    """
    @functools.wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)
        except ValidationError as error:
            return response(400, {"message": str(error)})
        except TodoNotFoundError:
            return response(404, {"message": "Tarea no encontrada"})
        except Exception:
            logger.exception("Error inesperado al procesar la petición")
            return response(500, {"message": "Error interno del servidor"})
    return wrapper


def parse_body(event):
    """Devuelve el cuerpo JSON de la petición como diccionario."""
    try:
        data = json.loads(event.get("body") or "")
    except (TypeError, ValueError) as error:
        raise ValidationError(
            "El cuerpo de la petición debe ser un JSON válido") from error
    if not isinstance(data, dict):
        raise ValidationError(
            "El cuerpo de la petición debe ser un objeto JSON")
    return data


def get_todo_id(event):
    """Devuelve el id de la ruta /todos/{id}, que debe ser un UUID."""
    todo_id = (event.get("pathParameters") or {}).get("id")
    try:
        return str(uuid.UUID(todo_id))
    except (TypeError, ValueError, AttributeError) as error:
        raise ValidationError("El id de la tarea no es válido") from error


def validate_text(data):
    """Valida el campo 'text': obligatorio, texto y con longitud limitada."""
    text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValidationError(
            "El campo 'text' es obligatorio y debe ser un texto")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValidationError(
            f"El campo 'text' no puede superar {MAX_TEXT_LENGTH} caracteres")
    return text.strip()


def validate_checked(data):
    """Valida el campo 'checked'. Acepta true/false o "true"/"false"."""
    checked = data.get("checked")
    if isinstance(checked, bool):
        return checked
    if isinstance(checked, str) and checked.lower() in ("true", "false"):
        return checked.lower() == "true"
    raise ValidationError(
        "El campo 'checked' es obligatorio y debe ser true o false")
