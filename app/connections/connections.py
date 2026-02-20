"""
Database connection management.

This module previously contained raw sqlite3 connection handling (DB_manager, DB_builder,
and table-creation classes). It has been replaced by Flask-SQLAlchemy ORM.

All models are now defined in app/models/core_classes.py.
Database initialization is handled by db.create_all() in run.py.
"""

import os
from app.extensions import db


def ensure_db_directory():
    """Create the database directory if it doesn't exist."""
    from config.config import Config
    db_path = Config._DB_PATH
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def init_db():
    """Create all tables that don't exist yet. Replaces DB_manager.create_missing_db()."""
    ensure_db_directory()

    # Import all models so SQLAlchemy registers them before create_all
    from app.models.core_classes import (  # noqa: F401
        Department, Product, InventoryLog, AssociateCode,
        TicketModel, ProductInTicket,
        DrawerLog, ProductChange, CashFlow,
        User, TicketFontConfig, TicketText,
    )
    from app.models.products import ensure_quicksale_product, ensure_default_department
    from app.models.config import ensure_default_font_config

    db.create_all()
    ensure_quicksale_product()
    ensure_default_department()
    ensure_default_font_config()


from sqlalchemy import event as sa_event


def register_sqlite_pragmas(app):
    """Call after db.init_app(app) to register SQLite PRAGMA settings."""
    with app.app_context():
        @sa_event.listens_for(db.engine, 'connect')
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=DELETE")  # use classic rollback journal
            cursor.close()