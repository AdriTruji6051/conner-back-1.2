from app.models.products import Products, QUICKSALE_CODE, COMMONSALE_CODE
from app.models.tickets import Tickets
from app.controlers.core_classes import product_ticket, ticket_info
from app.helpers.helpers import raise_exception_if_missing_keys, ValidationError, collect_missing_keys

import math

UNDEFINED_PROFIT_MARGIN = 0.20

def custom_round(number: float) -> float:
    return round(number * 2) / 2

def custom_floor(number) -> float:
    return math.floor(number * 10) / 10

def validate_common_product(product: dict):
    v = ValidationError()
    keys = ['code', 'description', 'sale_type', 'sale_price', 'cantity']
    v.errors.extend(collect_missing_keys(product, keys, 'common product'))
    if v.has_errors:
        raise v

    if product.get('cost', 0) < 0:
        v.add('cost', 'Must be greater than or equal to zero')

    if product.get('cost', 0) > product['sale_price']:
        v.add('sale_price', 'Must be greater than or equal to cost')

    if product.get('wholesale_price', 0) > product['sale_price']:
        v.add('sale_price', 'Must be greater than or equal to wholesale_price')

    if product['sale_type'] != 'U' and product['sale_type'] != 'D':
        v.add('sale_type', 'Must have a value of "U" or "D"')

    v.raise_if_errors()
    
class Ticket:
    """Individual bill manager"""
    __products: list[product_ticket]
    __total: float
    __discount: float
    __products_count: float
    __articles_count: int
    __is_discount_applied: bool
    __profit: float
    
    def __init__(self):
        self.__products = []
        self.__total = 0
        self.__discount = 0
        self.__products_count = 0
        self.__articles_count = 0
        self.__is_discount_applied = False
        self.__profit = 0

    def __calculate(self):
        self.__total = 0
        self.__discount = 0
        self.__products_count = 0
        self.__articles_count = 0

        for product in self.__products:
            self.__products_count += product['cantity']
            self.__total += product['sale_price'] * product['cantity']

            self.__discount += (
                (product['sale_price'] * product['cantity']) - 
                (product['wholesale_price'] * product['cantity'] 
                if product['wholesale_price'] 
                else product['sale_price'] * product['cantity'])
            )

            product['total_price'] = (
                product['sale_price'] * product['cantity']
                if not self.__is_discount_applied 
                else (
                    product['wholesale_price'] * product['cantity']
                    if product['wholesale_price'] 
                    else product['sale_price'] * product['cantity']
                )
            )

            product['profit'] = (

                product['total_price'] - (product['cost'] * product['cantity']) 
                if product['cost'] 
                else product['total_price'] * UNDEFINED_PROFIT_MARGIN 
            )

            self.__profit += product['profit']

        if self.__is_discount_applied:
           self.__total -= self.__discount
        else:
            self.__discount = 0

        self.__total = custom_round(self.__total)
        self.__discount = custom_round(self.__discount)       
        self.__products_count = custom_floor(self.__products_count)
        self.__articles_count = len(self.__products)       

    def add(self, product_code: str, cantity: float = 1):
        if cantity < 0:
            raise ValueError('Cantity must be greater than zero.')
        
        has_finded = False
        
        # Check if the product is already at the Ticket, if it, increment cantity. If not, search for the product.
        for i in range(len(self.__products)):
            if self.__products[i]['code'] == product_code:
                if self.__products[i]['inventory'] != None and self.__products[i]['inventory'] < self.__products[i]['cantity'] + cantity:
                    raise ValueError('Inventory is not enough!')
                    
                self.__products[i]['cantity'] += cantity
                has_finded = True
                break 
        
        if not has_finded:
            product = Products.get(product_code)
            if product['inventory'] != None and product['inventory'] < cantity:
                raise ValueError('Inventory is not enough!')
                
            product['cantity'] = cantity
            product = {key: product[key] for key in product_ticket.__annotations__ if key in product}
            self.__products.append(product)

        self.__calculate()

    def add_common(self, product: product_ticket):
        validate_common_product(product)
        product['inventory'] = None
        product = {key: product[key] for key in product_ticket.__annotations__ if key in product}

        self.__products.append(product)
        self.__calculate()
    
    def remove(self, product_code: str, cantity: float = 0):
        if cantity < 0:
            raise ValueError('Cantity must be greater than zero.')
        
        for i in range(len(self.__products)):
            if self.__products[i]['code'] == product_code:
                if cantity == 0:
                    self.__products.pop(i)
                else:
                    if self.__products[i]['cantity'] - cantity > 0:
                        self.__products[i]['cantity'] -= cantity
                    else: 
                        self.__products.pop(i)
                break
                    
        self.__calculate()
    
    def toogle_wholesale(self):
        self.__is_discount_applied = not self.__is_discount_applied
        self.__calculate()
    
    def get_info(self) -> ticket_info:
        return {
            'products': self.__products,
            'products_count': self.__products_count,
            'articles_count': self.__articles_count,
            'sub_total': self.__total,
            'discount': self.__discount,
            'wholesale_active': self.__is_discount_applied,
            'profit': self.__profit
        }
    
