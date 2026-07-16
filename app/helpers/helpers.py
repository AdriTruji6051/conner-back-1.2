import socket
import json
import base64
import logging
from typing import Any, Dict, List, Optional
from flask import jsonify



# ---------------------------------------------------------------------------
# Log Sanitization - Security Enhancement
# ---------------------------------------------------------------------------

# Sensitive fields that should never be logged
SENSITIVE_FIELDS = {
    'password', 'token', 'secret', 'api_key', 'apikey',
    'authorization', 'auth', 'jwt', 'session', 'cookie',
    'secret_key', 'jwt_secret_key'
}

def sanitize_for_logging(data: Any, max_length: int = 200) -> str:
    """Sanitize data before logging to remove sensitive information.
    
    Args:
        data: Data to sanitize (dict, list, str, etc.)
        max_length: Maximum length of output string
        
    Returns:
        Sanitized string safe for logging
    """
    if data is None:
        return 'None'
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            # Check if key contains sensitive field name
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_for_logging(value, max_length)
            else:
                sanitized[key] = str(value)[:100]  # Limit individual values
        result = str(sanitized)
    elif isinstance(data, list):
        sanitized = [sanitize_for_logging(item, max_length) for item in data[:10]]  # Limit to 10 items
        result = str(sanitized)
    else:
        result = str(data)
    
    # Truncate if too long
    if len(result) > max_length:
        result = result[:max_length] + '...[truncated]'
    
    return result


def log_request_safely(route: str, data: Any = None, error: Exception = None, level: str = 'info'):
    """Log request information safely without exposing sensitive data.
    
    Args:
        route: Route/endpoint name
        data: Request data (will be sanitized)
        error: Exception if any
        level: Log level ('info', 'warning', 'error')
    """
    logger = logging.getLogger(__name__)
    
    if error:
        sanitized_data = sanitize_for_logging(data) if data else 'No data'
        logger.error(
            f"Route: {route} | Error: {type(error).__name__}: {str(error)[:200]} | "
            f"Data: {sanitized_data}"
        )
    else:
        sanitized_data = sanitize_for_logging(data) if data else 'No data'
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"Route: {route} | Data: {sanitized_data}")



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


def format_to_two_decimals(number: float) -> float:
    """Round and format a number to 2 decimal places to prevent floating-point precision errors.
    
    This is the unified rounding function for all monetary calculations in the system.
    """
    return round(number, 2)


def profit_percentage(cost: float, sale_price: float) -> int:
    if cost <= 0:
        raise ValueError('cost must be greater than zero')
    
    profit = sale_price - cost

    return int((profit / cost) * 100)


