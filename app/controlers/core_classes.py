from typing import TypedDict

class product_ticket(TypedDict):
    code: str
    description: str
    sale_type: str
    cost: float
    sale_price: float
    wholesale_price: float
    cantity: float
    inventory: float
    total_price: float
    profit: float

class editor_entry(TypedDict):
    ipv4: str
    user_id: int
    last_action: str
    timestamp: str

class ticket_info(TypedDict):
    products: list[product_ticket]
    products_count: float
    articles_count: int
    sub_total: float
    discount: float
    wholesale_active: bool
    profit: float
    editors: list[editor_entry]