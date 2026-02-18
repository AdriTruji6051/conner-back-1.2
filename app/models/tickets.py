from datetime import datetime
from flask import g

from app.connections.connections import DB_manager
from app.models.products import Products
from app.models.utyls import execute_sql_and_close_db, raise_exception_if_missing_keys, build_insert_sql_sequence, build_update_sql_sequence
from app.models.core_classes import ticket_create
from app.models.analytics import Analytics

create_ticket_keys = ['sub_total', 'total',  'discount', 'profit', 'products_count', 'notes', 'user_id', 'ipv4_sender', 'id']
create_product_in_tickets_keys = ['code' , 'description', 'cantity', 'profit', 'wholesale_price', 'sale_price', 'ticket_id']
update_ticket_keys = ['sub_total', 'total', 'discount', 'profit', 'products_count', 'id']
update_product_in_tickets_keys = ['cantity', 'profit', 'id']

def raise_exception_if_ticket_invalid_data(data: dict, is_update: bool = False):
    if not is_update:
        raise_exception_if_missing_keys(data, create_ticket_keys[:len(create_ticket_keys)-1] + ['products'], 'ticket create data')
    else:
        raise_exception_if_missing_keys(data, update_ticket_keys + ['products'], 'ticket update data')

    if data['products_count'] < 0:
        raise ValueError(f'Articles count must be greater than zero in data: {data}')
    
    if data['sub_total'] < 0:
        raise ValueError(f'Sub total must be greater than zero in data: {data}')
    
    if data['total'] < 0:
        raise ValueError(f'Total must be greater than zero in data: {data}')
    
    if data['discount'] < 0:
        raise ValueError(f'Discount must be greater than zero in data: {data}')
    
    if data['profit'] < 0:
        raise ValueError(f'Profit must be greater than zero in data: {data}')
    
    if data['total'] < data['sub_total']:
        raise ValueError(f'Total must be greater or equal than sub_total: {data}')
    
    if len(data['products']) == 0:
        raise ValueError(f'Products were not sended in data: {data}')
    
    
def raise_exception_if_product_in_ticket_invalid_data(data_array: list[dict], is_update: bool = False):
    for data in data_array:
        if not is_update:
            raise_exception_if_missing_keys(data, create_product_in_tickets_keys[:len(create_product_in_tickets_keys)-1], 'product_in_ticket create data')
            if data['wholesale_price'] < 0: 
                raise ValueError(f'Used wholesale price must be greater than zero in data: {data}')
            if data['sale_price'] < 0: 
                raise ValueError(f'Used price must be greater than zero in data: {data}')
        else:
            raise_exception_if_missing_keys(data, update_product_in_tickets_keys, 'product_in_ticket update data')
        
        if data['profit'] < 0: 
            raise ValueError(f'Used wholesale price must be greater than zero in data: {data}')
        if data['cantity'] < 0: 
            raise ValueError(f'Used price must be greater than zero in data: {data}')
        