class AppResponse:
    """Standardized API response wrapper for all endpoints"""
    
    def __init__(self, response_body: Any, success: bool, status_code: int, error_code: Optional[str] = None):
        self.response_body = response_body
        self.success = success
        self.status_code = status_code
        self.error_code = error_code

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
        if self.error_code:
            res['errorCode'] = self.error_code
        if pagination:
            res.update(pagination)
        return res
    
    def to_flask_tuple(self) -> tuple:
        """Convert to Flask response tuple (dict, status_code)"""
        return (jsonify(self.to_dict()), self.status_code)
    
    @staticmethod
    def success(data: Any, status_code: int = 200, error_code: Optional[str] = None) -> 'AppResponse':
        """Create successful response"""
        return AppResponse(response_body=data, success=True, status_code=status_code, error_code=error_code)
    
    @staticmethod
    def created(data: Any, error_code: Optional[str] = None) -> 'AppResponse':
        """Create 201 created response"""
        return AppResponse(response_body=data, success=True, status_code=201, error_code=error_code)
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_code: Optional[str] = None) -> 'AppResponse':
        """Create error response"""
        return AppResponse(response_body={'error': message}, success=False, status_code=status_code, error_code=error_code)
    
    @staticmethod
    def bad_request(message: str) -> 'AppResponse':
        """Create 400 bad request response"""
        return AppResponse.error(message, 400)
    
    @staticmethod
    def unauthorized(message: str = 'Unauthorized', error_code: Optional[str] = None) -> 'AppResponse':
        """Create 401 unauthorized response"""
        return AppResponse.error(message, 401, error_code)
    
    @staticmethod
    def forbidden(message: str = 'Forbidden', error_code: Optional[str] = None) -> 'AppResponse':
        """Create 403 forbidden response"""
        return AppResponse.error(message, 403, error_code)
    
    @staticmethod
    def not_found(message: str = 'Not found', error_code: Optional[str] = None) -> 'AppResponse':
        """Create 404 not found response"""
        return AppResponse.error(message, 404, error_code)
    
    @staticmethod
    def validation_error(errors: List[Dict[str, str]], error_code: Optional[str] = None) -> 'AppResponse':
        """Create 422 response with a list of field-level validation errors.

        ``responseBody`` will be the error list directly, e.g.::

            [{"cost": "Must be greater than zero"}, {"sale_type": "Invalid"}]
        """
        return AppResponse(response_body=errors, success=False, status_code=422, error_code=error_code)

    @staticmethod
    def unprocessable(message: str, error_code: Optional[str] = None) -> 'AppResponse':
        """Create 422 unprocessable entity response (single-message variant)"""
        return AppResponse.error(message, 422, error_code)

    @staticmethod
    def conflict(message: str, error_code: Optional[str] = None) -> 'AppResponse':
        """Create 409 conflict response (e.g. duplicate key)"""
        return AppResponse.error(message, 409, error_code)

    @staticmethod
    def no_content(message: str = 'No content') -> 'AppResponse':
        """Create 204 no content response"""
        return AppResponse(response_body={'message': message}, success=True, status_code=204)
    
    @staticmethod
    def server_error(message: str = 'Internal server error') -> 'AppResponse':
        """Create 500 server error response"""
        return AppResponse.error(message, 500)


# ---------------------------------------------------------------------------
# Photo Distribution Functions
# ---------------------------------------------------------------------------

def get_printer_service_hosts() -> List[str]:
    """Get all registered printer service hosts from Printers manager."""
    try:
        from app.controlers.printers import Printers
        printers_manager = Printers()
        
        # Get all registered hosts from avaliable_printers cache
        hosts = set()
        
        # If cache is empty, try to populate it with localhost
        if not printers_manager.avaliable_printers:
            try:
                printers_manager.dict('127.0.0.1', refresh=True)
            except Exception:
                pass
        
        # Collect all hosts from the cache
        for host in printers_manager.avaliable_printers.keys():
            hosts.add(host)
        
        # If no hosts found, default to localhost
        if not hosts:
            hosts.add('127.0.0.1')
        
        return list(hosts)
    except Exception as e:
        print(f"Error getting printer hosts: {e}")
        # Fallback to localhost
        return ['127.0.0.1']


