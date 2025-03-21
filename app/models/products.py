from datetime import datetime

from app.connections.connections import DB_manager
from app.helpers.helpers import profit_percentage
from app.models.utyls import raise_exception_if_missing_keys, execute_sql_and_close_db

# 'modified_at' is not included in data keys because is calculated into the functions
create_product_keys = ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "parent_code"]
update_product_keys = ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "parent_code", "original_code"]
update_department_keys = ["description", "code"]
create_associates_codes_keys = ["code", "parent_code", "tag"]
update_associates_codes_keys = ["code", "parent_code", "tag", "original_code"]
update_siblings_keys = ["sale_type", "cost", "sale_price", "department", "wholesale_price",  "parent_code"]



def update_siblings_products(data: dict, siblings_codes: list[str]):
    if len(siblings_codes):
        for sibling_code in siblings_codes:
            ans = Products.get(sibling_code)
            if ans:
                for key in update_siblings_keys:
                    ans[key] = data[key]
                Products.update(ans)
            else:
                continue     

# raise an error if data is not valid
def product_data_is_valid(data: dict, check_update_product_keys: bool = False) -> None:

    raise_exception_if_missing_keys(data, create_product_keys, 'create product')
    
    if check_update_product_keys:
        raise_exception_if_missing_keys(data, update_product_keys, 'update product')
    
    if(data['cost'] < 0):
        raise ValueError('Data sended is invalid -> Cost must be greater than zero')
    
    if(data['cost'] > data['sale_price']):
        raise ValueError('Data sended is invalid -> sale_price must be greater than cost')
    
    if(data['wholesale_price'] > data['sale_price']): 
        raise ValueError('Data sended is invalid -> sale_price must be greater than wholesale_price')
    
    if(data['sale_type'] != 'U' and data['sale_type'] != 'D'):
        raise ValueError('Data sended is invalid -> sale_type must have values of "U" or "D"')

