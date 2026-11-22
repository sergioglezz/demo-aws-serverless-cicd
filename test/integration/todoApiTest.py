"""Tests de integración contra la API desplegada.

Necesitan la variable BASE_URL con la URL base de la API, por ejemplo:
    BASE_URL=https://xxxx.execute-api.us-east-1.amazonaws.com/Prod \
        pytest test/integration/todoApiTest.py

Marcas:
    readonly   -> subconjunto que se ejecuta en producción (deja los datos
                  como estaban)
    writeonly  -> resto de pruebas, solo en staging
"""
import os
import unittest

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
TIMEOUT = 10  # segundos


@pytest.mark.api
class TestApi(unittest.TestCase):

    def setUp(self):
        self.assertTrue(
            BASE_URL.startswith("http"), "BASE_URL no configurada")
        self.url = f"{BASE_URL}/todos"

    # ------------------------------------------------------------ utilidades

    def create_todo(self, text):
        response = requests.post(self.url, json={"text": text},
                                 timeout=TIMEOUT)
        self.assertEqual(response.status_code, 201,
                         f"Error al crear la tarea en {self.url}")
        todo = response.json()
        self.assertEqual(todo["text"], text)
        return todo

    def delete_todo(self, todo_id):
        url = f"{self.url}/{todo_id}"
        response = requests.delete(url, timeout=TIMEOUT)
        self.assertEqual(response.status_code, 204,
                         f"Error al borrar la tarea en {url}")

    # ----------------------------------------------------------------- tests

    @pytest.mark.readonly
    def test_api_listtodos(self):
        todo = self.create_todo("Integration text example")

        response = requests.get(self.url, timeout=TIMEOUT)

        self.assertEqual(response.status_code, 200,
                         f"Error al listar en {self.url}")
        self.assertIn(todo["id"], [t["id"] for t in response.json()])
        self.delete_todo(todo["id"])

    @pytest.mark.writeonly
    def test_api_addtodo(self):
        todo = self.create_todo("Integration text example")
        self.assertFalse(todo["checked"])
        self.delete_todo(todo["id"])

    @pytest.mark.writeonly
    def test_api_addtodo_invalid(self):
        response = requests.post(self.url, json={"text": ""},
                                 timeout=TIMEOUT)
        self.assertEqual(response.status_code, 400)

    @pytest.mark.readonly
    def test_api_gettodo(self):
        todo = self.create_todo("Integration text example - GET")
        url = f"{self.url}/{todo['id']}"

        response = requests.get(url, timeout=TIMEOUT)

        self.assertEqual(response.status_code, 200, f"Error en GET {url}")
        self.assertEqual(response.json()["text"],
                         "Integration text example - GET")
        self.delete_todo(todo["id"])

    @pytest.mark.writeonly
    def test_api_updatetodo(self):
        todo = self.create_todo("Integration text example - Initial")
        url = f"{self.url}/{todo['id']}"

        response = requests.put(
            url,
            json={"text": "Integration text example - Modified",
                  "checked": True},
            timeout=TIMEOUT)

        self.assertEqual(response.status_code, 200, f"Error en PUT {url}")
        self.assertEqual(response.json()["text"],
                         "Integration text example - Modified")
        self.assertTrue(response.json()["checked"])

        response = requests.get(url, timeout=TIMEOUT)
        self.assertEqual(response.json()["text"],
                         "Integration text example - Modified")
        self.delete_todo(todo["id"])

    @pytest.mark.writeonly
    def test_api_deletetodo(self):
        todo = self.create_todo("Integration text example - Delete")
        url = f"{self.url}/{todo['id']}"

        self.delete_todo(todo["id"])

        response = requests.get(url, timeout=TIMEOUT)
        self.assertEqual(response.status_code, 404, f"Error en GET {url}")
