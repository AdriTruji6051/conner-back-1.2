from app.models.products import Products, QUICKSALE_CODE, COMMONSALE_CODE
from app.models.tickets import Tickets
from app.controlers.core_classes import product_ticket, ticket_info, editor_entry
from app.controlers.printers import Printers
from app.helpers.helpers import ValidationError, collect_missing_keys

from datetime import datetime
import math

UNDEFINED_PROFIT_MARGIN = 0.20

def custom_round(number: float) -> float:
    return round(number * 2) / 2

def custom_floor(number) -> float:
    return math.floor(number * 10) / 10

def format_to_two_decimals(number: float) -> float:
    """Round and format a number to 2 decimal places to prevent floating-point precision errors."""
    return round(number, 2)

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
            # Round total_price to 2 decimal places to prevent floating-point precision errors
            product['total_price'] = format_to_two_decimals(product['total_price'])

            product['profit'] = (
                product['total_price'] - (product['cost'] * product['cantity']) 
                if product['cost'] 
                else product['total_price'] * UNDEFINED_PROFIT_MARGIN 
            )
            # Round profit to 2 decimal places
            product['profit'] = format_to_two_decimals(product['profit'])

            self.__profit += product['profit']

        if self.__is_discount_applied:
           self.__total -= self.__discount
        else:
            self.__discount = 0

        self.__total = format_to_two_decimals(custom_round(self.__total))
        self.__discount = format_to_two_decimals(custom_round(self.__discount))
        self.__profit = format_to_two_decimals(self.__profit)
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
        # Format product values to .2f
        formatted_products = []
        for product in self.__products:
            formatted_product = product.copy()
            formatted_product['cantity'] = format_to_two_decimals(formatted_product['cantity'])
            formatted_product['cost'] = format_to_two_decimals(formatted_product['cost'])
            formatted_product['sale_price'] = format_to_two_decimals(formatted_product['sale_price'])
            formatted_product['wholesale_price'] = format_to_two_decimals(formatted_product['wholesale_price'])
            # Apply custom_round to total_price to match sub_total rounding consistency
            formatted_product['total_price'] = format_to_two_decimals(custom_round(formatted_product['total_price']))
            formatted_product['profit'] = format_to_two_decimals(formatted_product['profit'])
            if 'inventory' in formatted_product and formatted_product['inventory'] is not None:
                formatted_product['inventory'] = format_to_two_decimals(formatted_product['inventory'])
            formatted_products.append(formatted_product)
        
        return {
            'products': formatted_products,
            'products_count': format_to_two_decimals(self.__products_count),
            'articles_count': self.__articles_count,
            'sub_total': format_to_two_decimals(self.__total),
            'discount': format_to_two_decimals(self.__discount),
            'wholesale_active': self.__is_discount_applied,
            'profit': format_to_two_decimals(self.__profit)
        }
    
