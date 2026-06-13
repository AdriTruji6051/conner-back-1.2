"""
Standardized error codes for frontend translation.
Backend returns these codes, frontend translates them using i18n files.

Usage:
    from app.helpers.error_codes import ErrorCodes
    return AppResponse.unauthorized(error_code=ErrorCodes.AUTH_INVALID_CREDENTIALS)
"""


class ErrorCodes:
    """Centralized error code constants for API responses.
    
    These codes map to translation keys in the frontend i18n files.
    Format: CATEGORY.ERROR_NAME
    """
    
    # ==================== Authentication Errors ====================
    AUTH_INVALID_CREDENTIALS = 'AUTH.LOGIN_ERROR'
    AUTH_SESSION_EXPIRED = 'AUTH.SESSION_EXPIRED'
    AUTH_UNAUTHORIZED = 'ERRORS.UNAUTHORIZED'
    AUTH_FORBIDDEN = 'ERRORS.FORBIDDEN'
    AUTH_PLEASE_LOGIN = 'AUTH.PLEASE_LOGIN'
    
    # ==================== Validation Errors ====================
    VALIDATION_REQUIRED = 'VALIDATION.REQUIRED'
    VALIDATION_INVALID_FORMAT = 'VALIDATION.INVALID_FORMAT'
    VALIDATION_MIN_LENGTH = 'VALIDATION.MIN_LENGTH'
    VALIDATION_MAX_LENGTH = 'VALIDATION.MAX_LENGTH'
    VALIDATION_INVALID_NUMBER = 'VALIDATION.INVALID_NUMBER'
    VALIDATION_INVALID_EMAIL = 'VALIDATION.INVALID_EMAIL'
    VALIDATION_MIN_VALUE = 'VALIDATION.MIN_VALUE'
    VALIDATION_MAX_VALUE = 'VALIDATION.MAX_VALUE'
    VALIDATION_PATTERN_MISMATCH = 'VALIDATION.PATTERN_MISMATCH'
    VALIDATION_MUST_BE_POSITIVE = 'VALIDATION.MUST_BE_POSITIVE'
    VALIDATION_MUST_BE_INTEGER = 'VALIDATION.MUST_BE_INTEGER'
    VALIDATION_PASSWORDS_MUST_MATCH = 'VALIDATION.PASSWORDS_MUST_MATCH'
    
    # ==================== Product Errors ====================
    PRODUCT_NOT_FOUND = 'PRODUCTS.PRODUCT_NOT_FOUND'
    PRODUCT_DUPLICATE_CODE = 'PRODUCTS.DUPLICATE_CODE'
    PRODUCT_INVALID_PRICE = 'PRODUCTS.INVALID_PRICE'
    PRODUCT_CREATED = 'PRODUCTS.PRODUCT_CREATED'
    PRODUCT_UPDATED = 'PRODUCTS.PRODUCT_UPDATED'
    PRODUCT_DELETED = 'PRODUCTS.PRODUCT_DELETED'
    
    # ==================== Ticket Errors ====================
    TICKET_NOT_FOUND = 'TICKETS.TICKET_NOT_FOUND'
    TICKET_CREATED = 'TICKETS.TICKET_CREATED'
    TICKET_UPDATED = 'TICKETS.TICKET_UPDATED'
    TICKET_DELETED = 'TICKETS.TICKET_DELETED'
    
    # ==================== User Errors ====================
    USER_NOT_FOUND = 'USERS.USER_NOT_FOUND'
    USER_DUPLICATE_USERNAME = 'USERS.DUPLICATE_USERNAME'
    USER_CREATED = 'USERS.USER_CREATED'
    USER_UPDATED = 'USERS.USER_UPDATED'
    USER_DELETED = 'USERS.USER_DELETED'
    USER_PASSWORD_MISMATCH = 'USERS.PASSWORD_MISMATCH'
    
    # ==================== Department Errors ====================
    DEPARTMENT_NOT_FOUND = 'DEPARTMENTS.DEPARTMENT_NOT_FOUND'
    DEPARTMENT_CREATED = 'DEPARTMENTS.DEPARTMENT_CREATED'
    DEPARTMENT_UPDATED = 'DEPARTMENTS.DEPARTMENT_UPDATED'
    DEPARTMENT_DELETED = 'DEPARTMENTS.DEPARTMENT_DELETED'
    
    # ==================== Settings Errors ====================
    SETTINGS_UPDATED = 'SETTINGS.SETTINGS_UPDATED'
    SETTINGS_LANGUAGE_CHANGED = 'SETTINGS.LANGUAGE_CHANGED'
    SETTINGS_PHOTO_UPLOADED = 'SETTINGS.PHOTO_UPLOADED'
    SETTINGS_PHOTO_DELETED = 'SETTINGS.PHOTO_DELETED'
    
    # ==================== Drawer Errors ====================
    DRAWER_OPENED = 'DRAWER.DRAWER_OPENED'
    DRAWER_CLOSED = 'DRAWER.DRAWER_CLOSED'
    
    # ==================== Printer Errors ====================
    PRINTER_ERROR = 'PRINTERS.PRINTER_ERROR'
    PRINTER_PRINT_SUCCESS = 'PRINTERS.PRINT_SUCCESS'
    PRINTER_PRINT_FAILED = 'PRINTERS.PRINT_FAILED'
    
    # ==================== Generic Errors ====================
    ERROR_GENERIC = 'ERRORS.GENERIC_ERROR'
    ERROR_NETWORK = 'ERRORS.NETWORK_ERROR'
    ERROR_VALIDATION = 'ERRORS.VALIDATION_ERROR'
    ERROR_SERVER = 'ERRORS.SERVER_ERROR'
    ERROR_NOT_FOUND = 'ERRORS.NOT_FOUND'
    ERROR_CONFLICT = 'ERRORS.CONFLICT'
    ERROR_REQUIRED_FIELD = 'ERRORS.REQUIRED_FIELD'
    ERROR_INVALID_FORMAT = 'ERRORS.INVALID_FORMAT'
    ERROR_DUPLICATE_ENTRY = 'ERRORS.DUPLICATE_ENTRY'
    ERROR_OPERATION_FAILED = 'ERRORS.OPERATION_FAILED'
    ERROR_TIMEOUT = 'ERRORS.TIMEOUT'
    ERROR_UNKNOWN = 'ERRORS.UNKNOWN_ERROR'
    
    # ==================== Success Messages ====================
    SUCCESS_OPERATION = 'MESSAGES.SUCCESS'
    SUCCESS_SAVED = 'MESSAGES.SAVED'
    SUCCESS_DELETED = 'MESSAGES.DELETED'
    SUCCESS_UPDATED = 'MESSAGES.UPDATED'
    SUCCESS_CREATED = 'MESSAGES.CREATED'


# Helper function to get error code for common scenarios
def get_validation_error_code(_field_name: str, error_type: str) -> str:
    """Get appropriate error code for validation errors.
    
    Args:
        field_name: Name of the field with error
        error_type: Type of validation error (required, min_length, etc.)
        
    Returns:
        Error code string for translation
    """
    error_map = {
        'required': ErrorCodes.VALIDATION_REQUIRED,
        'min_length': ErrorCodes.VALIDATION_MIN_LENGTH,
        'max_length': ErrorCodes.VALIDATION_MAX_LENGTH,
        'invalid_format': ErrorCodes.VALIDATION_INVALID_FORMAT,
        'invalid_number': ErrorCodes.VALIDATION_INVALID_NUMBER,
        'invalid_email': ErrorCodes.VALIDATION_INVALID_EMAIL,
        'min_value': ErrorCodes.VALIDATION_MIN_VALUE,
        'max_value': ErrorCodes.VALIDATION_MAX_VALUE,
    }
    return error_map.get(error_type, ErrorCodes.ERROR_VALIDATION)
