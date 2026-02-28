from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
import os
import logging as _logging

from config.config import Config
from app.extensions import db
from app.connections.connections import init_db, register_sqlite_pragmas
from app.helpers.helpers import AppResponse, ValidationError

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


def _register_error_handlers(app: Flask):
    """Register global error handlers that ensure every error returns a
    consistent ``AppResponse``-formatted JSON envelope."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return AppResponse.validation_error(exc.errors).to_flask_tuple()

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(exc: IntegrityError):
        db.session.rollback()
        return AppResponse.conflict('Database constraint violation — a record with that key may already exist').to_flask_tuple()

    @app.errorhandler(404)
    def handle_not_found(exc):
        return AppResponse.not_found('The requested resource was not found').to_flask_tuple()

    @app.errorhandler(405)
    def handle_method_not_allowed(exc):
        return AppResponse.error('Method not allowed', 405).to_flask_tuple()

    @app.errorhandler(500)
    def handle_internal_error(exc):
        return AppResponse.server_error('An unexpected server error occurred').to_flask_tuple()


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

    _register_error_handlers(app)

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