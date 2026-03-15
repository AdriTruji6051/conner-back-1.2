from datetime import datetime

from app.extensions import db
from app.models.products import Products, QUICKSALE_CODE, COMMONSALE_CODE
from app.models.core_classes import TicketModel, ProductInTicket
from app.models.analytics import Analytics
from app.helpers.helpers import raise_exception_if_missing_keys, ValidationError, collect_missing_keys

create_ticket_keys = ['sub_total', 'total', 'discount', 'profit', 'products_count', 'notes', 'user_id', 'ipv4_sender']
create_product_in_tickets_keys = ['code', 'description', 'cantity', 'profit', 'wholesale_price', 'sale_price']
update_ticket_keys = ['sub_total', 'total', 'discount', 'profit', 'products_count', 'id']
update_product_in_tickets_keys = ['cantity', 'profit', 'id']

_GTE_ZERO_MSG = 'Must be greater than or equal to zero'


def raise_exception_if_ticket_invalid_data(data: dict, is_update: bool = False):
    v = ValidationError()

    if not is_update:
        v.errors.extend(collect_missing_keys(data, create_ticket_keys + ['products'], 'ticket create data'))
    else:
        v.errors.extend(collect_missing_keys(data, update_ticket_keys + ['products'], 'ticket update data'))

    # If required keys are missing we cannot safely inspect values
    if v.has_errors:
        raise v

    if data['products_count'] < 0:
        v.add('products_count', _GTE_ZERO_MSG)

    if data['sub_total'] < 0:
        v.add('sub_total', _GTE_ZERO_MSG)

    if data['total'] < 0:
        v.add('total', _GTE_ZERO_MSG)

    if data['discount'] < 0:
        v.add('discount', _GTE_ZERO_MSG)

    if data['profit'] < 0:
        v.add('profit', _GTE_ZERO_MSG)

    if data['total'] < data['sub_total']:
        v.add('total', 'Must be greater than or equal to sub_total')

    if len(data['products']) == 0:
        v.add('products', 'At least one product is required')

    v.raise_if_errors()


def raise_exception_if_product_in_ticket_invalid_data(data_array: list[dict], is_update: bool = False):
    v = ValidationError()

    for idx, data in enumerate(data_array):
        prefix = f'products[{idx}].'
        if not is_update:
            v.errors.extend(
                {prefix + k: msg for k, msg in err.items()}
                for err in collect_missing_keys(data, create_product_in_tickets_keys, 'product_in_ticket create data')
            )
        else:
            v.errors.extend(
                {prefix + k: msg for k, msg in err.items()}
                for err in collect_missing_keys(data, update_product_in_tickets_keys, 'product_in_ticket update data')
            )

        # Only check values if the keys exist
        if not is_update:
            if 'wholesale_price' in data and data['wholesale_price'] < 0:
                v.add(f'{prefix}wholesale_price', _GTE_ZERO_MSG)
            if 'sale_price' in data and data['sale_price'] < 0:
                v.add(f'{prefix}sale_price', _GTE_ZERO_MSG)

        if 'profit' in data and data['profit'] < 0:
            v.add(f'{prefix}profit', _GTE_ZERO_MSG)
        if 'cantity' in data and data['cantity'] < 0:
            v.add(f'{prefix}cantity', _GTE_ZERO_MSG)

    v.raise_if_errors()


