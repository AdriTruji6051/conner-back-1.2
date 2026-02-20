from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

from config.config import Config
from app.extensions import db
from app.connections.connections import init_db, register_sqlite_pragmas

if Config.LOGGING:
    import logging
    print('LOGGIN ACTIVE')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app-back.log"),
            logging.StreamHandler()         
        ]
    )


def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                    static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    app.config.from_object(Config)

    # Initialize SQLAlchemy ORM
    db.init_app(app)
    register_sqlite_pragmas(app)

    JWTManager(app)

    from app.views.products import routesProducts
    from app.views.tickets import routesTickets
    from app.views.analytics import routesAnalitycs
    from app.views.config import routesConfig
    from app.views.printers import routesPrinters
    from app.views.templates import routesTemplates

    app.register_blueprint(routesProducts)
    app.register_blueprint(routesTickets)
    app.register_blueprint(routesAnalitycs)
    app.register_blueprint(routesConfig)
    app.register_blueprint(routesPrinters)
    app.register_blueprint(routesTemplates)

    return app

def run_app():
    app = create_app()

    CORS(app, supports_credentials=True)

    # Create all database tables if they don't exist (replaces DB_manager.create_missing_db)
    with app.app_context():
        init_db()
        
        # Log all available endpoints
        if Config.LOGGING:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("=" * 80)
            logger.info("AVAILABLE ENDPOINTS")
            logger.info("=" * 80)
            routes = sorted(
                (rule.rule, ','.join(rule.methods - {'OPTIONS', 'HEAD'}))
                for rule in app.url_map.iter_rules()
                if rule.endpoint != 'static'
            )
            for route, methods in routes:
                logger.info(f"{methods:15} {route}")
            logger.info("=" * 80)

    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

if __name__== '__main__':
    run_app()