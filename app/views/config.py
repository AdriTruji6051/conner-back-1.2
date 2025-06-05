from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.models.config import Config

routesConfig = Blueprint('routes-config', __name__)

@routesConfig.route('/api/config/user', methods=['GET'])
def get_users():
    try:
        return jsonify({
            'users': Config.Users.get_all()
        })
    except Exception as e:
        logging.info(f'/api/config/user. Catch: {e}.')
        return jsonify({"error": "users not found"}), 404
    
@routesConfig.route('/api/config/user/login', methods=['POST'])
def login():
    try:
        data = dict(request.get_json())
        return jsonify(Config.Users.login(data['user'], data['password']))
    
    except Exception as e:
        logging.info(f'/api/config/user/login. Catch: {e}.')
        return jsonify({"error": "username or password incorrect"}), 401
    
@routesConfig.route('/api/config/user/create', methods=['POST'])
def create_user():
    try:
        data = dict(request.get_json())
        Config.Users.create(data)

        return jsonify({
            'status': 'successfull user create'
        })
    except Exception as e:
        logging.info(f'/api/config/user/create. Catch: {e}.')
        return jsonify({"error": "user not created"}), 401
    
@routesConfig.route('/api/config/user/update', methods=['PUT'])
def update_user():
    try:
        data = dict(request.get_json())
        Config.Users.update(data)

        return jsonify({
            'status': 'successfull user update'
        })
    except Exception as e:
        logging.info(f'/api/config/user/update. Catch: {e}.')
        return jsonify({"error": "user not updated"}), 401
    
@routesConfig.route('/api/config/user/delete/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        Config.Users.delete(id)

        return jsonify({
            'status': 'successfull user update'
        })
    except Exception as e:
        logging.info(f'/api/config/user/delete/<int:id>. Catch: {e}.')
        return jsonify({"error": "user not deleted"}), 401
    
@routesConfig.route('/api/config/ticket/text/headers', methods=['GET'])
def get_headers():
    try:
        return jsonify({
            'headers': Config.Ticket_text.get_headers()
        })
    except Exception as e:
        logging.info(f'/api/config/ticket/text/headers. Catch: {e}.')
        return jsonify({"error": "headers not founded"}), 500
    
@routesConfig.route('/api/config/ticket/text/footers', methods=['GET'])
def get_footers():
    try:
        return jsonify({
            'footers': Config.Ticket_text.get_footers()
        })
    except Exception as e:
        logging.info(f'/api/config/ticket/text/footers. Catch: {e}.')
        return jsonify({"error": "footers not founded"}), 500

@routesConfig.route('/api/config/ticket/text/headers/update', methods=['PUT'])
def update_headers():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.update_headers(data['headers'])

        return jsonify({
            'status': 'successfull headers update'
        })
    except Exception as e:
        logging.info(f'/api/config/ticket/text/headers. Catch: {e}.')
        return jsonify({"error": "headers not founded"}), 500
    
@routesConfig.route('/api/config/ticket/text/footers/update', methods=['PUT'])
def update_footers():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.update_footers(data['footers'])

        return jsonify({
            'status': 'successfull footers update'
        })
    except Exception as e:
        logging.info(f'/api/config/ticket/text/footers. Catch: {e}.')
        return jsonify({"error": "footers not founded"}), 500
    
@routesConfig.route('/api/config/ticket/fonts', methods=['GET'])
def getFonts():
    try:
        return jsonify({
            'fonts': Config.Ticket_text.getFonts()
        })
    except Exception as e:
        logging.info(f'/api/config/ticket/fonts. Catch: {e}.')
        return jsonify({"error": "fonts could not been provided!"}), 500
    
@routesConfig.route('/api/config/ticket/fonts/create', methods=['POST'])
def createFont():
    try:
        font = request.args.get('font')
        weigh = request.args.get('weigh', type=int)
        size = request.args.get('size', type=int)

        Config.Ticket_text.createFont(font, weigh, size)

        return jsonify({
            'fonts': Config.Ticket_text.getFonts(),
            'message': 'Succesfull font created!'
        })
    except Exception as e:
        logging.info(f'/api/config/ticket/fonts. Catch: {e}.')
        return jsonify({"error": "fonts could not been provided!"}), 500