from datetime import datetime
from app.models.core_classes import drawer_log, drawer_log_create, product_changes, cash_flow

from app.connections.connections import DB_manager
from app.models.utyls import raise_exception_if_missing_keys, execute_sql_and_close_db, build_insert_sql_sequence

allowed_methods = ['POST', 'PUT', 'DELETE']
create_drawer_logs_keys = ['open_at', 'user_id', 'method', 'transaction_type', 'transaction_id']
create_products_changes_keys = ['code', 'cost', 'sale_price', 'wholesale_price', 'original_code', 'modified_at', 'method']
create_cash_flow_keys = ['description', 'amount', 'date', 'in_or_out', 'is_payment']

def raise_excepciton_if_invalid_drawer_log(data: dict):
    raise_exception_if_missing_keys(data, create_drawer_logs_keys, 'Create drawer_logs keys')

    if data['method'] not in allowed_methods:
        raise ValueError('Method value is not valid')    

class Analytics:
    class Drawer_logs:
        @staticmethod
        def get(id: int) -> drawer_log:
            sql = 'SELECT * FROM drawer_logs WHERE id = ?;'
            db = DB_manager.get_analitycs_db()
            ans = db.execute(sql, [id]).fetchone()

            if not ans:
                raise Exception(f'Drawer log with the id {id} not exist')
            
            ans = dict(ans)
            DB_manager.close_analitycs_db()

            return ans
        
        @staticmethod
        def get_all(date: str) -> list[drawer_log]:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')

            sql = 'SELECT * FROM drawer_logs WHERE open_at LIKE ?;'
            db = DB_manager.get_analitycs_db()
            rows = db.execute(sql, [f'{date}%']).fetchall()

            if not len(rows):
                return list()
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            DB_manager.close_analitycs_db()
            
            return ans
        
        @staticmethod
        def create(data: drawer_log_create):
            raise_excepciton_if_invalid_drawer_log(data)

            sql = build_insert_sql_sequence('drawer_logs', create_drawer_logs_keys)
            params = [data[key] for key in create_drawer_logs_keys]

            execute_sql_and_close_db(sql, params, 'analytics')

    class Products_changes:
        @staticmethod
        def get(id) -> product_changes:
            sql = 'SELECT * FROM product_changes WHERE id = ?;'
            db = DB_manager.get_analitycs_db()
            ans = db.execute(sql, [id]).fetchone()

            if not ans:
                raise Exception(f'Product changes log with the id {id} not exist')
            
            ans = dict(ans)
            DB_manager.close_analitycs_db()

            return ans
        
        @staticmethod
        def get_all(date: str, exclude_delete: bool = True) -> list[product_changes]:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')

            if exclude_delete:
                sql = "SELECT * FROM product_changes WHERE modified_at LIKE ? AND method != 'DELETE';"
            else:                
                sql = 'SELECT * FROM product_changes WHERE modified_at LIKE ?;'

            db = DB_manager.get_analitycs_db()
            rows = db.execute(sql, [f'{date}%']).fetchall()

            if not len(rows):
                return list()
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            DB_manager.close_analitycs_db()
            
            return ans
        
        @staticmethod
        def create(data: dict):
            raise_exception_if_missing_keys(data, create_products_changes_keys, 'Create products_changes keys')
            sql = build_insert_sql_sequence('products_changes', create_products_changes_keys)
            params = [data[key] for key in create_products_changes_keys]

            execute_sql_and_close_db(sql, params, 'analytics')

    class Cash_flow:
        @staticmethod
        def get(id: int) -> cash_flow:
            sql = 'SELECT * FROM cash_flow WHERE id = ?;'
            db = DB_manager.get_analitycs_db()
            ans = db.execute(sql, [id]).fetchone()

            if not ans:
                raise Exception(f'Cash_flow with the id {id} not exist')
            
            ans = dict(ans)
            DB_manager.close_analitycs_db()

            return ans

        @staticmethod
        def get_date(date: str) -> list[cash_flow]:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')

            sql = 'SELECT * FROM cash_flow WHERE date LIKE ?;'
            db = DB_manager.get_analitycs_db()
            rows = db.execute(sql, [f'{date}%']).fetchall()

            if not len(rows):
                return list()
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            DB_manager.close_analitycs_db()
            
            return ans
        
        @staticmethod
        def insert(amount: float, in_or_out: int, is_payment: int = 0, description: str = 'None'):
            """ Amount of money. 1 if inflow, 0 if outflow. 1 if is payment 0 if not. """
            if amount < 0:
                raise ValueError('Amount must be greater than zero!')
            if in_or_out not in [0,1]:
                raise ValueError('In_or_out must have a value of 1 or 0!')
            if is_payment not in [0,1]:
                raise ValueError('Is_payment must have a value of 1 or 0!') 

            sql = build_insert_sql_sequence('cash_flow', create_cash_flow_keys)
            params = [
                description, amount, datetime.now().strftime('%Y-%m-%d'), in_or_out, is_payment
            ]

            execute_sql_and_close_db(sql, params, 'analytics')
        