class Tickets_manager:
    ticket_id_new = 1
    tickets_dict = {}
    tickets_dict[0] = {
        'ipv4': '127.0.0.1',
        'ticket': Ticket(),
        'commonsale_counter': 0
    }

    def __get(self, ticket_key: int) -> Ticket:
        """Return the Ticket object in the has map whith ticket_key as key value"""
        try:
            return Tickets_manager.tickets_dict[ticket_key]['ticket']
        except KeyError:
            raise ValueError(f'Ticket with key {ticket_key} not found')

    def __reset(self, ticket_key: int):
        Tickets_manager.tickets_dict[ticket_key]['ticket'] = Ticket()
        Tickets_manager.tickets_dict[ticket_key]['commonsale_counter'] = 0
    
    def __get_next_commonsale_code(self, ticket_key: int) -> str:
        """Generate a unique temporary COMMONSALE code for the ticket"""
        counter = Tickets_manager.tickets_dict[ticket_key]['commonsale_counter']
        Tickets_manager.tickets_dict[ticket_key]['commonsale_counter'] = counter + 1
        return f'{COMMONSALE_CODE}_{counter + 1}'
    
    def __normalize_commonsale_products(self, products: list[dict]) -> list[dict]:
        """Convert all temporary COMMONSALE codes back to the original COMMONSALE_CODE"""
        normalized_products = []
        for product in products:
            normalized_product = product.copy()
            if normalized_product['code'].startswith(COMMONSALE_CODE):
                normalized_product['code'] = COMMONSALE_CODE
            normalized_products.append(normalized_product)
        return normalized_products
    
    def add(self, ipv4: str = '127.0.0.1') -> int:
        """Create a Ticket object and return his Key to access it."""
        Tickets_manager.tickets_dict[Tickets_manager.ticket_id_new] = {
            'ipv4': ipv4,
            'ticket': Ticket(),
            'commonsale_counter': 0
        }
        Tickets_manager.ticket_id_new += 1
        
        return Tickets_manager.ticket_id_new - 1

    def remove(self, ticket_key: int):
        Tickets_manager.tickets_dict.pop(ticket_key)

    def save(self, ticket_key: int, notes: str, total: float = 0,  ipv4: str = '127.0.0.1', user_id: int = 0, print_many: int = 0):
        """Save at database the Ticket object with the ticket_key and return the ticket id saved at the database"""
        ticket_info = self.__get(ticket_key).get_info()
        if len(ticket_info['products']) < 1: 
            raise ValueError('There are not products on the ticket!')

        # Normalize COMMONSALE products back to original code before saving
        ticket_info['products'] = self.__normalize_commonsale_products(ticket_info['products'])

        ticket_info['ipv4_sender'] = ipv4
        ticket_info['total'] = total
        ticket_info['notes'] = notes
        ticket_info['user_id'] = user_id

        ticket_id = Tickets.create(ticket_info)

        for _ in range(print_many):
            print # TODO Add logic to send tickket to printer and send ticket_infor obj

        self.__reset(ticket_key)
        
        return ticket_id

    def get_keys(self, ipv4: str = '127.0.0.1') -> set:
        """Return all keys by default. If ipv4 is specified return only the tickets with that ipv4"""
        keys = set(Tickets_manager.tickets_dict)
        if ipv4 == '127.0.0.1':
            return keys
        
        keys_ipv4 = set()
        for key in keys:
            if Tickets_manager.tickets_dict[key]['ipv4'] == ipv4:
                keys_ipv4.add(key)

        return keys_ipv4
    
    def get_ticket_info(self, ticket_key: int) -> ticket_info:
        ticket = self.__get(ticket_key)
        return ticket.get_info()
    
    def add_product(self, ticket_key: int, product_code: str, cantity: int = 1):
        """Append or update product cantity from Ticket object with given ticket_key, if a cantity is not given, increment by one."""
        ticket = self.__get(ticket_key)
        ticket.add(product_code, cantity)
        return self.get_ticket_info(ticket_key)

    def remove_product(self, ticket_key: int, product_code: str, cantity: int = 0):
        """Remove from Ticket object with given ticket_key, the given product code and cantity. If cantity not specified all the product cantity will be removed."""
        ticket = self.__get(ticket_key)
        ticket.remove(product_code, cantity)
        return self.get_ticket_info(ticket_key)
    
    def toogle_ticket_wholesale(self, ticket_key: int):
        """Change between True or False in discount operations. Recalculate all the total in base in wholesale price or sale price"""
        ticket = self.__get(ticket_key)
        ticket.toogle_wholesale()
        return ticket.get_info()
    
    def add_common_product(self, ticket_key: int, price: float, cantity: float = 1, description: str = 'COMMONSALE'):
        """Add a COMMONSALE product with custom price and quantity to the ticket.
        
        Each COMMONSALE product gets a unique temporary code (COMMONSALE_1, COMMONSALE_2, etc.) 
        in the ticket to allow multiple different COMMONSALE products as separate line items.
        When the ticket is saved, all temporary codes are normalized back to COMMONSALE_CODE
        in the database, preserving each product's unique price, quantity, and description.
        """
        v = ValidationError()
        if price is None or price <= 0:
            v.add('price', 'Must be greater than zero')
        if cantity is None or cantity <= 0:
            v.add('cantity', 'Must be greater than zero')
        v.raise_if_errors()
        
        price = custom_floor(price)
        cantity = custom_floor(cantity)
        
        # Generate unique temporary code for this COMMONSALE product
        unique_code = self.__get_next_commonsale_code(ticket_key)
        
        common_product = {
            'code': unique_code,
            'description': description,
            'sale_type': 'U',
            'cost': custom_floor(price - (price * UNDEFINED_PROFIT_MARGIN)),
            'sale_price': price,
            'wholesale_price': price,
            'cantity': cantity,
            'inventory': None,
        }
        
        ticket = self.__get(ticket_key)
        ticket.add_common(common_product)
        return self.get_ticket_info(ticket_key)
    
    def quicksale(self, amount: float, ipv4: str = '127.0.0.1', user_id: int = 0):
        """ Create a new ticket with a single product with the amount of quicksale and save it."""
        amount = custom_floor(amount)
        quicksale_info = {
            'products': [
                {
                    'code': QUICKSALE_CODE,
                    'description': 'QUICKSALE',
                    'sale_type': 'U',
                    'cost': custom_floor(amount - (amount * UNDEFINED_PROFIT_MARGIN)),
                    'sale_price': amount,
                    'wholesale_price': amount,
                    'cantity': 1,
                    'inventory': 0,
                    'total_price': amount,
                    'profit': custom_floor(amount * UNDEFINED_PROFIT_MARGIN),
                }
            ],
            'products_count': 1,
            'articles_count': 1,
            'sub_total': amount,
            'discount': 0,
            'wholesale_active': False,
            'profit': custom_floor(amount * UNDEFINED_PROFIT_MARGIN),
            'ipv4_sender': ipv4,
            'total': amount,
            'notes': '',
            'user_id': user_id
        }

        return Tickets.create(quicksale_info)