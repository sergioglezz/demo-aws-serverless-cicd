import todoList
from api_utils import (api_handler, get_todo_id, parse_body, response,
                       validate_checked, validate_text)


@api_handler
def update(event, context):
    """PUT /todos/{id}: modifica el texto y el estado de una tarea."""
    todo_id = get_todo_id(event)
    data = parse_body(event)
    item = todoList.update_item(
        todo_id, validate_text(data), validate_checked(data))
    return response(200, item)
