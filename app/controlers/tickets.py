from app.models.products import Products
from app.models.tickets import Tickets
from app.controlers.core_classes import product_ticket, ticket_info
from app.models.utyls import raise_exception_if_missing_keys

import math

UNDEFINED_PROFIT_MARGIN = 0.20

def custom_round(number: float):
    return round(number * 2) / 2

def custom_floor(number):
    return math.floor(number * 10) / 10

def validate_common_product(product: dict):
    keys = ['code', 'description', 'TEST2-2-U', 'sale_type', 'cost', 'sale_price', 'wholesale_price', 'cantity']
    raise_exception_if_missing_keys(product, keys, 'common product')

    if(product['cost'] < 0):
        raise ValueError('product sended is invalid -> Cost must be greater than zero')
    
    if(product['cost'] > product['sale_price']):
        raise ValueError('product sended is invalid -> sale_price must be greater than cost')
    
    if(product['wholesale_price'] > product['sale_price']): 
        raise ValueError('product sended is invalid -> sale_price must be greater than wholesale_price')
    
    if(product['sale_type'] != 'U' and product['sale_type'] != 'D'):
        raise ValueError('product sended is invalid -> sale_type must have values of "U" or "D"')
    
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
        self.__products = list()
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
        
        for i in range(len(self.__products)):
            if self.__products[i]['code'] == product_code:
                if self.__products[i]['inventory'] != None:
                    if self.__products[i]['inventory'] < self.__products[i]['inventory'] + cantity:
                        raise ValueError('Inventory is not enough!')
                    
                self.__products[i]['cantity'] += cantity
                has_finded = True
                break 
        
        if not has_finded:
            product = Products.get(product_code)
            if product['inventory'] != None:
                if product['inventory'] < cantity:
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
    tickets_dict = dict()
    tickets_dict[0] = {
        'ipv4': '127.0.0.1',
        'ticket': Ticket()
    }

    def __get(self, ticket_key: int) -> Ticket:
        """Return the Ticket object in the has map whith ticket_key as key value"""
        return Tickets_manager.tickets_dict[ticket_key]['ticket']

    def __reset(self, ticket_key: int):
        Tickets_manager.tickets_dict[ticket_key]['ticket'] = Ticket()
    
    def add(self, ipv4: str = '127.0.0.1') -> int:
        """Create a Ticket object and return his Key to access it."""
        Tickets_manager.tickets_dict[Tickets_manager.ticket_id_new] = {
            'ipv4': ipv4,
            'ticket': Ticket()
        }
        Tickets_manager.ticket_id_new += 1
        
        return Tickets_manager.ticket_id_new - 1

    def remove(self, ticket_key: int):
        Tickets_manager.tickets_dict.pop(ticket_key)

    def save(self, ticket_key: int, notes: str, total: float = 0,  ipv4: str = '127.0.0.1', user_id: int = 0, print_many: int = 0):
        """Save at database the Ticket object with the ticket_key and return the ticket id saved at the database"""
        ticket_info = self.__get(ticket_key).get_info()
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
    
    def quicksale(self, amount: float, ipv4: str = '127.0.0.1', user_id: int = 0):
        """ Create a new ticket with a single product with the amount of quicksale and save it."""
        quicksale_info = {
            'products': [
                {
                    'code': 'QUICKSALE',
                    'description': 'QUICKSALE',
                    'sale_type': 'U',
                    'cost': amount - (amount * UNDEFINED_PROFIT_MARGIN),
                    'sale_price': amount,
                    'wholesale_price': amount,
                    'cantity': 1,
                    'inventory': 0,
                    'total_price': amount,
                    'profit': amount * UNDEFINED_PROFIT_MARGIN,
                }
            ],
            'products_count': 1,
            'articles_count': 1,
            'sub_total': amount,
            'discount': 0,
            'wholesale_active': False,
            'profit': amount * UNDEFINED_PROFIT_MARGIN,
            'ipv4_sender': ipv4,
            'total': amount,
            'notes': '',
            'user_id': user_id
        }

        return Tickets.create(quicksale_info)