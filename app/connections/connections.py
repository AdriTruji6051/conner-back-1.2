
import sqlite3
from flask import g
import os 

def execute_table_sql(sql: str, data_base: str, table_name: str = 'Not specified'):
    allowed_data_bases = ['products', 'analytics', 'config', 'tickets']

    if data_base not in allowed_data_bases:
        raise Exception('Specified data_base value is not allowed')
    
    db = object()

    if data_base == allowed_data_bases[0]:
        db = DB_manager.get_products_db()
    elif data_base == allowed_data_bases[1]:
        db = DB_manager.get_analitycs_db()
    elif data_base == allowed_data_bases[2]:
        db = DB_manager.get_config_db()
    elif data_base == allowed_data_bases[3]:
        db == DB_manager.get_tickets_db()

    try:
        db.execute(sql)
        db.commit()
    except Exception as e:
        raise Exception(f"Couldn't create {table_name} table: {e}")
    finally:
        DB_manager.close_products_db()
        DB_manager.close_tickets_db()
        DB_manager.close_analitycs_db()

from config.config import Config
# DB Builder methods
class DB_builder:
    @staticmethod
    def create_products_db():
        os.makedirs(os.path.dirname(Config.PRODUCTS_DB_DIR), exist_ok=True)
        conn = sqlite3.connect(Config.PRODUCTS_DB_DIR)
        conn.close()

        Products_tables.create_departments()
        Products_tables.create_products()
        Products_tables.create_associates_codes()
    
    @staticmethod
    def create_tickets_db():
        os.makedirs(os.path.dirname(Config.TICKETS_DB_DIR), exist_ok=True)
        conn = sqlite3.connect(Config.TICKETS_DB_DIR)
        conn.close()

        Tickets_tables.create_tickets()
        Tickets_tables.create_products_in_tickets()
    
    @staticmethod
    def create_analytics_db():
        os.makedirs(os.path.dirname(Config.ANALITYCS_DB_DIR), exist_ok=True)
        conn = sqlite3.connect(Config.ANALITYCS_DB_DIR)
        conn.close()

        Analitycs_tables.create_drawer_logs()
        Analitycs_tables.create_products_changes()

    @staticmethod
    def create_config_db():
        os.makedirs(os.path.dirname(Config.CONFIG_DB_DIR), exist_ok=True)
        conn = sqlite3.connect(Config.CONFIG_DB_DIR)
        conn.close()

        Config_tables.create_ticket_text()
        Config_tables.create_ticket_font_configs()
        Config_tables.create_users()

# DB Manager methods
class DB_manager:
    @staticmethod
    def all_db_exist() -> bool:
        if not os.path.exists(Config.PRODUCTS_DB_DIR):
            return False
        if not os.path.exists(Config.TICKETS_DB_DIR):
            return False
        if not os.path.exists(Config.ANALITYCS_DB_DIR):
            return False
        if not os.path.exists(Config.CONFIG_DB_DIR):
            return False
        
        return True
    
    @staticmethod
    def create_missing_db():
        if not os.path.exists(Config.PRODUCTS_DB_DIR):
            DB_builder.create_products_db()

        if not os.path.exists(Config.TICKETS_DB_DIR):
            DB_builder.create_tickets_db()

        if not os.path.exists(Config.ANALITYCS_DB_DIR):
            DB_builder.create_analytics_db()

        if not os.path.exists(Config.CONFIG_DB_DIR):
            DB_builder.create_config_db()

    # DB Getters and closers ------->

    @staticmethod
    def get_products_db():
        if 'products_db' not in g:
            g.db = sqlite3.connect(Config.PRODUCTS_DB_DIR)
            g.db.row_factory = sqlite3.Row
        return g.db
    
    @staticmethod
    def close_products_db():
        db = g.pop('products_db', None)
        if db is not None:
            db.close()
        
    @staticmethod
    def get_tickets_db():
        if 'tickets_db' not in g:
            g.db = sqlite3.connect(Config.TICKETS_DB_DIR)
            g.db.row_factory = sqlite3.Row
        return g.db
    
    @staticmethod
    def close_tickets_db():
        db = g.pop('tickets_db', None)
        if db is not None:
            db.close()
        
    @staticmethod
    def get_analitycs_db():
        if 'analitycs_db' not in g:
            g.db = sqlite3.connect(Config.ANALITYCS_DB_DIR)
            g.db.row_factory = sqlite3.Row
        return g.db
    
    
    @staticmethod
    def close_analitycs_db():
        db = g.pop('analitycs_db', None)
        if db is not None:
            db.close()

    @staticmethod
    def get_config_db():
        if 'config_db' not in g:
            g.db = sqlite3.connect(Config.CONFIG_DB_DIR)
            g.db.row_factory = sqlite3.Row
        return g.db
    
    @staticmethod
    def close_config_db():
        db = g.pop('config_db', None)
        if db is not None:
            db.close()
        
