from typing import TypedDict
from app.controlers.core_classes import product_ticket

class product_create(TypedDict):
    code: str
    description: str
    sale_type: str
    cost: float
    sale_price: float
    department: int
    wholesale_price: float
    priority: int
    inventory: float
    parent_code: str

class product(product_create):
    profit_margin: int
    modified_at: str
    is_associate: bool

class product_update(product_create):
    original_code: str

class associates_codes(TypedDict):
    code: str
    parent_code: str
    tag: str

class associates_codes_update(associates_codes):
    original_code: str

class siblings(TypedDict):
    parent_product: product
    child_products: list[product]

class department(TypedDict):
    code: int
    description: str

class user(TypedDict):
    id: int
    user: str
    user_name: str

class user_logged(TypedDict):
    user: str
    user_name: str
    role_type: str

class user_create(TypedDict):
    user: str
    user_name: str
    password: str
    role_type: str

class user_update(TypedDict):
    user: str
    user_name: str
    password: str
    role_type: str
    id: int

class create_text_ticket(TypedDict):
    text: str
    line: int
    is_header: int
    font_config: int

class text_ticket(TypedDict):
    text: str
    font: str
    size: int
    weigh: int
    line: int

class drawer_log(TypedDict):
    id: int
    open_at: str
    user_id: int
    method: str
    transaction_type: int
    transaction_id: object

class cash_flow(TypedDict):
    id: int
    description: str
    amount: float
    date: str
    in_or_out: int
    is_payment: int

class drawer_log_create(TypedDict):
    open_at: str
    user_id: int
    method: str
    transaction_type: int
    transaction_id: object

class product_changes(TypedDict):
    id: int
    code: str
    original_code: str
    cost: float
    sale_price: float
    wholesale_price: float
    modified_at: str
    method_str: str

class ticket_create(TypedDict):
    products: list[product_ticket]
    products_count: float
    sub_total: float
    discount: float
    profit: float

    ipv4_sender: str
    total: float
    notes: str
    user_id: int
