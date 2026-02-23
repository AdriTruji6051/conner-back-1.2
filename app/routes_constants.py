"""
Routes Constants
This module contains all API route constants used throughout the application.
Routes are organized by domain with base paths concatenated for better maintainability.
"""

# ===================== BASE PATHS =====================
API_BASE = '/api'

# ===================== PRODUCTS ROUTES =====================
PRODUCTS_BASE = f'{API_BASE}/product'

# Products - Get
ROUTE_GET_PRODUCT_BY_CODE = f'{PRODUCTS_BASE}/code/<string:code>'
ROUTE_GET_PRODUCT_BY_DESCRIPTION = f'{PRODUCTS_BASE}/description/<string:description>'
ROUTE_GET_PRODUCT_SIBLINGS = f'{PRODUCTS_BASE}/siblings/<string:code>'

# Products - Create/Update/Delete
ROUTE_CREATE_PRODUCT = f'{PRODUCTS_BASE}/create'
ROUTE_UPDATE_PRODUCT = f'{PRODUCTS_BASE}/update'
ROUTE_DELETE_PRODUCT = f'{PRODUCTS_BASE}/delete/<string:code>'

# Products - Inventory Management
ROUTE_UPDATE_INVENTORY = f'{PRODUCTS_BASE}/<string:code>/update/inventory/<float:cantity>'
ROUTE_ADD_INVENTORY = f'{PRODUCTS_BASE}/<string:code>/add/inventory/<float:cantity>'
ROUTE_REMOVE_INVENTORY = f'{PRODUCTS_BASE}/<string:code>/remove/inventory/<float:cantity>'

# ===================== PRODUCT DEPARTMENTS ROUTES =====================
DEPARTMENTS_BASE = f'{PRODUCTS_BASE}/departments'

ROUTE_GET_ALL_DEPARTMENTS = DEPARTMENTS_BASE
ROUTE_GET_DEPARTMENT = f'{DEPARTMENTS_BASE}/<int:code>'
ROUTE_CREATE_DEPARTMENT = f'{DEPARTMENTS_BASE}/create/<string:description>'
ROUTE_UPDATE_DEPARTMENT = f'{DEPARTMENTS_BASE}/update/<string:code>/description/<int:description>'
ROUTE_DELETE_DEPARTMENT = f'{DEPARTMENTS_BASE}/delete/<int:code>'

# ===================== PRODUCT ASSOCIATES ROUTES =====================
ASSOCIATES_BASE = f'{PRODUCTS_BASE}/associates'

ROUTE_GET_ASSOCIATES_RAW_DATA = f'{ASSOCIATES_BASE}/parent/<string:parent_code>'
ROUTE_CREATE_ASSOCIATE = f'{ASSOCIATES_BASE}/create'
ROUTE_UPDATE_ASSOCIATE = f'{ASSOCIATES_BASE}/update'
ROUTE_DELETE_ASSOCIATE = f'{ASSOCIATES_BASE}/delete/<string:code>'

# ===================== TICKETS ROUTES =====================
TICKETS_BASE = f'{API_BASE}/ticket'

# Tickets - Quick Sale & Create
ROUTE_QUICKSALE_TICKET = f'{TICKETS_BASE}/quicksale/<amount>'
ROUTE_CREATE_TICKET = f'{TICKETS_BASE}/new'

# Tickets - Get
ROUTE_GET_TICKET_KEYS = f'{TICKETS_BASE}/get/keys'
ROUTE_GET_TICKET_KEYS_SHARED = f'{TICKETS_BASE}/get/keys/shared'
ROUTE_GET_TICKET = f'{TICKETS_BASE}/get/<int:key>'
ROUTE_GET_TICKETS_BY_DATE = f'{TICKETS_BASE}/get/date/<string:date>'
ROUTE_GET_PRODUCTS_IN_TICKET = f'{TICKETS_BASE}/get/products/id/<int:id>'