class Products_tables:
    @staticmethod
    def create_departments():
        sql = """
            CREATE TABLE "departments" (
                "code"	INTEGER NOT NULL,
                "description"	TEXT NOT NULL,
                PRIMARY KEY("code" AUTOINCREMENT)
            );
            """
        execute_table_sql(sql, 'products', 'departments')

    @staticmethod
    def create_products():
        sql = """
            CREATE TABLE "products" (
                "code"	TEXT NOT NULL UNIQUE,
                "description"	TEXT NOT NULL,
                "sale_type"	TEXT NOT NULL,
                "cost"	REAL,
                "sale_price"	REAL NOT NULL,
                "department"	INTEGER,
                "wholesale_price"	REAL,
                "priority"	INTEGER,
                "inventory"	REAL,
                "modified_at"	TEXT,
                "profit_margin"	INTEGER,
                "parent_code"	TEXT,
                PRIMARY KEY("code"),
                FOREIGN KEY("department") REFERENCES "departments"("code") ON UPDATE CASCADE ON DELETE SET NULL
            );
            """
        execute_table_sql(sql, 'products', 'products')

    @staticmethod
    def create_associates_codes():
        sql = """
            CREATE TABLE "associates_codes" (
                "code"	TEXT NOT NULL,
                "parent_code"	TEXT NOT NULL,
                "tag"	TEXT,
                PRIMARY KEY("code"),
                FOREIGN KEY("parent_code") REFERENCES "products"("code") ON UPDATE CASCADE ON DELETE CASCADE
            );
            """
        execute_table_sql(sql, 'products', 'associates_codes')

class Tickets_tables:
    @staticmethod
    def create_tickets():
        sql = """
            CREATE TABLE "tickets" (
                "id"	INTEGER NOT NULL,
                "created_at"	TEXT NOT NULL,
                "sub_total"	REAL NOT NULL,
                "total"	REAL NOT NULL,
                "profit"	REAL NOT NULL,
                "articles_count"	INTEGER NOT NULL,
                "notes"	TEXT,
                "username"	TEXT NOT NULL, 
                "ipv4_sender" TEXT NOT NULL,
                "discount"	REAL,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
            """
        
        db = DB_manager.get_tickets_db()

        try:
            db.execute(sql)
            db.commit()
        except Exception as e:
            raise Exception(f"Couldn't create tickets table:  {e}")
        finally:
            DB_manager.close_tickets_db()

    @staticmethod
    def create_products_in_tickets():
        sql = """
            CREATE TABLE "product_in_ticket" (
                "id"	INTEGER NOT NULL,
                "ticket_id"	INTEGER NOT NULL,
                "code"	VARCHAR(50) NOT NULL,
                "description"	TEXT NOT NULL,
                "cantity"	REAL NOT NULL,
                "profit"	REAL,
                "used_wholesale"	REAL,
                "used_price"	REAL NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT),
                FOREIGN KEY("ticket_id") REFERENCES "tickets"("id")
            );
            """
        
        db = DB_manager.get_tickets_db()

        try:
            db.execute(sql)
            db.commit()
        except Exception as e:
            raise Exception(f"Couldn't create product_in_ticket table: {e}")
        finally:
            DB_manager.close_tickets_db()

class Analitycs_tables:
    @staticmethod
    def create_products_changes():
        sql = """
            CREATE TABLE "products_changes" (
            "id"	INTEGER NOT NULL,
            "code"	TEXT NOT NULL,
            "original_code"	TEXT,
            "cost"	REAL,
            "sale_price"	REAL NOT NULL,
            "wholesale_price"	REAL,
            "modified_at"	TEXT NOT NULL,
            "method"	TEXT,
            PRIMARY KEY("id" AUTOINCREMENT)
        );
        """
        execute_table_sql(sql, 'analytics', 'products_changes')

    @staticmethod
    def create_drawer_logs():
        sql = """
            CREATE TABLE "drawer_logs" (
                "id"	INTEGER NOT NULL,
                "open_at"	TEXT NOT NULL,
                "user_id"	INTEGER NOT NULL,
                "method"	INTEGER NOT NULL,
                "transaction_type"	INTEGER NOT NULL,
                "transaction_id"	INTEGER,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
        """
        execute_table_sql(sql, 'analytics', 'drawer_logs')

class Config_tables:
    @staticmethod
    def create_ticket_font_configs():
        sql = """
            CREATE TABLE "ticket_font_configs" (
                "id"	INTEGER NOT NULL,
                "font"	TEXT NOT NULL,
                "weigh"	TEXT NOT NULL,
                "size"	INTEGER NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
        """
        execute_table_sql(sql, 'config', 'ticket_font_configs')

    @staticmethod
    def create_ticket_text():
        sql = """
            CREATE TABLE "ticket_text" (
                "id"	INTEGER NOT NULL,
                "text"	TEXT NOT NULL,
                "line"	INTEGER NOT NULL,
                "is_header"	INTEGER NOT NULL,
                "font_config"	INTEGER,
                PRIMARY KEY("id" AUTOINCREMENT),
                FOREIGN KEY("font_config") REFERENCES "ticket_font_configs"("id") ON UPDATE CASCADE ON DELETE SET NULL
            );
        """
        execute_table_sql(sql, 'config', 'ticket_text')
    
    @staticmethod
    def create_users():
        sql = """
            CREATE TABLE "users" (
                "id"	INTEGER NOT NULL,
                "user"	TEXT NOT NULL UNIQUE,
                "user_name"	TEXT NOT NULL,
                "password"	TEXT NOT NULL,
                "role_type"	TEXT NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
        """
        execute_table_sql(sql, 'config', 'users')