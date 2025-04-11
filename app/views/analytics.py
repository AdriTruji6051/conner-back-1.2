from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.models.analytics import Analytics

routesAnalitycs = Blueprint('routes-analitycs', __name__)

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

