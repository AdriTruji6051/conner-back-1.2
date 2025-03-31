from typing import TypedDict

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

class drawer_log_create(TypedDict):
    open_at: str
    user_id: int
    method: str
    transaction_type: int
    transaction_id: object
