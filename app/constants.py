"""
Application-wide constants for the Conner POS backend.

This module centralizes all magic strings, numbers, and configuration values
used throughout the application to improve maintainability and reduce errors.
"""

# ============================================================================
# Product Constants
# ============================================================================

# Special product codes
QUICKSALE_CODE = 'QUICKSALE'
COMMONSALE_CODE = 'COMMONSALE'

# Department constants
DEFAULT_DEPARTMENT_DESCRIPTION = '___'

# Sale types
SALE_TYPE_UNIT = 'U'
SALE_TYPE_DECIMAL = 'D'
VALID_SALE_TYPES = (SALE_TYPE_UNIT, SALE_TYPE_DECIMAL)

# ============================================================================
# Pagination Constants
# ============================================================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
SEARCH_DEFAULT_PAGE_SIZE = 20

# ============================================================================
# Ticket Constants
# ============================================================================

# Default profit margin when cost is unknown
UNDEFINED_PROFIT_MARGIN = 0.20

# Default IP address for local operations
DEFAULT_IPV4 = '127.0.0.1'

# Default language for tickets
DEFAULT_LANGUAGE = 'es-MX'

# ============================================================================
# Validation Constants
# ============================================================================

# Minimum length for secret keys
MIN_SECRET_KEY_LENGTH = 32

# Sensitive field names for log sanitization
SENSITIVE_FIELDS = {
    'password', 'token', 'secret', 'api_key', 'apikey',
    'authorization', 'auth', 'jwt', 'session', 'cookie',
    'secret_key', 'jwt_secret_key'
}

# ============================================================================
# Error Messages
# ============================================================================

# Product errors
ERROR_PROTECTED_PLACEHOLDER = 'Protected placeholder products cannot be used as associate.'
ERROR_PRODUCT_NOT_FOUND = 'Product with code {code} not found'
ERROR_PRODUCT_CODE_RESERVED = 'This code is reserved for system use.'
ERROR_PRODUCT_PROTECTED_PARENT = 'Protected placeholder products cannot be used as parent.'
ERROR_PRODUCT_PROTECTED_MODIFY = 'Protected placeholder products cannot be modified.'
ERROR_PRODUCT_PROTECTED_DELETE = 'Protected placeholder products cannot be deleted.'
ERROR_PRODUCT_PROTECTED_INVENTORY = 'Protected placeholder inventory cannot be modified manually.'

# Department errors
ERROR_DEPARTMENT_NOT_FOUND = 'Department with code {code} not found'
ERROR_DEPARTMENT_DEFAULT_EXISTS = 'Default no-department already exists.'
ERROR_DEPARTMENT_RESERVED_DESCRIPTION = 'Description reserved for default department.'
ERROR_DEPARTMENT_PROTECTED_UPDATE = 'Default department cannot be updated.'
ERROR_DEPARTMENT_PROTECTED_DELETE = 'Default department cannot be deleted.'

# Ticket errors
ERROR_TICKET_NOT_FOUND = 'Ticket with key {ticket_key} not found'
ERROR_TICKET_NO_PRODUCTS = 'There are not products on the ticket!'

# Associate code errors
ERROR_ASSOCIATE_NOT_FOUND = 'Associate code {code} not found'
ERROR_ASSOCIATE_PARENT_NOT_FOUND = 'Parent product not found'

# Validation errors
ERROR_MISSING_CODE = 'Not code sended.'
ERROR_INVALID_CANTITY = 'Cantity must be greater than zero.'
ERROR_INVALID_INVENTORY = 'Inventory cannot be zero or lower.'
ERROR_INSUFFICIENT_INVENTORY = 'Inventory insuficient for product! {code}, {description}'
ERROR_NOT_ENOUGH_INVENTORY = 'Not enough inventory for product with code: {code}'
ERROR_NO_INVENTORY_TRACKING = 'Product with code {code} not found or does not track inventory'

# ============================================================================
# HTTP Status Messages
# ============================================================================

MSG_PRODUCT_CREATED = 'product created'
MSG_PRODUCT_UPDATED = 'product updated'
MSG_PRODUCT_DELETED = 'product deleted'
MSG_INVENTORY_UPDATED = 'inventory updated'

MSG_DEPARTMENT_CREATED = 'department created'
MSG_DEPARTMENT_UPDATED = 'department updated'
MSG_DEPARTMENT_DELETED = 'department deleted'

MSG_ASSOCIATE_CREATED = 'associate product created'
MSG_ASSOCIATE_UPDATED = 'associate product updated'
MSG_ASSOCIATE_DELETED = 'associate product deleted'

MSG_TICKET_SAVED = 'ticket saved'

MSG_UNEXPECTED_ERROR = 'Unexpected error'
MSG_CONFLICT_EXISTS = 'A product with that code already exists'

# ============================================================================
# Database Constants
# ============================================================================

# Default values
DEFAULT_PRIORITY = 0
DEFAULT_COST = 0
DEFAULT_SALE_PRICE = 0
DEFAULT_WHOLESALE_PRICE = 0
DEFAULT_PROFIT_MARGIN = 0

# ============================================================================
# Logging Constants
# ============================================================================

# Log file names
LOG_FILE_BACKEND = 'app-back.log'

# Log sanitization
MAX_LOG_LENGTH = 200
MAX_LOG_ITEMS = 10
MAX_LOG_VALUE_LENGTH = 100

# ============================================================================
# Printer Constants
# ============================================================================

# Default printer port
PRINTER_SERVICE_PORT = 9100
PRINTER_SERVICE_HOST = 'localhost'

# ============================================================================
# Environment Variable Names
# ============================================================================

ENV_SECRET_KEY = 'SECRET_KEY'
ENV_JWT_SECRET_KEY = 'JWT_SECRET_KEY'
ENV_TOKEN_HOURS = 'TOKEN_HOURS'
ENV_DB_PATH = 'DB_PATH'
ENV_HOST = 'HOST'
ENV_PORT = 'PORT'
ENV_DEBUG = 'DEBUG'
ENV_LOGGING = 'LOGGING'
ENV_ALLOWED_ORIGINS = 'ALLOWED_ORIGINS'

# ============================================================================
# Default Environment Values
# ============================================================================

DEFAULT_TOKEN_HOURS = 8
DEFAULT_DB_PATH = './db/conner.db'
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5000
DEFAULT_DEBUG = True
DEFAULT_LOGGING = True
DEFAULT_ALLOWED_ORIGINS = 'http://localhost:4200'
