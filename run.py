from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

from config.config import Config
from app.connections.connections import DB_manager

import logging

if Config.LOGGING:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()         
        ]
    )


def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                    static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    app.config.from_object(Config)

    JWTManager(app)

    from app.views.products import routesProducts
    from app.views.tickets import routesTickets

    app.register_blueprint(routesProducts)
    app.register_blueprint(routesTickets)

    return app

def run_app():
    app = create_app()

    CORS(app, supports_credentials=True)

    # App context is used to manage the same db connections with flask, but used before of the app running 
    with app.app_context():
        if(not DB_manager.all_db_exist()):
            DB_manager.create_missing_db()

    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

if __name__== '__main__':
    run_app()