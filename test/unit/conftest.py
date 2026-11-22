"""Fixtures comunes: una tabla de DynamoDB simulada con moto."""
import json

import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "todo-unit-tests"


@pytest.fixture(autouse=True)
def aws_environment(monkeypatch):
    """Credenciales ficticias para que ningún test llegue a AWS real."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("DYNAMODB_TABLE", TABLE_NAME)
    monkeypatch.setenv("ENDPOINT_OVERRIDE", "")


@pytest.fixture
def table():
    """Tabla de tareas vacía en un DynamoDB simulado."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        yield dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )


def make_event(body=None, todo_id=None):
    """Evento de API Gateway mínimo para invocar un handler."""
    if body is not None and not isinstance(body, str):
        body = json.dumps(body)
    return {
        "body": body,
        "pathParameters": {"id": todo_id} if todo_id else None,
    }