class Tickets:
    @staticmethod
    def get(ticket_id: int) -> TicketModel:
        ticket = TicketModel.query.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket id not exists.")
        return ticket

    @staticmethod
    def list_created_at(date: str) -> list[TicketModel]:
        tickets = TicketModel.query.filter(
            db.or_(
                TicketModel.created_at.like(f'{date}%'),
                TicketModel.modified_at.like(f'{date}%')
            )
        ).all()
        return tickets

    @staticmethod
    def create(data: dict) -> int:
        raise_exception_if_ticket_invalid_data(data, False)
        try:
            ticket = TicketModel(
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                sub_total=data['sub_total'],
                total=data['total'],
                discount=data['discount'],
                profit=data['profit'],
                products_count=data['products_count'],
                notes=data['notes'],
                user_id=data['user_id'],
                ipv4_sender=data['ipv4_sender'],
            )
            db.session.add(ticket)
            db.session.flush()  # Get the auto-generated id

            ticket_id = ticket.id

            Tickets.Product_in_ticket.create(data['products'], ticket_id)

            db.session.commit()

            log = {
                'open_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': 0,
                'method': 'POST',
                'transaction_type': 1,
                'transaction_id': ticket_id
            }

            Analytics.Drawer_logs.create(log)

            return ticket_id

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update(data: dict):
        raise_exception_if_ticket_invalid_data(data, True)
        try:
            ticket_id = data['id']
            ticket = TicketModel.query.get(ticket_id)
            if not ticket:
                raise ValueError(f'Ticket with id {ticket_id} not found')

            ticket.sub_total = data['sub_total']
            ticket.total = data['total']
            ticket.discount = data['discount']
            ticket.profit = data['profit']
            ticket.products_count = data['products_count']
            ticket.modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            Tickets.Product_in_ticket.update(data['products'], ticket_id)

            db.session.commit()

            return ticket_id

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete(ticket_id: int):
        Tickets.Product_in_ticket.delete_by_ticket(ticket_id)

        ticket = TicketModel.query.get(ticket_id)
        if ticket:
            db.session.delete(ticket)
            db.session.commit()

    class Product_in_ticket:
        @staticmethod
        def get(code: str, ticket_id: int) -> ProductInTicket:
            product = ProductInTicket.query.filter_by(code=code, ticket_id=ticket_id).first()
            if not product:
                raise ValueError(f'Not product_in_ticket with code: {code} and ticket id {ticket_id} found.')
            return product

        @staticmethod
        def get_by_ticket(ticket_id: int) -> list[ProductInTicket]:
            return ProductInTicket.query.filter_by(ticket_id=ticket_id).all()

        @staticmethod
        def create(data: list[dict], ticket_id: int):
            raise_exception_if_product_in_ticket_invalid_data(data, False)

            # Check inventory and prepare removals
            for prod in data:
                if not Products.enough_inventory(prod['code'], prod['cantity']):
                    raise ValueError(f'The product {prod["code"]}, {prod["description"]} not have the enough inventory for create.')

            # Remove inventory
            for prod in data:
                Products.remove_inventory(prod['code'], prod['cantity'])

            # Create product_in_ticket records
            for prod in data:
                pit = ProductInTicket(
                    ticket_id=ticket_id,
                    code=prod['code'],
                    description=prod['description'],
                    cantity=prod['cantity'],
                    profit=prod.get('profit'),
                    wholesale_price=prod.get('wholesale_price'),
                    sale_price=prod['sale_price'],
                )
                db.session.add(pit) 

            # Don't commit here — the caller (Tickets.create) will commit

        @staticmethod
        def update(data: list[dict], ticket_id: int):
            raise_exception_if_product_in_ticket_invalid_data(data, True)

            for prod in data:
                try:
                    existing = ProductInTicket.query.filter_by(code=prod.get('code'), ticket_id=ticket_id).first()
                    if not existing:
                        continue

                    old_cantity = existing.cantity
                    new_cantity = prod['cantity']
                    diff = old_cantity - new_cantity

                    if diff < 0:
                        # Need more inventory
                        if not Products.enough_inventory(prod['code'], abs(diff)):
                            raise ValueError(f'The product {prod["code"]} not have the enough inventory for update.')
                        Products.remove_inventory(prod['code'], abs(diff))
                    elif diff > 0:
                        # Return inventory
                        Products.add_inventory(prod['code'], diff)

                except ValueError:
                    raise
                except Exception:
                    continue

            # Update the product_in_ticket records
            for prod in data:
                pit = ProductInTicket.query.get(prod['id'])
                if pit:
                    pit.cantity = prod['cantity']
                    pit.profit = prod['profit']

            # Don't commit — caller handles it

        @staticmethod
        def delete(id: int):
            pit = ProductInTicket.query.get(id)
            if not pit:
                return

            Products.add_inventory(pit.code, pit.cantity)

            db.session.delete(pit)
            db.session.commit()

        @staticmethod
        def delete_by_ticket(ticket_id: int):
            products_to_delete = Tickets.Product_in_ticket.get_by_ticket(ticket_id)
            for product in products_to_delete:
                Products.add_inventory(product.code, product.cantity)
                db.session.delete(product)
            db.session.commit()

    @staticmethod
    def modify(data: dict):
        """Modify an already-saved ticket in the database.
        
        Each product in data['products'] must have an 'action' field:
        - 'keep': No changes to this product.
        - 'update': Update cantity, profit, sale_price, wholesale_price, description.
        - 'add': Add a new product to the ticket.
        - 'remove': Remove the product from the ticket.
        
        Inventory adjustments are made for products that track inventory.
        Products with code=None (deleted), QUICKSALE, or COMMONSALE skip inventory checks.
        """
        raise_exception_if_ticket_invalid_data(data, True)
        raise_exception_if_modify_product_invalid_data(data['products'])

        try:
            ticket_id = data['id']
            ticket = TicketModel.query.get(ticket_id)
            if not ticket:
                raise ValueError(f'Ticket with id {ticket_id} not found')

            # Process each product action
            for prod in data['products']:
                action = prod['action']

                if action == 'keep':
                    continue

                elif action == 'remove':
                    pit = ProductInTicket.query.get(prod['id'])
                    if not pit:
                        continue
                    if _should_adjust_inventory(pit.code):
                        Products.add_inventory(pit.code, pit.cantity)
                    db.session.delete(pit)

                elif action == 'update':
                    pit = ProductInTicket.query.get(prod['id'])
                    if not pit:
                        continue

                    old_cantity = pit.cantity
                    new_cantity = prod['cantity']
                    diff = new_cantity - old_cantity

                    if diff != 0 and _should_adjust_inventory(pit.code):
                        if diff > 0:
                            if not Products.enough_inventory(pit.code, diff):
                                raise ValueError(
                                    f'Not enough inventory for product {pit.code} '
                                    f'(need {diff} more)'
                                )
                            Products.remove_inventory(pit.code, diff)
                        else:
                            Products.add_inventory(pit.code, abs(diff))

                    pit.cantity = new_cantity
                    pit.profit = prod.get('profit', pit.profit)
                    pit.sale_price = prod.get('sale_price', pit.sale_price)
                    pit.wholesale_price = prod.get('wholesale_price', pit.wholesale_price)
                    pit.description = prod.get('description', pit.description)

                elif action == 'add':
                    code = prod['code']
                    cantity = prod['cantity']

                    if _should_adjust_inventory(code):
                        if not Products.enough_inventory(code, cantity):
                            raise ValueError(
                                f'Not enough inventory for product {code} '
                                f'(need {cantity})'
                            )
                        Products.remove_inventory(code, cantity)

                    pit = ProductInTicket(
                        ticket_id=ticket_id,
                        code=code,
                        description=prod['description'],
                        cantity=cantity,
                        profit=prod.get('profit'),
                        wholesale_price=prod.get('wholesale_price'),
                        sale_price=prod['sale_price'],
                    )
                    db.session.add(pit)

            # Update ticket header
            ticket.sub_total = data['sub_total']
            ticket.total = data['total']
            ticket.discount = data['discount']
            ticket.profit = data['profit']
            ticket.products_count = data['products_count']
            if 'notes' in data:
                ticket.notes = data['notes']
            ticket.modified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            db.session.commit()

            log = {
                'open_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': 0,
                'method': 'PUT',
                'transaction_type': 1,
                'transaction_id': ticket_id
            }
            Analytics.Drawer_logs.create(log)

            return ticket_id

        except Exception as e:
            db.session.rollback()
            raise e


