"""
sa_core/middleware.py

Attaches a SQLAlchemy session to every request, commits on success,
rolls back on exception, and closes on completion.
"""
from sa_core.database import SessionLocal


class SQLAlchemySessionMiddleware:
    """
    Manages SQLAlchemy session lifecycle per HTTP request.
    Attach it AFTER Django's auth middleware so request.user is available.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session = SessionLocal()
        request.sa_session = session
        try:
            response = self.get_response(request)
            session.commit()
            return response
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            # Clean up reference to avoid accidental use after close
            if hasattr(request, "sa_session"):
                del request.sa_session
