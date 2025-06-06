import bcrypt # TODO check later

from app.models.core_classes import user_create, user_update, user, user_logged, text_ticket, create_text_ticket, font_config

from app.connections.connections import DB_manager
from app.models.utyls import raise_exception_if_missing_keys, build_insert_sql_sequence, build_update_sql_sequence, execute_sql_and_close_db

create_user_keys = ['user', 'user_name', 'password', 'role_type']
update_user_keys = ['user', 'user_name', 'password', 'role_type', 'id']
create_text_keys = ['text', 'line', 'is_header', 'font_config']
create_font_config_keys = ['font', 'weigh', 'size']

class Config:
    class Users:
        @staticmethod
        def get_all() -> list[user]:
            sql = 'SELECT id, user, user_name, role_type FROM users;'
            db = DB_manager.get_config_db()
            rows = db.execute(sql).fetchall()

            if not len(rows):
                return []
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            DB_manager.close_config_db()

            return ans
        
        @staticmethod
        def login(user: str, password: str) -> user_logged:
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
                'id': user['id'],
                'user' : user['user'],
                'user_name' : user['user_name'],
                'role_type' : user['role_type']
            }

        @staticmethod
        def create(data: user_create):
            raise_exception_if_missing_keys(data, create_user_keys, 'create users data')
            sql = build_insert_sql_sequence('users', create_user_keys)
            params = [data[key] for key in create_user_keys]
            execute_sql_and_close_db(sql, params, 'config')
        
        @staticmethod
        def update(data: user_update):            
            update_keys = update_user_keys[:len(update_user_keys) - 1]
            raise_exception_if_missing_keys(data, update_user_keys, 'update users data')

            sql = build_update_sql_sequence('users', update_keys, 'id')
            params = [data[key] for key in update_user_keys]
            execute_sql_and_close_db(sql, params, 'config')
        
        @staticmethod
        def delete(id: int):
            sql = 'DELETE FROM users WHERE id = ?;'
            execute_sql_and_close_db(sql, [id], 'config')

    class Ticket_text:
        @staticmethod
        def raise_exception_if_text_not_valid(data: list[dict], is_header: bool = False):
            if not data:
                raise ValueError('Text array must have values, not be empty')
            try:
                for row in data:
                    row = dict(row)
                    raise_exception_if_missing_keys(row, create_text_keys, 'text_headers array' if is_header else 'text_footers array')

                    if not len(row['text']):
                        raise ValueError(f'Not text in row: {row}')
                    if row['line'] < 0:
                        raise ValueError(f'line value must be greater than zero in row: {row}')
                    if is_header and row['is_header'] != 1:
                        raise ValueError('If this line value is header, value is_header must be seated with value int(1)')
                    if not is_header and row['is_header'] != 0:
                        raise ValueError('If this line value is footer, value is_header must be seated with value int(0)')
                    if row['is_header'] not in [0,1]:
                        raise ValueError('Error, is_header value must be seated with int(0) or int(1)')
            except Exception as e:
                raise Exception(f'Invalid text, with ERROR: {e}')

        @staticmethod
        def get_headers() -> list[text_ticket]:
            sql = """
                SELECT tt.text, tt.line, tc.font, tc.size, tc.weigh, tt.font_config 
                FROM ticket_text tt JOIN ticket_font_configs tc 
                ON tt.font_config = tc.id 
                WHERE tt.is_header = 1 ORDER BY tt.line;
            """
            db = DB_manager.get_config_db()
            rows = db.execute(sql).fetchall()

            if not rows:
                return []
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            return ans
        
        @staticmethod
        def get_footers() -> list[text_ticket]:
            sql = """
                SELECT tt.text, tt.line, tc.font, tc.size, tc.weigh, tt.font_config 
                FROM ticket_text tt JOIN ticket_font_configs tc 
                ON tt.font_config = tc.id 
                WHERE tt.is_header = 0 ORDER BY tt.line;
            """
            db = DB_manager.get_config_db()
            rows = db.execute(sql).fetchall()

            if not rows:
                return []
            
            ans = list()
            for row in rows:
                ans.append(dict(row))

            return ans

        @staticmethod
        def update_headers(data: list[create_text_ticket]):
            Config.Ticket_text.raise_exception_if_text_not_valid(data, True)
            Config.Ticket_text.drop_headers()

            sql = build_insert_sql_sequence('ticket_text', create_text_keys)

            for row in data:
                params = [row[key] for key in create_text_keys]
                execute_sql_and_close_db(sql, params, 'config')
        
        @staticmethod
        def update_footers(data: list[create_text_ticket]):
            Config.Ticket_text.raise_exception_if_text_not_valid(data, False)
            Config.Ticket_text.drop_footers()

            sql = build_insert_sql_sequence('ticket_text', create_text_keys)

            for row in data:
                params = [row[key] for key in create_text_keys]
                execute_sql_and_close_db(sql, params, 'config')
        
        @staticmethod
        def drop_headers():
            sql = 'DELETE FROM ticket_text WHERE is_header = 1;'
            execute_sql_and_close_db(sql, [], 'config')
        
        @staticmethod
        def drop_footers():
            sql = 'DELETE FROM ticket_text WHERE is_header = 0;'
            execute_sql_and_close_db(sql, [], 'config')

        @staticmethod
        def getFonts() -> list[font_config]:
            sql = 'SELECT * FROM ticket_font_configs;'
            db = DB_manager.get_config_db()
            rows = db.execute(sql).fetchall()

            return [dict(row) for row in rows]
        
        @staticmethod
        def createFont(font: str, weigh: int, size: int):
            sql = build_insert_sql_sequence('ticket_font_configs', create_font_config_keys)
            execute_sql_and_close_db(sql, [font, weigh, size], 'config')
        
        @staticmethod
        def deleteFont(id: int):
            sql = 'DELETE FROM ticket_font_configs WHERE id = ?;'
            execute_sql_and_close_db(sql, [], 'config')