import todoList
from api_utils import api_handler, get_todo_id, response


@api_handler
def delete(event, context):
    """DELETE /todos/{id}: borra una tarea."""
    todoList.delete_item(get_todo_id(event))
    return response(204)