_VALID_ACTIONS = ('keep', 'update', 'add', 'remove')


def _should_adjust_inventory(code: str | None) -> bool:
    """Return True if inventory should be adjusted for the given product code.
    Skip for None (deleted product), QUICKSALE, or COMMONSALE codes."""
    if code is None:
        return False
    if code in (QUICKSALE_CODE, COMMONSALE_CODE):
        return False
    return True


def raise_exception_if_modify_product_invalid_data(data_array: list[dict]):
    """Validate the products array for the modify-ticket endpoint."""
    v = ValidationError()

    for idx, prod in enumerate(data_array):
        prefix = f'products[{idx}].'

        if 'action' not in prod:
            v.add(f'{prefix}action', 'Missing required field')
            continue

        action = prod['action']
        if action not in _VALID_ACTIONS:
            v.add(f'{prefix}action', f'Must be one of {_VALID_ACTIONS}')
            continue

        if action == 'keep':
            if 'id' not in prod:
                v.add(f'{prefix}id', 'Missing required field for keep action')

        elif action == 'remove':
            if 'id' not in prod:
                v.add(f'{prefix}id', 'Missing required field for remove action')

        elif action == 'update':
            for key in ('id', 'cantity', 'profit'):
                if key not in prod:
                    v.add(f'{prefix}{key}', 'Missing required field for update action')
            if 'cantity' in prod and prod['cantity'] < 0:
                v.add(f'{prefix}cantity', 'Must be greater than or equal to zero')
            if 'profit' in prod and prod['profit'] < 0:
                v.add(f'{prefix}profit', 'Must be greater than or equal to zero')
            if 'sale_price' in prod and prod['sale_price'] < 0:
                v.add(f'{prefix}sale_price', 'Must be greater than or equal to zero')

        elif action == 'add':
            for key in ('code', 'description', 'cantity', 'sale_price'):
                if key not in prod:
                    v.add(f'{prefix}{key}', 'Missing required field for add action')
            if 'cantity' in prod and prod['cantity'] < 0:
                v.add(f'{prefix}cantity', 'Must be greater than or equal to zero')
            if 'sale_price' in prod and prod['sale_price'] < 0:
                v.add(f'{prefix}sale_price', 'Must be greater than or equal to zero')
            if 'profit' in prod and prod['profit'] is not None and prod['profit'] < 0:
                v.add(f'{prefix}profit', 'Must be greater than or equal to zero')

    v.raise_if_errors()