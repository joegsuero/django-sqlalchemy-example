"""
sa_core/middleware.py

Middleware opcional que adjunta una sesión SQLAlchemy a cada request.
Útil para vistas Django clásicas que necesiten acceso via request.sa_session.

NO incluir en MIDDLEWARE si todos los accesos a la BD se hacen
con `with get_session()` desde los ViewSets (que es el patrón recomendado).

Para activarlo, agregarlo en config/settings.py:
    MIDDLEWARE = [
        ...
        'sa_core.middleware.SQLAlchemySessionMiddleware',
    ]
"""
from sa_core.database import SessionLocal


class SQLAlchemySessionMiddleware:
    """
    Gestiona el ciclo de vida de la sesión SQLAlchemy por request HTTP.
    Hace commit en respuestas exitosas, rollback en excepciones.
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
            if hasattr(request, "sa_session"):
                del request.sa_session
