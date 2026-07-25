from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from config.config import Config


def jwt_protected():
    """Drop-in replacement for ``@jwt_required()`` that can be toggled off.

    When ``DISABLE_JWT=True`` is set in the environment the decorator becomes
    a no-op, allowing all requests through without a token.  In every other
    respect the behaviour is identical to ``@jwt_required()``.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not Config.DISABLE_JWT:
                verify_jwt_in_request()
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    """Safe replacement for ``get_jwt_identity()``.

    Returns the JWT identity when JWT is enabled, or ``None`` when
    ``DISABLE_JWT=True`` (avoids the RuntimeError raised by calling
    ``get_jwt_identity()`` without an active JWT context).
    """
    if Config.DISABLE_JWT:
        return None
    return get_jwt_identity()