# Tickets - Manage
ROUTE_TOOGLE_WHOLESALE = f'{TICKETS_BASE}/toogle/wholesale/<int:ticket_key>'
ROUTE_ADD_PRODUCT_TICKET = f'{TICKETS_BASE}/add'
ROUTE_ADD_COMMON_PRODUCT_TICKET = f'{TICKETS_BASE}/add/common'
ROUTE_REMOVE_PRODUCT_TICKET = f'{TICKETS_BASE}/remove'
ROUTE_SAVE_TICKET = f'{TICKETS_BASE}/save'

# ===================== CONFIG ROUTES =====================
CONFIG_BASE = f'{API_BASE}/config'

# Config - Users
USERS_CONFIG_BASE = f'{CONFIG_BASE}/user'

ROUTE_GET_USERS = USERS_CONFIG_BASE
ROUTE_LOGIN_USER = f'{USERS_CONFIG_BASE}/login'
ROUTE_CREATE_USER = f'{USERS_CONFIG_BASE}/create'
ROUTE_UPDATE_USER = f'{USERS_CONFIG_BASE}/update'
ROUTE_DELETE_USER = f'{USERS_CONFIG_BASE}/delete/<int:id>'

# Config - Ticket Text (Headers, Footers, Fonts)
TICKET_TEXT_BASE = f'{CONFIG_BASE}/ticket/text'

ROUTE_GET_HEADERS = f'{TICKET_TEXT_BASE}/headers'
ROUTE_UPDATE_HEADERS = f'{TICKET_TEXT_BASE}/headers/update'
ROUTE_GET_FOOTERS = f'{TICKET_TEXT_BASE}/footers'
ROUTE_UPDATE_FOOTERS = f'{TICKET_TEXT_BASE}/footers/update'

# Config - Ticket Fonts
TICKET_FONTS_BASE = f'{CONFIG_BASE}/ticket/fonts'

ROUTE_GET_FONTS = TICKET_FONTS_BASE
ROUTE_CREATE_FONT = f'{TICKET_FONTS_BASE}/create'

# ===================== PRINTERS ROUTES =====================
PRINT_BASE = f'{API_BASE}/print'

ROUTE_LIST_PRINTERS = f'{PRINT_BASE}/list'
ROUTE_DICT_PRINTERS = f'{PRINT_BASE}/dict'
ROUTE_UPDATE_PRINTER = f'{PRINT_BASE}/update/<string:printer>'

# ===================== ANALYTICS ROUTES =====================
ANALYTICS_BASE = f'{API_BASE}'

# Analytics - Cash Flow
ROUTE_INSERT_CASH_INFLOW = f'{ANALYTICS_BASE}/cash/inflow'
ROUTE_INSERT_CASH_OUTFLOW = f'{ANALYTICS_BASE}/cash/outflow'
ROUTE_INSERT_CASH_PAYMENT = f'{ANALYTICS_BASE}/cash/payment'

# Analytics - Drawer Logs
DRAWER_LOG_BASE = f'{ANALYTICS_BASE}/drawer/log'

ROUTE_GET_DRAWER_LOG = f'{DRAWER_LOG_BASE}/<int:id>'
ROUTE_GET_DRAWER_LOG_BY_DATE = f'{DRAWER_LOG_BASE}/date/<string:date>'

# Analytics - Product Changes
PRODUCT_LOG_BASE = f'{ANALYTICS_BASE}/product/log/changes'

ROUTE_GET_PRODUCT_CHANGES = f'{PRODUCT_LOG_BASE}/<int:id>'
ROUTE_GET_PRODUCT_CHANGES_BY_DATE = f'{PRODUCT_LOG_BASE}/date/<string:date>'

# ===================== TEMPLATES ROUTES =====================
ROUTE_INDEX = '/'
ROUTE_DASHBOARD = '/dashboard'
ROUTE_DYNAMIC_PATH = '/<path:path>'
ROUTE_DASHBOARD_DYNAMIC_PATH = '/dashboard/<path:path>'
