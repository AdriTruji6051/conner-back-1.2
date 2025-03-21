from app.connections.connections import DB_manager

def build_create_sql_sequence(table_name: str, values: list[str]) -> str:
    return f'INSERT INTO {table_name} ({', '.join(values)}) values ({', '.join(['?'] * len(values))});'

def build_update_sql_sequence(table_name: str, values: list[str], where_value: str) -> str:
    return f'UPDATE {table_name} SET {' = ?, '.join(values)} = ? WHERE {where_value} = ?;'

def raise_exception_if_missing_keys(data: dict, keys: list[str], tag: str):
    if not set(keys).issubset(data):
        missing = set(keys) - set(data)
        raise KeyError(f'Keys {missing} are missing in {tag}')
    
def execute_sql_and_close_db(sql: str, params: list, data_base: str) -> None:
    allowed_data_bases = ['products', 'analytics', 'config']
    
    if data_base not in allowed_data_bases:
        raise Exception('Specified data_base value is not allowed')
    
    if data_base == allowed_data_bases[0]:
        db = DB_manager.get_products_db()
        db.execute("PRAGMA foreign_keys = ON;")
        db.execute(sql, params)
        db.commit()
        DB_manager.close_products_db()

    elif data_base == allowed_data_bases[1]:
        db = DB_manager.get_analitycs_db()
        db.execute(sql, params)
        db.commit()
        DB_manager.close_analitycs_db()

    elif data_base == allowed_data_bases[2]:
        db = DB_manager.get_tickets_db()
        db.execute(sql, params)
        db.commit()
        DB_manager.close_tickets_db()