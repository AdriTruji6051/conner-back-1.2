from typing import Any, Dict, List, Optional
from flask import jsonify


# ---------------------------------------------------------------------------
# Custom exception for collecting multiple field-level validation errors
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Exception that carries a list of field-level validation errors.

    Each error is a dict with a single key (the field name) mapped to the
    error message, e.g. ``{"cost": "Must be greater than zero"}``.
    The list is returned as-is in ``responseBody`` so the client receives
    **all** validation failures at once.
    """

    def __init__(self, errors: List[Dict[str, str]] | None = None):
        self.errors: List[Dict[str, str]] = errors or []
        super().__init__(str(self.errors))

    # -- collector helpers --------------------------------------------------

    def add(self, field: str, message: str) -> 'ValidationError':
        """Append a single field error and return *self* for chaining."""
        self.errors.append({field: message})
        return self

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def raise_if_errors(self) -> None:
        """Raise *self* only when at least one error has been collected."""
        if self.has_errors:
            raise self


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def collect_missing_keys(data: dict, keys: list[str], description_tag: str = 'Not specified') -> List[Dict[str, str]]:
    """Return a list of ``{key: "is required …"}`` dicts for every missing key.

    Unlike the legacy ``raise_exception_if_missing_keys`` this never raises
    by itself — it just returns errors so the caller can collect them.
    """
    if set(keys).issubset(data):
        return []
    missing = set(keys) - set(data)
    return [{key: f'Is required for {description_tag}'} for key in sorted(missing)]


def raise_exception_if_missing_keys(data: dict, keys: list[str], description_tag: str = 'Not specified'):
    """Validate that all required keys are present in data dict.

    Kept for backward compatibility — internally delegates to
    ``collect_missing_keys`` and converts the result into a single
    ``ValidationError``.
    """
    errors = collect_missing_keys(data, keys, description_tag)
    if errors:
        raise ValidationError(errors)


def profit_percentage(cost: float, sale_price: float) -> int:
    if cost <= 0:
        raise ValueError('cost must be greater than zero')
    
    profit = sale_price - cost

    return int((profit / cost) * 100)


class AppResponse:
    """Standardized API response wrapper for all endpoints"""
    
    def __init__(self, response_body: Any, success: bool, status_code: int):
        self.response_body = response_body
        self.success = success
        self.status_code = status_code

    @staticmethod
    def _split_pagination(payload: Any) -> tuple[Any, Optional[Dict[str, Any]]]:
        """If payload contains pagination metadata, separate it for top-level inclusion."""
        if isinstance(payload, dict):
            required_keys = {'items', 'page', 'page_size', 'pages', 'total'}
            if required_keys.issubset(payload.keys()):
                pagination = {k: payload[k] for k in ('page', 'page_size', 'pages', 'total')}
                return payload['items'], pagination
        return payload, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        body, pagination = self._split_pagination(self.response_body)
        res = {
            'responseBody': body,
            'success': self.success,
            'statusCode': self.status_code
        }
        if pagination:
            res.update(pagination)
        return res
    
    def to_flask_tuple(self) -> tuple:
        """Convert to Flask response tuple (dict, status_code)"""
        return (jsonify(self.to_dict()), self.status_code)
    
    @staticmethod
    def success(data: Any, status_code: int = 200) -> 'AppResponse':
        """Create successful response"""
        return AppResponse(response_body=data, success=True, status_code=status_code)
    
    @staticmethod
    def created(data: Any) -> 'AppResponse':
        """Create 201 created response"""
        return AppResponse(response_body=data, success=True, status_code=201)
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> 'AppResponse':
        """Create error response"""
        return AppResponse(response_body={'error': message}, success=False, status_code=status_code)
    
    @staticmethod
    def bad_request(message: str) -> 'AppResponse':
        """Create 400 bad request response"""
        return AppResponse.error(message, 400)
    
    @staticmethod
    def unauthorized(message: str = 'Unauthorized') -> 'AppResponse':
        """Create 401 unauthorized response"""
        return AppResponse.error(message, 401)
    
    @staticmethod
    def forbidden(message: str = 'Forbidden') -> 'AppResponse':
        """Create 403 forbidden response"""
        return AppResponse.error(message, 403)
    
    @staticmethod
    def not_found(message: str = 'Not found') -> 'AppResponse':
        """Create 404 not found response"""
        return AppResponse.error(message, 404)
    
    @staticmethod
    def validation_error(errors: List[Dict[str, str]]) -> 'AppResponse':
        """Create 422 response with a list of field-level validation errors.

        ``responseBody`` will be the error list directly, e.g.::

            [{"cost": "Must be greater than zero"}, {"sale_type": "Invalid"}]
        """
        return AppResponse(response_body=errors, success=False, status_code=422)

    @staticmethod
    def unprocessable(message: str) -> 'AppResponse':
        """Create 422 unprocessable entity response (single-message variant)"""
        return AppResponse.error(message, 422)

    @staticmethod
    def conflict(message: str) -> 'AppResponse':
        """Create 409 conflict response (e.g. duplicate key)"""
        return AppResponse.error(message, 409)

    @staticmethod
    def no_content(message: str = 'No content') -> 'AppResponse':
        """Create 204 no content response"""
        return AppResponse(response_body={'message': message}, success=True, status_code=204)
    
    @staticmethod
    def server_error(message: str = 'Internal server error') -> 'AppResponse':
        """Create 500 server error response"""
        return AppResponse.error(message, 500)