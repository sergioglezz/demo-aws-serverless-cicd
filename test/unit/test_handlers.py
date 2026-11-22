"""Tests de los handlers de Lambda: validación y códigos HTTP."""
import decimal
import json
import uuid

import pytest

import todoList
from conftest import make_event
from create import create
from decimalencoder import DecimalEncoder
from delete import delete
from get import get
from list import list as list_todos
from update import update


def body(respuesta):
    return json.loads(respuesta["body"])


# ---------------------------------------------------------------- POST /todos

def test_create_devuelve_201_y_la_tarea(table):
    respuesta = create(make_event({"text": "  Comprar pan  "}), None)

    assert respuesta["statusCode"] == 201
    assert respuesta["headers"]["Content-Type"] == "application/json"
    tarea = body(respuesta)
    assert tarea["text"] == "Comprar pan"
    assert tarea["checked"] is False
    assert todoList.get_item(tarea["id"]) is not None


@pytest.mark.parametrize("evento", [
    make_event(None),
    make_event("esto no es JSON"),
    make_event([1, 2, 3]),
    make_event({}),
    make_event({"text": ""}),
    make_event({"text": "   "}),
    make_event({"text": 42}),
    make_event({"text": "x" * 1001}),
])
def test_create_rechaza_peticiones_no_validas(table, evento):
    respuesta = create(evento, None)

    assert respuesta["statusCode"] == 400
    assert "message" in body(respuesta)
    assert todoList.get_items() == []


def test_create_acepta_el_texto_de_longitud_maxima(table):
    assert create(make_event({"text": "x" * 1000}), None)["statusCode"] == 201


def test_error_inesperado_devuelve_500_sin_detalles(table, monkeypatch):
    def falla(text):
        raise RuntimeError("detalle interno que no debe salir")

    monkeypatch.setattr(todoList, "put_item", falla)

    respuesta = create(make_event({"text": "hola"}), None)

    assert respuesta["statusCode"] == 500
    assert "detalle interno" not in respuesta["body"]


# ----------------------------------------------------------------- GET /todos

def test_list_devuelve_todas_las_tareas(table):
    todoList.put_item("uno")
    todoList.put_item("dos")

    respuesta = list_todos(make_event(), None)

    assert respuesta["statusCode"] == 200
    assert {t["text"] for t in body(respuesta)} == {"uno", "dos"}


def test_list_vacia_devuelve_lista_vacia(table):
    assert body(list_todos(make_event(), None)) == []


# ------------------------------------------------------------ GET /todos/{id}

def test_get_devuelve_la_tarea(table):
    tarea = todoList.put_item("leer")

    respuesta = get(make_event(todo_id=tarea["id"]), None)

    assert respuesta["statusCode"] == 200
    assert body(respuesta) == tarea


def test_get_devuelve_404_si_no_existe(table):
    respuesta = get(make_event(todo_id=str(uuid.uuid4())), None)
    assert respuesta["statusCode"] == 404


@pytest.mark.parametrize("todo_id", [None, "no-es-un-uuid", "1' OR '1'='1"])
def test_get_rechaza_ids_no_validos(table, todo_id):
    assert get(make_event(todo_id=todo_id), None)["statusCode"] == 400


# ------------------------------------------------------------ PUT /todos/{id}

def test_update_modifica_la_tarea(table):
    tarea = todoList.put_item("antes")

    respuesta = update(
        make_event({"text": "después", "checked": True}, tarea["id"]), None)

    assert respuesta["statusCode"] == 200
    assert body(respuesta)["text"] == "después"
    assert body(respuesta)["checked"] is True


def test_update_acepta_checked_como_texto(table):
    tarea = todoList.put_item("antes")

    respuesta = update(
        make_event({"text": "después", "checked": "true"}, tarea["id"]), None)

    assert body(respuesta)["checked"] is True


@pytest.mark.parametrize("datos", [
    {"text": "sin checked"},
    {"checked": True},
    {"text": "x", "checked": "quizás"},
    {"text": "x", "checked": 1},
])
def test_update_rechaza_datos_no_validos(table, datos):
    tarea = todoList.put_item("antes")

    respuesta = update(make_event(datos, tarea["id"]), None)

    assert respuesta["statusCode"] == 400
    assert todoList.get_item(tarea["id"])["text"] == "antes"


def test_update_devuelve_404_si_no_existe(table):
    evento = make_event({"text": "x", "checked": False}, str(uuid.uuid4()))

    assert update(evento, None)["statusCode"] == 404
    assert todoList.get_items() == []


# --------------------------------------------------------- DELETE /todos/{id}

def test_delete_borra_la_tarea(table):
    tarea = todoList.put_item("borrar")

    respuesta = delete(make_event(todo_id=tarea["id"]), None)

    assert respuesta["statusCode"] == 204
    assert "body" not in respuesta
    assert todoList.get_item(tarea["id"]) is None


def test_delete_devuelve_404_si_no_existe(table):
    respuesta = delete(make_event(todo_id=str(uuid.uuid4())), None)
    assert respuesta["statusCode"] == 404


# ------------------------------------------------------------- DecimalEncoder

def test_decimal_encoder_convierte_numeros_de_dynamodb():
    datos = {"entero": decimal.Decimal("3"), "real": decimal.Decimal("1.5")}
    assert json.loads(json.dumps(datos, cls=DecimalEncoder)) == {
        "entero": 3, "real": 1.5}


def test_decimal_encoder_rechaza_tipos_desconocidos():
    with pytest.raises(TypeError):
        json.dumps({"x": object()}, cls=DecimalEncoder)