class tickets_manager:
    ticket_id_new = 1
    tickets_dict = {}
    tickets_dict[0] = {
        'ipv4': '127.0.0.1',
        'ticket': Ticket(),
        'commonsale_counter': 0,
        'editors': []
    }

    def __get(self, ticket_key: int) -> Ticket:
        """Return the Ticket object in the has map whith ticket_key as key value"""
        try:
            return tickets_manager.tickets_dict[ticket_key]['ticket']
        except KeyError:
            raise ValueError(f'Ticket with key {ticket_key} not found')

    def __reset(self, ticket_key: int):
        tickets_manager.tickets_dict[ticket_key]['ticket'] = Ticket()
        tickets_manager.tickets_dict[ticket_key]['commonsale_counter'] = 0
        tickets_manager.tickets_dict[ticket_key]['editors'] = []
    
    def __track_editor(self, ticket_key: int, ipv4: str, user_id: int, action: str):
        """Record or update the editor entry for a given ipv4 + user_id on this ticket."""
        editors: list[editor_entry] = tickets_manager.tickets_dict[ticket_key]['editors']
        timestamp = datetime.now().isoformat()

        for editor in editors:
            if editor['ipv4'] == ipv4 and editor['user_id'] == user_id:
                editor['last_action'] = action
                editor['timestamp'] = timestamp
                return

        editors.append({
            'ipv4': ipv4,
            'user_id': user_id,
            'last_action': action,
            'timestamp': timestamp
        })
    
    def __get_next_commonsale_code(self, ticket_key: int) -> str:
        """Generate a unique temporary COMMONSALE code for the ticket"""
        counter = tickets_manager.tickets_dict[ticket_key]['commonsale_counter']
        tickets_manager.tickets_dict[ticket_key]['commonsale_counter'] = counter + 1
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
        tickets_manager.tickets_dict[tickets_manager.ticket_id_new] = {
            'ipv4': ipv4,
            'ticket': Ticket(),
            'commonsale_counter': 0,
            'editors': []
        }
        tickets_manager.ticket_id_new += 1
        
        return tickets_manager.ticket_id_new - 1

    def remove(self, ticket_key: int):
        tickets_manager.tickets_dict.pop(ticket_key)

    def save(self, ticket_key: int, notes: str, total: float = 0, ipv4: str = '127.0.0.1', user_id: int = 0, print_many: int = 0, printer_name: str = None):
        """Save at database the Ticket object with the ticket_key and return the ticket id saved at the database"""
        self.__track_editor(ticket_key, ipv4, user_id, 'save')
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

        if print_many > 0 and printer_name:
            printers = Printers()
            printers.print_ticket(ticket_info, ticket_id, notes, printer_name, ipv4, print_many)

        self.__reset(ticket_key)
        
        return ticket_id

    def get_keys(self, ipv4: str = '127.0.0.1') -> set:
        """Return all keys by default. If ipv4 is specified return only the tickets with that ipv4"""
        keys = set(tickets_manager.tickets_dict)
        if ipv4 == '127.0.0.1':
            return keys
        
        keys_ipv4 = set()
        for key in keys:
            if tickets_manager.tickets_dict[key]['ipv4'] == ipv4:
                keys_ipv4.add(key)

        return keys_ipv4
    
    def get_ticket_info(self, ticket_key: int) -> ticket_info:
        ticket = self.__get(ticket_key)
        info = ticket.get_info()
        info['editors'] = list(tickets_manager.tickets_dict[ticket_key]['editors'])
        return info
    
    def add_product(self, ticket_key: int, product_code: str, cantity: int = 1, ipv4: str = '127.0.0.1', user_id: int = 0):
        """Append or update product cantity from Ticket object with given ticket_key, if a cantity is not given, increment by one."""
        ticket = self.__get(ticket_key)
        ticket.add(product_code, cantity)
        self.__track_editor(ticket_key, ipv4, user_id, 'add_product')
        return self.get_ticket_info(ticket_key)

    def remove_product(self, ticket_key: int, product_code: str, cantity: int = 0, ipv4: str = '127.0.0.1', user_id: int = 0):
        """Remove from Ticket object with given ticket_key, the given product code and cantity. If cantity not specified all the product cantity will be removed."""
        ticket = self.__get(ticket_key)
        ticket.remove(product_code, cantity)
        self.__track_editor(ticket_key, ipv4, user_id, 'remove_product')
        return self.get_ticket_info(ticket_key)
    
    def toogle_ticket_wholesale(self, ticket_key: int, ipv4: str = '127.0.0.1', user_id: int = 0):
        """Change between True or False in discount operations. Recalculate all the total in base in wholesale price or sale price"""
        ticket = self.__get(ticket_key)
        ticket.toogle_wholesale()
        self.__track_editor(ticket_key, ipv4, user_id, 'toogle_wholesale')
        return self.get_ticket_info(ticket_key)
    
    def add_common_product(self, ticket_key: int, price: float, cantity: float = 1, description: str = 'COMMONSALE', ipv4: str = '127.0.0.1', user_id: int = 0):
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
        self.__track_editor(ticket_key, ipv4, user_id, 'add_common_product')
        return self.get_ticket_info(ticket_key)
    
    def set_product_quantity(self, ticket_key: int, product_code: str, quantity: float, ipv4: str = '127.0.0.1', user_id: int = 0):
        """Override the quantity of an existing product in the ticket with the given quantity.
        
        This replaces the entire quantity (not add/subtract like add_product).
        If the product doesn't exist in the ticket, raises ValueError.
        """
        v = ValidationError()
        if quantity is None or quantity <= 0:
            v.add('quantity', 'Must be greater than zero')
        v.raise_if_errors()
        
        ticket = self.__get(ticket_key)
        products = ticket._Ticket__products  # Access private products list
        
        # Find the product in the ticket
        product_found = False
        for product in products:
            if product['code'] == product_code:
                product_found = True
                # Check inventory constraints if applicable
                if product['inventory'] is not None and product['inventory'] < quantity:
                    raise ValueError('Inventory is not enough!')
                # Set the new quantity directly (override)
                product['cantity'] = quantity
                break
        
        if not product_found:
            raise ValueError(f'Product with code {product_code} not found in ticket {ticket_key}')
        
        # Recalculate ticket totals
        ticket._Ticket__calculate()
        self.__track_editor(ticket_key, ipv4, user_id, 'set_product_quantity')
        return self.get_ticket_info(ticket_key)
    
    def set_product_wholesale_price(self, ticket_key: int, product_code: str, wholesale_price: float, ipv4: str = '127.0.0.1', user_id: int = 0):
        """Update wholesale price for an existing product in the ticket only."""
        v = ValidationError()
        if wholesale_price is None or wholesale_price <= 0:
            v.add('wholesale_price', 'Must be greater than zero')
        v.raise_if_errors()

        ticket = self.__get(ticket_key)
        products = ticket._Ticket__products
        product_found = False

        for product in products:
            if product['code'] == product_code:
                product_found = True
                cost = product.get('cost')
                if cost is not None and wholesale_price <= cost:
                    raise ValueError('Wholesale price must be greater than cost')
                product['wholesale_price'] = custom_floor(wholesale_price)
                break

        if not product_found:
            raise ValueError(f'Product with code {product_code} not found in ticket {ticket_key}')

        ticket._Ticket__calculate()
        self.__track_editor(ticket_key, ipv4, user_id, 'set_product_wholesale_price')
        return self.get_ticket_info(ticket_key)
        """Override the quantity of an existing product in the ticket with the given quantity.
        
        This replaces the entire quantity (not add/subtract like add_product).
        If the product doesn't exist in the ticket, raises ValueError.
        """
        v = ValidationError()
        if quantity is None or quantity <= 0:
            v.add('quantity', 'Must be greater than zero')
        v.raise_if_errors()
        
        ticket = self.__get(ticket_key)
        products = ticket._Ticket__products  # Access private products list
        
        # Find the product in the ticket
        product_found = False
        for product in products:
            if product['code'] == product_code:
                product_found = True
                # Check inventory constraints if applicable
                if product['inventory'] is not None and product['inventory'] < quantity:
                    raise ValueError('Inventory is not enough!')
                # Set the new quantity directly (override)
                product['cantity'] = quantity
                break
        
        if not product_found:
            raise ValueError(f'Product with code {product_code} not found in ticket {ticket_key}')
        
        # Recalculate ticket totals
        ticket._Ticket__calculate()
        self.__track_editor(ticket_key, ipv4, user_id, 'set_product_quantity')
        return self.get_ticket_info(ticket_key)
    
    def quicksale(self, amount: float, ipv4: str = '127.0.0.1', user_id: int = 0, printer_name: str = None):
        """ Create a new ticket with a single product with the amount of quicksale and save it."""
        amount = custom_floor(amount)
        profit_amount = custom_floor(amount * UNDEFINED_PROFIT_MARGIN)
        cost_amount = custom_floor(amount - profit_amount)
        
        quicksale_info = {
            'products': [
                {
                    'code': QUICKSALE_CODE,
                    'description': 'QUICKSALE',
                    'sale_type': 'U',
                    'cost': format_to_two_decimals(cost_amount),
                    'sale_price': format_to_two_decimals(amount),
                    'wholesale_price': format_to_two_decimals(amount),
                    'cantity': 1.0,
                    'inventory': 0.0,
                    'total_price': format_to_two_decimals(amount),
                    'profit': format_to_two_decimals(profit_amount),
                }
            ],
            'products_count': 1.0,
            'articles_count': 1,
            'sub_total': format_to_two_decimals(amount),
            'discount': 0.0,
            'wholesale_active': False,
            'profit': format_to_two_decimals(profit_amount),
            'ipv4_sender': ipv4,
            'total': format_to_two_decimals(amount),
            'notes': '',
            'user_id': user_id
        }

        ticket = Tickets.create(quicksale_info)
        print(printer_name) # TODO Add logic to send tickket to printer and send ticket_infor obj

        return ticket