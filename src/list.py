import todoList
from api_utils import api_handler, response


@api_handler
def list(event, context):
    """GET /todos: devuelve todas las tareas."""
    return response(200, todoList.get_items())
