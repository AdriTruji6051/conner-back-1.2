from dotenv import load_dotenv
from datetime import timedelta
import os
import sys

# Load secrets from .env file
load_dotenv()

class Config:
    # Security keys with default values for development
    # WARNING: Change these in production!
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-min-32-chars")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production-min-32-chars")
    
    # Validate and warn about default keys
    if SECRET_KEY == "dev-secret-key-change-in-production-min-32-chars":
        print("WARNING: Using default SECRET_KEY. Generate a secure key for production!")
        print("Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
    elif len(SECRET_KEY) < 32:
        print("WARNING: SECRET_KEY should be at least 32 characters long")
        print(f"Current length: {len(SECRET_KEY)}")
    
    if JWT_SECRET_KEY == "dev-jwt-secret-key-change-in-production-min-32-chars":
        print("WARNING: Using default JWT_SECRET_KEY. Generate a secure key for production!")
        print("Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
    elif len(JWT_SECRET_KEY) < 32:
        print("WARNING: JWT_SECRET_KEY should be at least 32 characters long")
        print(f"Current length: {len(JWT_SECRET_KEY)}")
    
    # Token expiration configuration
    TOKEN_NEVER_EXPIRES = os.getenv("TOKEN_NEVER_EXPIRES", "True").lower() in ('true', '1', 'yes', 'y')
    
    if TOKEN_NEVER_EXPIRES:
        JWT_ACCESS_TOKEN_EXPIRES = False
        print("WARNING: JWT tokens configured to NEVER EXPIRE. This is NOT recommended for production!")
    else:
        TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "8"))
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=TOKEN_HOURS)

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

    # Network configuration - 0.0.0.0 allows access from other computers in local network
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Convert string env vars to boolean properly
    DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1', 'yes', 'y')
    LOGGING = os.getenv("LOGGING", "True").lower() in ('true', '1', 'yes', 'y')
    
    # CORS allowed origins (comma-separated list)
    # Default: "*" allows all origins (convenient for development, restrict in production)
    allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
    if allowed_origins_str == "*":
        ALLOWED_ORIGINS = ["*"]
        print("WARNING: CORS configured to allow ALL origins (*). Restrict in production!")
    else:
        ALLOWED_ORIGINS = allowed_origins_str.split(',')
        ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]