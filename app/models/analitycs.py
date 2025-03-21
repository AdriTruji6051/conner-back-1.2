from app.connections.connections import DB_manager
from app.models.utyls import raise_exception_if_missing_keys, execute_sql_and_close_db, build_create_sql_sequence

allowed_methods = ['POST', 'PUT', 'DELETE']
create_drawer_logs_keys = ['open_at', 'user_id', 'method', 'transaction_type', 'transaction_id']
create_products_changes_keys = ['code', 'cost', 'sale_price', 'wholesale_price', 'original_code', 'modified_at', 'method']

def raise_excepciton_if_invalid_drawer_log(data: dict):
    raise_exception_if_missing_keys(data, create_drawer_logs_keys, 'Create drawer_logs keys')

    if data['method'] not in allowed_methods:
        raise ValueError('Method value is not valid')    

class Analytics:
    class Drawer_logs:
        @staticmethod
        def get(id: int) -> dict:
            sql = 'SELECT * FROM drawer_logs WHERE id = ?;'
            db = DB_manager.get_analitycs_db()
            ans = db.execute(sql, [id]).fetchone()

            if not ans:
                raise Exception(f'Drawer log with the id {id} not exist')
            
            ans = dict(ans)
            DB_manager.close_analitycs_db()

            return ans
        
        @staticmethod
        def get_all() -> list[dict]:
            sql = 'SELECT * FROM drawer_logs;'
            db = DB_manager.get_analitycs_db()
            rows = db.execute(sql).fetchall()

            if not len(rows):
                raise Exception(f'Not drawer logs to show')
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            DB_manager.close_analitycs_db()
            
            return ans
        
        @staticmethod
        def create(data: dict):
            raise_excepciton_if_invalid_drawer_log(data)

            sql = build_create_sql_sequence('drawer_logs', create_drawer_logs_keys)
            params = [data[key] for key in create_drawer_logs_keys]

            execute_sql_and_close_db(sql, params, 'analytics')

    class Products_changes:
        def get(id):
            sql = 'SELECT * FROM product_changes WHERE id = ?;'
            db = DB_manager.get_analitycs_db()
            ans = db.execute(sql, [id]).fetchone()

            if not ans:
                raise Exception(f'Product changes log with the id {id} not exist')
            
            ans = dict(ans)
            DB_manager.close_analitycs_db()

            return ans
        
        def get_all() -> list[dict]:
            sql = 'SELECT * FROM product_changes;'
            db = DB_manager.get_analitycs_db()
            rows = db.execute(sql).fetchall()

            if not len(rows):
                raise Exception(f'Not product changes logs to show')
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            DB_manager.close_analitycs_db()
            
            return ans
        
        def create(data: dict):
            raise_exception_if_missing_keys(data, create_products_changes_keys, 'Create products_changes keys')
            sql = build_create_sql_sequence('products_changes', create_products_changes_keys)
            params = [data[key] for key in create_products_changes_keys]

            execute_sql_and_close_db(sql, params, 'analytics')