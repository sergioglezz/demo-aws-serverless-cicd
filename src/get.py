import todoList
from api_utils import api_handler, get_todo_id, response


@api_handler
def get(event, context):
    """GET /todos/{id}: devuelve una tarea."""
    item = todoList.get_item(get_todo_id(event))
    if item is None:
        raise todoList.TodoNotFoundError()
    return response(200, item)
