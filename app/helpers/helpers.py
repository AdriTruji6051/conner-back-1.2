from typing import Any, Dict, Optional
from flask import jsonify


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            'responseBody': self.response_body,
            'success': self.success,
            'statusCode': self.status_code
        }
    
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
    def unprocessable(message: str) -> 'AppResponse':
        """Create 422 unprocessable entity response"""
        return AppResponse.error(message, 422)
    
    @staticmethod
    def server_error(message: str = 'Internal server error') -> 'AppResponse':
        """Create 500 server error response"""
        return AppResponse.error(message, 500)