from dotenv import load_dotenv
from datetime import timedelta
import os

# Load secrets from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-key-jwt")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(int(os.getenv("TOKEN_HOURS", "8")))

    # SQLAlchemy single consolidated database
    _DB_PATH = os.path.abspath(os.getenv('DB_PATH', './db/conner.db'))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Legacy paths (kept for reference / migration scripts only)
    PRODUCTS_DB_DIR = os.getenv('PRODUCTS_DB', './products.db')
    TICKETS_DB_DIR = os.getenv('TICKETS_DB', './tickets.db')
    ANALITYCS_DB_DIR = os.getenv('ANALITYCS_DB', './analitycs.db')
    CONFIG_DB_DIR = os.getenv('CONFIG_DB', './config.db')
    MAIN_DB_DIR = os.getenv('MAIN_DB', './main.db')

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))

    DEBUG = os.getenv("DEBUG", True)
    LOGGING = os.getenv("LOGGING", True)