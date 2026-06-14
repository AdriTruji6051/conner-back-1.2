import socket
import json
import base64
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
        
        # Get printer dictionary which includes host information
        # Try localhost first, then get from dict
        printers_dict = printers_manager.dict('127.0.0.1', refresh=True)
        
        # Extract unique hosts from printer dictionary
        hosts = set()
        for printer_name, printer_info in printers_dict.items():
            if isinstance(printer_info, dict) and 'host' in printer_info:
                hosts.add(printer_info['host'])
        
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
        printer_name: Optional printer name to use (will update printer before sending)
        ipv4: IP address of printer service
        port: Port of printer service (default 9100)
        
    Returns:
        Response dictionary from printer service
    """
    try:
        from app.controlers.printers import Printers
        printers_manager = Printers()
        
        # If printer_name specified, update the printer first
        if printer_name:
            try:
                printers_manager.update_printer(printer_name, ipv4)
            except Exception as e:
                print(f"Warning: Could not set printer {printer_name}: {e}")
        
        # Send command to service
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((ipv4, port))
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
        print(f"Error: Printer service not reachable at {ipv4}:{port}")
        return {
            'status': 'error',
            'message': f'Printer service not reachable at {ipv4}:{port}. Make sure the service is running.'
        }
    except socket.timeout:
        print(f"Error: Printer service timeout at {ipv4}:{port}")
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
