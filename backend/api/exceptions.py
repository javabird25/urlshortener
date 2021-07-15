from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as default_exception_handler


class Conflict(APIException):
    status_code = 409
    default_code = 'conflict'
    default_detail = 'Resource is occupied.'


def exception_handler(exc, context):
    """Custom API exception handler which unwraps the exception details from JSON "detail" value."""
    response = default_exception_handler(exc, context)
    if response is not None:
        response.content = str(exc.detail)
    return response
