import datetime
from app.connections.connections import DB_manager

class Products:
    @staticmethod
    def create(data: dict):
        # 'modified_at' is not included in data keys because is calculated into this function
        keys = ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "profit_margin", "parent_code"]

        if set(keys).issubset(data):
            raise KeyError('Not all the keys were sented')

        params = [data[key] for key in keys]
        params.append(datetime.now().strftime('%Y-%m-%d'))

        sql = """
            INSERT INTO products 
            (code, description, sale_type, cost, sale_price, department, wholesale_price, priority, inventory, profit_margin, parent_code, modified_at) 
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        db = DB_manager.get_products_db()
        db.execute(sql, params)
        db.commit()
        DB_manager.close_products_db()
    
    def update(data: dict):
        # 'modified_at' is not included in data keys because is calculated into this function
        keys = ["description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "inventory", "profit_margin", "parent_code", "code", "priority", "original_code"]

        if set(keys).issubset(data):
            raise KeyError('Not all the keys were sented')

        # 'original_code' is poped to append at the last place
        keys.pop()

        params = [data[key] for key in keys]
        params.append(datetime.now().strftime('%Y-%m-%d'))
        params.append(data['original_code'])

        sql = """
            UPDATE products SET description = ?, sale_type = ?, cost = ?, sale_price = ?, department = ?, wholesale_price = ?, inventory = ?, profit_margin = ?, parent_code = ?, code = ?, priority = ?, modified_at = ? WHERE code = ?;
        """
        db = DB_manager.get_products_db()
        db.execute(sql, params)
        db.commit()
        DB_manager.close_products_db()

    @staticmethod
    def get_by_id(id: str) -> dict:
        sql = 'SELECT * FROM products WHERE code = ?;'
        db = DB_manager.get_products_db()
        ans = dict(db.execute(sql, [id]).fetchone())
        DB_manager.close_products_db()

        return ans
    
    @staticmethod
    def search_by_description(description: str, called_before: bool = False) -> list[dict]:
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