class Products:
    @staticmethod
    def get(code: str) -> dict:
        # Check if code is in associates codes (linked products to retrieve the parent data product),
        # if not, search if the product is the main product
        tag = '' # Used for linked products
        id_associate = code
        is_associate = False

        sql = 'SELECT * FROM associates_codes WHERE code = ?;'
        db = DB_manager.get_products_db()
        ans = db.execute(sql, [code]).fetchone()

        if ans:
            tag += ' ' + dict(ans)['tag']
            code = dict(ans)['parent_code']   
            is_associate = True

        sql = 'SELECT * FROM products WHERE code = ?;'
        
        ans = db.execute(sql, [code]).fetchone()
        if ans:
            ans = dict(ans)
            ans['description']+= tag
            ans['code'] = id_associate # if not associate found, code will be the original code
            ans['is_associate'] = is_associate
        else:
            raise Exception('Product not found')
            
        DB_manager.close_products_db()

        return ans
    
    @staticmethod
    def get_by_description(description: str, called_before: bool = False) -> list[dict]:
        db = DB_manager.get_products_db()
        description_split = description.split()

        # if description has several words, we will create a dinamyc search for include all
        # the words, alse if they are not ordered
        params = list()
        sql = 'SELECT * FROM products WHERE '

        if len(description_split) > 2:
            sql += 'description LIKE ? ORDER BY priority DESC, CASE WHEN description LIKE ? THEN 0 ELSE 1 END, description;'
            params.append(f'%{description}%')
            params.append(f'{description}%')

        else:
            # Structure for dynamic params in query
            for i in range(len(description_split)):
                sql += ' description LIKE ? AND ' if i+1 < len(description_split) else ' description LIKE ? '
                params.append(f'%{description_split[i]}%')
            # Final and static query structure
            sql += 'ORDER BY priority DESC, CASE WHEN description LIKE ? THEN 0 WHEN description LIKE ? THEN 1 ELSE 2 END, description;'
            params.append(f'{description}%')
            params.append(f'{description_split[0]}%')

        rows = db.execute(sql, params).fetchall()
        ans = list()

        for row in rows:
            ans.append(dict(row))

        # Change Ñ or ñ for better results in spanish searchs
        if 'ñ' in description and not called_before:
            ans.extend(Products.search_by_description(description.replace('ñ', 'Ñ'), True))
        elif 'Ñ' in description and not called_before:
            ans.extend(Products.search_by_description(description.replace('Ñ', 'ñ'), True))

        DB_manager.close_products_db()

        return ans
    
    @staticmethod
    def get_siblings(code: str) -> None:
        # check if parent product, if not, search his parent code, 
        # if not has anything linked, raise not found exception
        sql = 'SELECT * FROM products WHERE parent_code = ?;'
        db = DB_manager.get_products_db()
        siblings_rows = db.execute(sql, [code]).fetchall()

        if not len(siblings_rows):
            # 
            sql_child = 'SELECT parent_code FROM products WHERE code = ?;'
            child = db.execute(sql_child, [code]).fetchone()

            if not child:
                raise Exception('Product not exist')
            
            # check again, if the product has siblings 
            code = dict(child)['parent_code']
            siblings_rows = db.execute(sql, [code]).fetchall()
            
            if not len(siblings_rows):
                raise Exception('Product has not parent linked')
            
        childs = list()
        for row in siblings_rows:
            childs.append(dict(row))

        sql = 'SELECT * FROM products WHERE code = ?;'
        parent = dict(db.execute(sql, [code]))

        # print related products
        return {
            'parent_product' : parent,
            'child_products' : childs
        }

    @staticmethod
    def create(data: dict) -> None:
        product_data_is_valid(data)

        params = [data[key] for key in create_product_keys]

        # Profit and modifiet_at are calculated inside the server, they don't have to be sent by the client
        params.append(profit_percentage(data['cost'], data['sale_price']))
        params.append(datetime.now().strftime('%Y-%m-%d'))

        sql = """
            INSERT INTO products 
            (code, description, sale_type, cost, sale_price, department, wholesale_price, priority, inventory, parent_code, profit_margin, modified_at) 
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        execute_sql_and_close_db(sql, params, 'products')

        if 'siblings_codes' in data:
            update_siblings_products(data, data['siblings_codes'])

    @staticmethod
    def update(data: dict):
        product_data_is_valid(data=data, check_update_product_keys=True)
        
        # 'original_code' isn't used because it is appended at the last place
        params = [data[key] for key in create_product_keys[:len(update_product_keys) -1]]

        params.append(profit_percentage(data['cost'], data['sale_price']))
        params.append(datetime.now().strftime('%Y-%m-%d'))
        params.append(data['original_code'])

        sql = """
            UPDATE products SET code = ?, description = ?, sale_type = ?, cost = ?,  sale_price = ?, department = ?, 
            wholesale_price = ?, priority = ?, inventory = ?, parent_code = ?, profit_margin = ?, modified_at = ? 
            WHERE code = ?;
        """
        execute_sql_and_close_db(sql, params, 'products')

        if 'siblings_codes' in data:
            update_siblings_products(data, data['siblings_codes'])

    @staticmethod
    def delete(code: str) -> None:
        sql = 'DELETE FROM products WHERE code = ?;'
        execute_sql_and_close_db(sql, [code], 'products')
    
    class Departments:
        @staticmethod
        def get(code: str) -> dict:
            sql = 'SELECT * FROM departments WHERE code = ?;'
            db = DB_manager.get_products_db()
            ans = db.execute(sql, [code]).fetchone()

            if ans:
                ans = dict(ans)
            else:
                raise Exception('Not department finded')
            
            DB_manager.close_products_db()
            return ans
        
        @staticmethod
        def get_all() -> list[dict]:
            sql = 'SELECT * FROM departments;'
            db = DB_manager.get_products_db()
            rows = db.execute(sql).fetchall()
            ans = list()

            if rows:
                for row in rows:
                    ans.append(dict(row))
            else:
                raise Exception('Not department finded')
            
            DB_manager.close_products_db()
            return ans

        @staticmethod
        def create(description: str) -> None:
            sql = 'INSERT INTO departments (description) values (?);'
            execute_sql_and_close_db(sql, [description], 'products')

        @staticmethod
        def update(data: dict): 
            raise_exception_if_missing_keys(data, update_department_keys, 'update departments')
            params = [data[key] for key in update_department_keys]
            sql = 'UPDATE departments SET description = ? WHERE code = ?;'
            execute_sql_and_close_db(sql, params, 'products')
        
        @staticmethod
        def delete(code: str) -> None:
            sql = 'DELETE FROM departments WHERE code = ?;'
            execute_sql_and_close_db(sql, [code], 'products')
        
    class Associates_codes:
        @staticmethod
        def get(code: str) -> dict:
            sql = """
                SELECT ac.code, ac.parent_code, ac.tag, p.description, p.sale_type, p.cost, p.sale_price, 
                p.department, p.wholesale_price, p.priority, p.inventory, p.modified_at, p.profit_margin, 
                p.parent_code FROM associates_codes ac JOIN products p ON ac.parent_code = p.code 
                WHERE ac.code = ?;
            """
            db = DB_manager.get_products_db()
            ans = db.execute(sql, [code]).fetchone()

            if ans:
                ans = dict(ans)
                ans['is_associate'] = True
            else:
                raise Exception('Not associate_code finded')
            
            DB_manager.close_products_db()
            return ans

        @staticmethod
        def create(data: dict) -> None:
            raise_exception_if_missing_keys(data, create_associates_codes_keys, 'create associate_codes')
            
            params = [data[key] for key in create_associates_codes_keys]
            sql = 'INSERT INTO associates_codes (code, parent_code, tag) values (?, ?, ?);'

            execute_sql_and_close_db(sql, params, 'products')

        @staticmethod
        def update(data: dict) -> None:
            raise_exception_if_missing_keys(data, update_associates_codes_keys, 'create associate_codes')
            
            params = [data[key] for key in update_associates_codes_keys]
            sql = 'UPDATE associates_codes SET code = ?, parent_code = ?, tag = ? WHERE code = ?;'

            execute_sql_and_close_db(sql, params, 'products')
        
        @staticmethod
        def delete(code: str) -> None:
            sql = 'DELETE FROM associates_codes WHERE code = ?;'
            execute_sql_and_close_db(sql, [code], 'products')