
import sqlite3
from flask import g
import os 

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

    @staticmethod
    def create_config_db():
        os.makedirs(os.path.dirname(Config.CONFIG_DB_DIR), exist_ok=True)
        conn = sqlite3.connect(Config.CONFIG_DB_DIR)
        conn.close()
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
        try:
            if 'products_db' not in g:
                g.db = sqlite3.connect(Config.PRODUCTS_DB_DIR)
                g.db.row_factory = sqlite3.Row
            return g.db
        
        except Exception as e:
            raise(e)
    
    @staticmethod
    def close_products_db():
        try:
            db = g.pop('products_db', None)
            if db is not None:
                db.close()

        except Exception as e:
            raise(e)
        
    @staticmethod
    def get_tickets_db():
        try:
            if 'tickets_db' not in g:
                g.db = sqlite3.connect(Config.TICKETS_DB_DIR)
                g.db.row_factory = sqlite3.Row
            return g.db
        
        except Exception as e:
            raise(e)
    
    @staticmethod
    def close_tickets_db():
        try:
            db = g.pop('tickets_db', None)
            if db is not None:
                db.close()

        except Exception as e:
            raise(e)
        
    @staticmethod
    def get_analitycs_db():
        try:
            if 'analitycs_db' not in g:
                g.db = sqlite3.connect(Config.ANALITYCS_DB_DIR)
                g.db.row_factory = sqlite3.Row
            return g.db
        
        except Exception as e:
            raise(e)
    
    @staticmethod
    def close_analitycs_db():
        try:
            db = g.pop('analitycs_db', None)
            if db is not None:
                db.close()

        except Exception as e:
            raise(e)
        
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
        
        db = DB_manager.get_products_db()

        try:
            db.execute(sql)
            db.commit()
        except Exception as e:
            raise "Couldn't create departments table"
        finally:
            DB_manager.close_products_db()

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
                FOREIGN KEY("department") REFERENCES "departments"("code")
            );
            """
        
        db = DB_manager.get_products_db()

        try:
            db.execute(sql)
            db.commit()
        except Exception as e:
            raise "Couldn't create products table"
        finally:
            DB_manager.close_products_db()

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
            raise "Couldn't create tickets table"
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
            raise "Couldn't create product_in_ticket table"
        finally:
            DB_manager.close_tickets_db()