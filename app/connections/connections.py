
import sqlite3
from flask import g
import os 

def execute_table_sql(sql: str, data_base: str, table_name: str = 'Not specified'):
    allowed_data_bases = ['analytics', 'config', 'main']

    if data_base not in allowed_data_bases:
        raise Exception('Specified data_base value is not allowed')
    
    db = object()

    if data_base == allowed_data_bases[0]:
        db = DB_manager.get_analitycs_db()
    elif data_base == allowed_data_bases[1]:
        db = DB_manager.get_config_db()
    elif data_base == allowed_data_bases[2]:
        db = DB_manager.get_main_db()

    try:
        db.execute(sql)
        db.commit()
    except Exception as e:
        raise Exception(f"Couldn't create {table_name} table: {e}")
    finally:
        DB_manager.close_analitycs_db()
        DB_manager.close_main_db()

from config.config import Config
# DB Builder methods
class DB_builder:
    @staticmethod
    def create_products_db():
        os.makedirs(os.path.dirname(Config.MAIN_DB_DIR), exist_ok=True)
        conn = sqlite3.connect(Config.MAIN_DB_DIR)
        conn.close()

        Products_tables.create_departments()
        Products_tables.create_products()
        Products_tables.create_associates_codes()
    
    @staticmethod
    def create_tickets_db():
        os.makedirs(os.path.dirname(Config.MAIN_DB_DIR), exist_ok=True)
        conn = sqlite3.connect(Config.MAIN_DB_DIR)
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
        if not os.path.exists(Config.ANALITYCS_DB_DIR):
            return False
        if not os.path.exists(Config.CONFIG_DB_DIR):
            return False
        if not os.path.exists(Config.MAIN_DB_DIR):
            return False
        
        return True
    
    @staticmethod
    def create_missing_db():
        if not os.path.exists(Config.ANALITYCS_DB_DIR):
            DB_builder.create_analytics_db()

        if not os.path.exists(Config.CONFIG_DB_DIR):
            DB_builder.create_config_db()

        if not os.path.exists(Config.MAIN_DB_DIR):
            DB_builder.create_products_db()
            DB_builder.create_tickets_db()

    # DB Getters and closers ------->

    @staticmethod
    def get_main_db():
        if 'main_db' not in g:
            g.db = sqlite3.connect(Config.MAIN_DB_DIR)
            g.db.row_factory = sqlite3.Row
        return g.db
    
    @staticmethod
    def close_main_db():
        db = g.pop('main_db', None)
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
        execute_table_sql(sql, 'main', 'departments')

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
        execute_table_sql(sql, 'main', 'products')

        sql = """
            CREATE TABLE inventory_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL,
                old_inventory REAL,
                new_inventory REAL,
                change REAL,
                change_type TEXT CHECK(change_type IN ('INCREASE', 'DECREASE')),
                modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_code) REFERENCES products(code) ON DELETE CASCADE
            );
        """
        execute_table_sql(sql, 'main', 'products')

        sql = """
            CREATE TRIGGER track_inventory_changes
            AFTER UPDATE OF inventory ON products
            FOR EACH ROW
            WHEN OLD.inventory <> NEW.inventory
            BEGIN
                INSERT INTO inventory_log (product_code, old_inventory, new_inventory, change, change_type)
                VALUES (
                    NEW.code,
                    OLD.inventory,
                    NEW.inventory,
                    NEW.inventory - OLD.inventory,
                    CASE 
                        WHEN NEW.inventory > OLD.inventory THEN 'INCREASE'
                        ELSE 'DECREASE'
                    END
                );
            END;
        """
        execute_table_sql(sql, 'main', 'products')

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
        execute_table_sql(sql, 'main', 'associates_codes')

class Tickets_tables:
    @staticmethod
    def create_tickets():
        sql = """
            CREATE TABLE "tickets" (
                "id"	INTEGER NOT NULL,
                "created_at"	TEXT NOT NULL,
                'modified_at' TEXT,
                "sub_total"	REAL NOT NULL,
                "total"	REAL NOT NULL,
                "profit"	REAL NOT NULL,
                "products_count"	INTEGER NOT NULL,
                "notes"	TEXT,
                "user_id"	INTEGER NOT NULL, 
                "ipv4_sender" TEXT NOT NULL,
                "discount"	REAL,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
            """
        
        execute_table_sql(sql, 'main', 'tickets')

    @staticmethod
    def create_products_in_tickets():
        sql = """
            CREATE TABLE "product_in_ticket" (
                "id"	INTEGER NOT NULL,
                "ticket_id"	INTEGER NOT NULL,
                "code"	TEXT,
                "description"	TEXT NOT NULL,
                "cantity"	REAL NOT NULL,
                "profit"	REAL,
                "wholesale_price"	REAL,
                "sale_price"	REAL NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT),
                FOREIGN KEY("code") REFERENCES "products"("code") ON UPDATE CASCADE ON DELETE SET NULL,
                FOREIGN KEY("ticket_id") REFERENCES "tickets"("id")
            );
            """
        
        execute_table_sql(sql, 'main', 'product_in_ticket')

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