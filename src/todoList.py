"""Capa de acceso a datos: operaciones CRUD de tareas sobre DynamoDB."""
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


class TodoNotFoundError(Exception):
    """La tarea solicitada no existe."""


def get_table(dynamodb=None):
    """Devuelve la tabla indicada en la variable DYNAMODB_TABLE.

    ENDPOINT_OVERRIDE permite apuntar a DynamoDB Local durante el desarrollo.
    """
    if dynamodb is None:
        endpoint_url = os.environ.get("ENDPOINT_OVERRIDE") or None
        dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url)
    return dynamodb.Table(os.environ["DYNAMODB_TABLE"])


def _now():
    """Fecha y hora actual en UTC, formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def _is_missing(error):
    """Indica si el error se debe a que no se cumplió attribute_exists."""
    return (error.response["Error"]["Code"]
            == "ConditionalCheckFailedException")


def get_item(key, dynamodb=None):
    """Devuelve la tarea con ese id, o None si no existe."""
    result = get_table(dynamodb).get_item(Key={"id": key})
    return result.get("Item")


def get_items(dynamodb=None):
    """Devuelve todas las tareas.

    Un scan de DynamoDB devuelve como máximo 1 MB por llamada, así que se
    recorren todas las páginas.
    """
    table = get_table(dynamodb)
    response = table.scan()
    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    return items


def put_item(text, dynamodb=None):
    """Crea una tarea nueva y la devuelve."""
    timestamp = _now()
    item = {
        # uuid4 es aleatorio; uuid1 incluía la MAC del servidor y la hora
        "id": str(uuid.uuid4()),
        "text": text,
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }
    get_table(dynamodb).put_item(Item=item)
    return item


def update_item(key, text, checked, dynamodb=None):
    """Actualiza una tarea existente y devuelve su nuevo estado.

    Lanza TodoNotFoundError si la tarea no existe (sin la condición,
    DynamoDB crearía una tarea nueva con ese id).
    """
    try:
        result = get_table(dynamodb).update_item(
            Key={"id": key},
            ConditionExpression="attribute_exists(#id)",
            UpdateExpression=(
                "SET #text = :text, checked = :checked, "
                "updatedAt = :updatedAt"
            ),
            ExpressionAttributeNames={"#id": "id", "#text": "text"},
            ExpressionAttributeValues={
                ":text": text,
                ":checked": checked,
                ":updatedAt": _now(),
            },
            ReturnValues="ALL_NEW",
        )
    except ClientError as error:
        if _is_missing(error):
            raise TodoNotFoundError(key) from error
        raise
    return result["Attributes"]


def delete_item(key, dynamodb=None):
    """Borra una tarea. Lanza TodoNotFoundError si no existe."""
    try:
        get_table(dynamodb).delete_item(
            Key={"id": key},
            ConditionExpression="attribute_exists(#id)",
            ExpressionAttributeNames={"#id": "id"},
        )
    except ClientError as error:
        if _is_missing(error):
            raise TodoNotFoundError(key) from error
        raise
