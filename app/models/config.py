import bcrypt # check later

from app.connections.connections import DB_manager
from app.models.utyls import raise_exception_if_missing_keys, build_create_sql_sequence, build_update_sql_sequence, execute_sql_and_close_db

create_user_keys = ['user', 'user_name', 'password', 'role_type']
update_user_keys = ['user', 'user_name', 'password', 'role_type', 'id']

class Config:
    class Users:
        @staticmethod
        def get_all() -> list[dict]:
            sql = 'SELECT id, user, user_name, role_type FROM users;'
            db = DB_manager.get_config_db()
            rows = db.execute(sql).fetchall()

            if not len(rows):
                raise Exception('No users to show!')
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            DB_manager.close_config_db()

            return ans
        
        @staticmethod
        def login(user: str, password: str) -> dict:
            sql = 'SELECT * FROM users WHERE user = ?;'
            db = DB_manager.get_config_db()
            user = db.execute(sql, [user]).fetchone()

            if not user:
                raise Exception('User or password are incorrect!')
            
            user = dict(user)

            if not password == user['password']:
                raise Exception('User or password are incorrect!')
            
            DB_manager.close_config_db()

            return {
                'user' : user['user'],
                'user_name' : user['user_name'],
                'role_type' : user['role_type']
            }

        @staticmethod
        def create(data: dict):
            raise_exception_if_missing_keys(data, create_user_keys, 'create users data')
            sql = build_create_sql_sequence('users', create_user_keys)
            params = [data[key] for key in create_user_keys]
            execute_sql_and_close_db(sql, params, 'config')
        
        @staticmethod
        def update(data: dict):
            raise_exception_if_missing_keys(data, update_keys, 'create users data')
            update_keys = update_user_keys[:len(update_user_keys) - 1]

            sql = build_update_sql_sequence('users', update_keys, 'id')
            params = [data[key] for key in create_user_keys]
            execute_sql_and_close_db(sql, params, 'config')
        
        @staticmethod
        def delete(id: dict):
            sql = 'DELETE FROM users WHERE id = ?;'
            execute_sql_and_close_db(sql, [id])

    class Ticket_text:
        @staticmethod
        def insert_headers(data: list[dict]):
            return
        
        @staticmethod
        def insert_footers(data: list[dict]):
            return
        
        @staticmethod
        def drop_headers():
            return
        
        @staticmethod
        def drop_footers():
            return