class Tickets:
    @staticmethod
    def get(ticket_id: int) -> dict:
        sql = 'SELECT * tickets WHERE id = ?;'
        ticket = DB_manager.get_main_db().execute(sql, [ticket_id]).fetchone()

        if not ticket:
            raise ValueError("Ticket id not exists.")

        ticket['products'] = Tickets.Product_in_ticket.get_by_ticket(ticket_id)

        return ticket

    @staticmethod
    def list_created_at(date: str) -> list[dict]:
        sql = 'SELECT * FROM tickets WHERE created_at LIKE ? OR modified_at LIKE ?;'
        rows = DB_manager.get_main_db().execute(sql, [f'{date}%', f'{date}%']).fetchall()
        
        ans = []

        for row in rows:
            ans.append(dict(row))

        return ans

    @staticmethod
    def create(data: ticket_create) -> int:
        raise_exception_if_ticket_invalid_data(data, False)
        try:
            ticket_id = dict(DB_manager.get_main_db().execute('SELECT MAX (id) FROM tickets;').fetchone())['MAX (id)']
            ticket_id = ticket_id + 1 if ticket_id != None else 1 
            data['id'] = ticket_id

            sql = build_insert_sql_sequence('tickets', create_ticket_keys + ['created_at'])
            params = [data[key] for key in create_ticket_keys]
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            Tickets.Product_in_ticket.create(data['products'], ticket_id)

            execute_sql_and_close_db(sql, params, 'main')

            log = {
                'open_at': datetime.now().strftime('%Y-%m-%d'),
                'user_id': 0,
                'method': 'POST',
                'transaction_type': 1,
                'transaction_id': ticket_id
            }
            
            Analytics.Drawer_logs.create(log)

            return ticket_id
        
        except Exception as e:
            Tickets.delete(ticket_id)
            raise e
        finally:
            DB_manager.close_main_db()
    
    @staticmethod
    def update(data: dict):
        raise_exception_if_ticket_invalid_data(data, True)
        try:
            ticket_id = data['id']

            sql_keys = update_ticket_keys[:len(update_ticket_keys) - 1]
            sql = build_update_sql_sequence('tickets', sql_keys, 'id')
            params = [data[key] for key in update_ticket_keys]
            
            Tickets.Product_in_ticket.update(data['products'], ticket_id)

            execute_sql_and_close_db(sql, params, 'main')
            
            return ticket_id
        
        except Exception as e:
            raise e
        finally:
            DB_manager.close_main_db()
    
    @staticmethod
    def delete(ticket_id: int):
        Tickets.Product_in_ticket.delete_by_ticket(ticket_id)

        sql = 'DELETE FROM tickets WHERE id = ?;'
        execute_sql_and_close_db(sql, [ticket_id], 'main')
    
    # Product_in_ticket Subclass --------------->
    class Product_in_ticket:
        @staticmethod
        def get(code: int, ticket_id) -> dict:
            sql = 'SELECT * FROM product_in_ticket WHERE code = ? AND ticket_id = ?;'
            product = DB_manager.get_main_db().execute(sql, [code, ticket_id]).fetchone()
            
            if not product:
                raise ValueError(f'Not product_in_ticket with code: {code} and ticket id {ticket_id} found.')
            
            return dict(product)
        
        @staticmethod
        def get_by_ticket(ticket_id: int) -> list[dict]:
            sql = 'SELECT * FROM product_in_ticket WHERE ticket_id = ?;'
            rows = DB_manager.get_main_db().execute(sql, [ticket_id]).fetchall()
            
            ans = []

            for row in rows:
                ans.append(dict(row))

            return ans
            
        @staticmethod
        def create(data: list[dict], ticket_id: int):
            raise_exception_if_product_in_ticket_invalid_data(data, False)
            create_params = []

            # check if the inventory is valid for substract
            for prod in data:
                if Products.enough_inventory(prod['code'], prod['cantity']):
                    create_params.append((prod['code'], prod['cantity']))
                else:
                    raise ValueError(f'The product {prod["code"]}, {prod["description"]} not have the enough inventory for create.')

            for params in create_params:
                Products.remove_inventory(params[0], params[1])

            sql = build_insert_sql_sequence('product_in_ticket', create_product_in_tickets_keys)

            params_keys = create_product_in_tickets_keys[:len(create_product_in_tickets_keys) - 1]

            params = []

            for prod in data:
                prod_params = [prod[key] for key in params_keys]
                prod_params.append(ticket_id)
                params.append(prod_params)
            
            execute_sql_and_close_db(sql, params, 'main_db', True, False)
            

        @staticmethod
        def update(data: dict, ticket_id: int):
            raise_exception_if_product_in_ticket_invalid_data(data, True)

            update_params = []

            # check if the inventory is valid for substract
            # and if it's previous on ticket, increase or decrease 
            # the inventory

            for prod in data:
                query_inventory
                try:
                    query_inventory = Tickets.Product_in_ticket.get(prod['code'], ticket_id)['inventory']
                except:
                    continue
                
                update_cantity = (query_inventory - prod['cantity'])
                
                if Products.enough_inventory(prod['code'], update_cantity):
                    update_params.append((prod['code'], update_cantity))
                else:
                    raise ValueError(f'The product {prod["code"]}, {prod["description"]} not have the enough inventory for update.')

            for params in update_params:
                if params[1] < 0:
                    Products.remove_inventory(params[0], params[1] * - 1)
                else:
                    Products.add_inventory(params[0], params[1])

            sql = build_update_sql_sequence('product_in_ticket', update_product_in_tickets_keys, 'id')

            for prod in data:
                params = [prod[key] for key in update_product_in_tickets_keys]
                execute_sql_and_close_db(sql, params, 'main')
        
        @staticmethod
        def delete(id: int):
            sql = 'SELECT code, cantity FROM product_in_ticket WHERE id = ?;'
            product = dict(DB_manager.get_main_db().execute(sql, [id]).fetchone())

            if not product:
                return
            
            Products.add_inventory(product['code'], product['cantity'])

            sql = 'DELETE FROM product_in_ticket WHERE id = ?;'
            execute_sql_and_close_db(sql, [id], 'main')
        
        @staticmethod
        def delete_by_ticket(ticket_id: int):
            products_to_delete = Tickets.Product_in_ticket.get_by_ticket(ticket_id)
            for product in products_to_delete:
                Tickets.Product_in_ticket.delete(product['id'])