def push_photo_to_service(host: str, port: int, photo_id: str, photo_data: bytes) -> bool:
    """Push photo to a single printer service.
    
    Args:
        host: Service host IP address
        port: Service port (default 9100)
        photo_id: Unique photo identifier
        photo_data: Processed photo bytes (PNG format)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Encode photo data to base64
        photo_base64 = base64.b64encode(photo_data).decode('utf-8')
        
        # Create request
        request = {
            "action": "photo/save",
            "photo_id": photo_id,
            "photo_data": photo_base64,
            "overwrite": True
        }
        
        # Send to service
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((host, port))
            s.sendall(json.dumps(request).encode('utf-8'))
            
            # Receive response
            response = s.recv(4096).decode('utf-8')
            result = json.loads(response)
            
            success = result.get('status') == 'success'
            if success:
                print(f"Photo {photo_id} pushed to {host}:{port}")
            else:
                print(f"Failed to push photo to {host}:{port}: {result.get('message')}")
            
            return success
    except Exception as e:
        print(f"Failed to push photo to {host}:{port} - {e}")
        return False


def push_photo_to_all_services(photo_id: str, photo_data: bytes) -> Dict[str, bool]:
    """Push photo to all registered printer services.
    
    Args:
        photo_id: Unique photo identifier
        photo_data: Processed photo bytes (PNG format)
        
    Returns:
        Dictionary mapping host to success status
    """
    hosts = get_printer_service_hosts()
    results = {}
    
    if not hosts:
        print("Warning: No printer service hosts found")
        return results
    
    for host in hosts:
        port = 9100  # Default printer service port
        success = push_photo_to_service(host, port, photo_id, photo_data)
        results[host] = success
    
    return results


def delete_photo_from_service(host: str, port: int, photo_id: str) -> bool:
    """Delete photo from a single printer service.
    
    Args:
        host: Service host IP address
        port: Service port (default 9100)
        photo_id: Unique photo identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        request = {
            "action": "photo/delete",
            "photo_id": photo_id
        }
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, port))
            s.sendall(json.dumps(request).encode('utf-8'))
            response = s.recv(4096).decode('utf-8')
            result = json.loads(response)
            
            success = result.get('status') == 'success'
            if success:
                print(f"Photo {photo_id} deleted from {host}:{port}")
            else:
                print(f"Failed to delete photo from {host}:{port}: {result.get('message')}")
            
            return success
    except Exception as e:
        print(f"Failed to delete photo from {host}:{port} - {e}")
        return False


def delete_photo_from_all_services(photo_id: str) -> Dict[str, bool]:
    """Delete photo from all registered printer services.
    
    Args:
        photo_id: Unique photo identifier
        
    Returns:
        Dictionary mapping host to success status
    """
    hosts = get_printer_service_hosts()
    results = {}
    
    for host in hosts:
        port = 9100
        success = delete_photo_from_service(host, port, photo_id)
        results[host] = success
    
    return results





def send_to_printer_service(command: dict, printer_name: str = None, ipv4: str = '127.0.0.1', port: int = 9100) -> dict:
    """Send a command to the printer service.
    
    Args:
        command: Dictionary command to send to printer service
        printer_name: Optional printer name to use (will find correct service IP)
        ipv4: IP address of client (used to search for printer)
        port: Port of printer service (default 9100)
        
    Returns:
        Response dictionary from printer service
    """
    try:
        from app.controlers.printers import Printers
        printers_manager = Printers()
        
        # Find the correct printer service IP if printer_name is specified
        service_ip = ipv4
        if printer_name:
            found_ip = printers_manager._find_printer_service_ip(printer_name, ipv4)
            if not found_ip:
                return {
                    'status': 'error',
                    'message': f'Printer "{printer_name}" not found in any available printer service'
                }
            service_ip = found_ip
            
            # Update the printer on the correct service
            try:
                printers_manager.update_printer(printer_name, service_ip)
            except Exception as e:
                print(f"Warning: Could not set printer {printer_name} on {service_ip}: {e}")
        
        # Send command to the correct service
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((service_ip, port))
            s.sendall(json.dumps(command).encode('utf-8'))
            
            # Receive response
            response = s.recv(4096).decode('utf-8')
            
            # Check if response is empty
            if not response or not response.strip():
                print(f"Warning: Printer service returned empty response")
                return {
                    'status': 'warning',
                    'message': 'Printer service returned empty response. The action may not be supported yet.'
                }
            
            # Try to parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError as json_err:
                print(f"Warning: Could not parse printer service response: {response[:100]}")
                return {
                    'status': 'warning',
                    'message': f'Printer service returned invalid JSON: {str(json_err)}',
                    'raw_response': response[:200]
                }
            
    except ConnectionRefusedError:
        print(f"Error: Printer service not reachable at {service_ip}:{port}")
        return {
            'status': 'error',
            'message': f'Printer service not reachable at {service_ip}:{port}. Make sure the service is running.'
        }
    except socket.timeout:
        print(f"Error: Printer service timeout at {service_ip}:{port}")
        return {
            'status': 'error',
            'message': f'Printer service timeout. The service may be busy or not responding.'
        }
    except Exception as e:
        print(f"Error sending to printer service: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
