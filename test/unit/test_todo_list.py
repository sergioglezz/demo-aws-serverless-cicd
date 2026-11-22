"""Tests de la capa de datos (todoList) contra un DynamoDB simulado."""
import uuid

import pytest
from botocore.exceptions import ClientError

import todoList
from conftest import TABLE_NAME

TEXT = "Aprender DevOps y Cloud en la UNIR"


def test_get_table_usa_la_tabla_configurada(table):
    assert todoList.get_table().name == TABLE_NAME


def test_get_table_respeta_endpoint_override(monkeypatch):
    llamadas = {}

    class FakeResource:
        def Table(self, name):
            return name

    def fake_resource(service, endpoint_url=None):
        llamadas["endpoint_url"] = endpoint_url
        return FakeResource()

    monkeypatch.setenv("ENDPOINT_OVERRIDE", "http://dynamodb:8000")
    monkeypatch.setattr(todoList.boto3, "resource", fake_resource)

    assert todoList.get_table() == TABLE_NAME
    assert llamadas["endpoint_url"] == "http://dynamodb:8000"


def test_put_item_crea_la_tarea(table):
    item = todoList.put_item(TEXT)

    assert item["text"] == TEXT
    assert item["checked"] is False
    assert item["createdAt"] == item["updatedAt"]
    # El id es un UUID aleatorio (versión 4), no basado en la MAC
    assert uuid.UUID(item["id"]).version == 4
    assert table.get_item(Key={"id": item["id"]})["Item"] == item


def test_get_item_devuelve_la_tarea(table):
    item = todoList.put_item(TEXT)
    assert todoList.get_item(item["id"]) == item


def test_get_item_devuelve_none_si_no_existe(table):
    assert todoList.get_item(str(uuid.uuid4())) is None


def test_get_items_lista_todas_las_tareas(table):
    textos = {"uno", "dos", "tres"}
    for texto in textos:
        todoList.put_item(texto)

    assert {item["text"] for item in todoList.get_items()} == textos


def test_get_items_recorre_todas_las_paginas():
    class FakeTable:
        def __init__(self):
            self.llamadas = []

        def scan(self, **kwargs):
            self.llamadas.append(kwargs)
            if not kwargs:
                return {"Items": [{"id": "1"}],
                        "LastEvaluatedKey": {"id": "1"}}
            return {"Items": [{"id": "2"}]}

    fake_table = FakeTable()

    class FakeDynamo:
        def Table(self, name):
            return fake_table

    items = todoList.get_items(FakeDynamo())

    assert items == [{"id": "1"}, {"id": "2"}]
    assert fake_table.llamadas[1] == {"ExclusiveStartKey": {"id": "1"}}


def test_update_item_modifica_la_tarea(table):
    item = todoList.put_item(TEXT)

    actualizado = todoList.update_item(item["id"], "Nuevo texto", True)

    assert actualizado["text"] == "Nuevo texto"
    assert actualizado["checked"] is True
    assert actualizado["createdAt"] == item["createdAt"]


def test_update_item_no_crea_tareas_nuevas(table):
    with pytest.raises(todoList.TodoNotFoundError):
        todoList.update_item(str(uuid.uuid4()), "texto", False)
    assert todoList.get_items() == []


def test_delete_item_borra_la_tarea(table):
    item = todoList.put_item(TEXT)

    todoList.delete_item(item["id"])

    assert todoList.get_item(item["id"]) is None


def test_delete_item_falla_si_no_existe(table):
    with pytest.raises(todoList.TodoNotFoundError):
        todoList.delete_item(str(uuid.uuid4()))


@pytest.mark.parametrize("operacion", ["update_item", "delete_item"])
def test_otros_errores_de_dynamodb_se_propagan(operacion):
    error = ClientError(
        {"Error": {"Code": "ProvisionedThroughputExceededException",
                   "Message": "Demasiadas peticiones"}},
        operacion)

    class FailingTable:
        def update_item(self, **kwargs):
            raise error

        def delete_item(self, **kwargs):
            raise error

    class FakeDynamo:
        def Table(self, name):
            return FailingTable()

    args = ("id", "texto", False) if operacion == "update_item" else ("id",)
    with pytest.raises(ClientError):
        getattr(todoList, operacion)(*args, dynamodb=FakeDynamo())
