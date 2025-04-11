from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.models.analytics import Analytics
from app.controlers.printers import Printers

PRINTERS_MANAGER = Printers()

routesAnalitycs = Blueprint('routes-analitycs', __name__)

@routesAnalitycs.route('/api/cash/inflow', methods=['POST'])
def insert_inflow():
    try:
        amount = request.args.get('amount', type=float)
        drawer = request.args.get('drawer')
        description = request.args.get('description')

        Analytics.Cash_flow.insert(amount=amount, in_or_out=1, is_payment=0, description=description)
        return jsonify(
            PRINTERS_MANAGER.open_drawer()
        ) # TODO Change the drawer for the drawer name 
    
    except Exception as e:
        logging.error(f'/api/cash/inflow Error: {e}. Data recieved: {amount}, {drawer}, {description}')
        return jsonify({"error": "problems at register inflow"}), 500
    
@routesAnalitycs.route('/api/cash/outflow', methods=['POST'])
def insert_ouflow():
    try:
        amount = request.args.get('amount', type=float)
        drawer = request.args.get('drawer')
        description = request.args.get('description')
        Analytics.Cash_flow.insert(amount=amount, in_or_out=0, is_payment=0, description=description)
        return jsonify(
            PRINTERS_MANAGER.open_drawer()
        ) # TODO Change the drawer for the drawer name 
    
    except Exception as e:
        logging.error(f'/api/cash/outflow. Error: {e}. Data recieved: {amount}, {drawer}, {description}')
        return jsonify({"error": "problems at register cash outflow"}), 500
    
@routesAnalitycs.route('/api/cash/payment', methods=['POST'])
def insert_payment():
    try:
        amount = request.args.get('amount', type=float)
        drawer = request.args.get('drawer')
        description = request.args.get('description')
        Analytics.Cash_flow.insert(amount=amount, in_or_out=0, is_payment=1, description=description)
        return jsonify(
            PRINTERS_MANAGER.open_drawer()
        ) # TODO Change the drawer for the drawer name 
    
    except Exception as e:
        logging.error(f'/api/cash/payment. Error: {e}. Data recieved: {amount}, {drawer}, {description}')
        return jsonify({"error": "problems at register cash payment"}), 500


@routesAnalitycs.route('/api/drawer/log/<int:id>', methods=['GET'])
def get_drawer_log(id):
    try:
        return jsonify(Analytics.Drawer_logs.get(id))
    
    except Exception as e:
        logging.error(f'/api/drawer/log/<int:id>. Error: {e}. Data recieved: {id}')
        return jsonify({"error": "drawer logs not found"}), 404
    
@routesAnalitycs.route('/api/drawer/log/date/<string:date>', methods=['GET'])
def get_drawer_log_date_date(date):
    try:
        return jsonify({
            'logs': Analytics.Drawer_logs.get_all(date)
        })
    
    except Exception as e:
        logging.error(f'/api/drawer/log/date/<string:date>. Error: {e}. Data recieved: {date}')
        return jsonify({"error": f"drawer logs at date {date} not found"}), 404
    
@routesAnalitycs.route('/api/product/log/changes/<int:id>', methods=['GET'])
def get_changes_log(id: int):
    try:
        return jsonify(Analytics.Products_changes.get(id))
    
    except Exception as e:
        logging.error(f'/api/product/log/changes/<int:id>. Error: {e}. Data recieved: {id}')
        return jsonify({"error": f"product log not found"}), 404
    
@routesAnalitycs.route('/api/product/log/changes/date/<string:date>', methods=['GET'])
def get_changes_log_date(date: str):
    try:
        return jsonify({
            'logs': Analytics.Products_changes.get_all(date)
        })
    
    except Exception as e:
        logging.error(f'/api/product/log/changes/date/<string:date>. Error: {e}. Data recieved: {date}')
        return jsonify({"error": f"product logs at date {date} not found"}), 404