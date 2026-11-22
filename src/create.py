import todoList
from api_utils import api_handler, parse_body, response, validate_text


@api_handler
def create(event, context):
    """POST /todos: crea una tarea."""
    text = validate_text(parse_body(event))
    return response(201, todoList.put_item(text))
