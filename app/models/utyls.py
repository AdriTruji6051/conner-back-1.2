from app.connections.connections import DB_manager
from flask import g

def build_insert_sql_sequence(table_name: str, values: list[str]) -> str:
    return f'INSERT INTO {table_name} ({', '.join(values)}) values ({', '.join(['?'] * len(values))});'

def build_update_sql_sequence(table_name: str, values: list[str], where_value: str) -> str:
    return f'UPDATE {table_name} SET {' = ?, '.join(values)} = ? WHERE {where_value} = ?;'

def raise_exception_if_missing_keys(data: dict, keys: list[str], description_tag: str):
    if not set(keys).issubset(data):
        missing = set(keys) - set(data)
        raise KeyError(f'Keys {missing} are missing in {description_tag}')
    
def execute_sql_and_close_db(sql: str, params: list, data_base: str, execute_many: bool = False, foreign_keys: bool = True, commit: bool = True) -> None:
    allowed_data_bases = ['analytics', 'config', 'main', 'main_db']
    
    if data_base not in allowed_data_bases:
        raise Exception('Specified data_base value is not allowed')
    
    db = object()
        
    if data_base == allowed_data_bases[0]:
        db = DB_manager.get_analitycs_db()   

    elif data_base == allowed_data_bases[1]:
        db = DB_manager.get_config_db()
        db.execute("PRAGMA foreign_keys = ON;")

    elif data_base == allowed_data_bases[2] or data_base == allowed_data_bases[3]:
        db = DB_manager.get_main_db()
        
        if foreign_keys:
            db.execute("PRAGMA foreign_keys = ON;")
        
    try:
        if execute_many:
            db.executemany(sql, params)
            
        else:
            db.execute(sql, params)
        if commit:
            db.commit()
    except Exception as e:
        raise Exception(f"Couldn't execute sql sequence: {sql}. With params: {params}. In the {data_base} database. ERROR: {e}")
    finally:
        DB_manager.close_main_db
        DB_manager.close_analitycs_db()
        DB_manager.get_config_db()
