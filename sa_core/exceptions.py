"""
sa_core/exceptions.py

Maps SQLAlchemy exceptions to DRF-compatible exceptions.
"""
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.views import exception_handler
from sqlalchemy.exc import IntegrityError, NoResultFound, MultipleResultsFound


class ConflictError(APIException):
    status_code = 409
    default_detail = "A conflict occurred."
    default_code = "conflict"


def sqlalchemy_exception_handler(exc, context):
    """
    Custom DRF exception handler that converts SQLAlchemy errors
    into proper HTTP responses.

    Register in settings:
        REST_FRAMEWORK = {
            "EXCEPTION_HANDLER": "sa_core.exceptions.sqlalchemy_exception_handler"
        }
    """
    # Handle SQLAlchemy-specific exceptions first
    if isinstance(exc, NoResultFound):
        exc = NotFound(detail="The requested resource was not found.")
    elif isinstance(exc, MultipleResultsFound):
        exc = ValidationError(detail="Multiple results found; expected one.")
    elif isinstance(exc, IntegrityError):
        detail = str(exc.orig) if exc.orig else "Integrity constraint violated."
        exc = ConflictError(detail=detail)

    return exception_handler(exc, context)
