from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.models.config import Config
from app.helpers.helpers import AppResponse
from app.routes_constants import (
    ROUTE_GET_USERS, ROUTE_LOGIN_USER, ROUTE_CREATE_USER, ROUTE_UPDATE_USER, ROUTE_DELETE_USER,
    ROUTE_GET_HEADERS, ROUTE_UPDATE_HEADERS, ROUTE_GET_FOOTERS, ROUTE_UPDATE_FOOTERS,
    ROUTE_GET_FONTS, ROUTE_CREATE_FONT
)

routesConfig = Blueprint('routes-config', __name__)

@routesConfig.route(ROUTE_GET_USERS, methods=['GET'])
def get_users():
    try:
        return AppResponse.success({'users': [u.to_dict() for u in Config.Users.get_all()]}).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/user. Catch: {e}.')
        return AppResponse.not_found("users not found").to_flask_tuple()
    
@routesConfig.route(ROUTE_LOGIN_USER, methods=['POST'])
def login():
    try:
        data = dict(request.get_json())
        return AppResponse.success(Config.Users.login(data['user'], data['password'])).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/user/login. Catch: {e}.')
        return AppResponse.unauthorized("username or password incorrect").to_flask_tuple()
    
@routesConfig.route(ROUTE_CREATE_USER, methods=['POST'])
def create_user():
    try:
        data = dict(request.get_json())
        Config.Users.create(data)
        return AppResponse.created({'status': 'successfull user create'}).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/user/create. Catch: {e}.')
        return AppResponse.unauthorized("user not created").to_flask_tuple()
    
@routesConfig.route(ROUTE_UPDATE_USER, methods=['PUT'])
def update_user():
    try:
        data = dict(request.get_json())
        Config.Users.update(data)
        return AppResponse.success({'status': 'successfull user update'}).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/user/update. Catch: {e}.')
        return AppResponse.unauthorized("user not updated").to_flask_tuple()
    
@routesConfig.route(ROUTE_DELETE_USER, methods=['DELETE'])
def delete_user(id):
    try:
        Config.Users.delete(id)
        return AppResponse.success({'status': 'successfull user deleted'}).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/user/delete/<int:id>. Catch: {e}.')
        return AppResponse.unauthorized("user not deleted").to_flask_tuple()
    
@routesConfig.route(ROUTE_GET_HEADERS, methods=['GET'])
def get_headers():
    try:
        return AppResponse.success(Config.Ticket_text.get_headers()).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/ticket/text/headers. Catch: {e}.')
        return AppResponse.server_error("headers not founded").to_flask_tuple()
    
@routesConfig.route(ROUTE_GET_FOOTERS, methods=['GET'])
def get_footers():
    try:
        return AppResponse.success(Config.Ticket_text.get_footers()).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/ticket/text/footers. Catch: {e}.')
        return AppResponse.server_error("footers not founded").to_flask_tuple()

@routesConfig.route(ROUTE_UPDATE_HEADERS, methods=['PUT'])
def update_headers():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.update_headers(data['headers'])
        return AppResponse.success({'status': 'successfull headers update'}).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/ticket/text/headers. Catch: {e}.')
        return AppResponse.server_error("headers not founded").to_flask_tuple()
    
@routesConfig.route(ROUTE_UPDATE_FOOTERS, methods=['PUT'])
def update_footers():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.update_footers(data['footers'])
        return AppResponse.success({'status': 'successfull footers update'}).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/ticket/text/footers. Catch: {e}.')
        return AppResponse.server_error("footers not founded").to_flask_tuple()
    
@routesConfig.route(ROUTE_GET_FONTS, methods=['GET'])
def get_fonts():
    try:
        return AppResponse.success([f.to_dict() for f in Config.Ticket_text.getFonts()]).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/ticket/fonts. Catch: {e}.')
        return AppResponse.server_error("fonts could not been provided!").to_flask_tuple()
    
@routesConfig.route(ROUTE_CREATE_FONT, methods=['POST'])
def create_font():
    try:
        font = request.args.get('font')
        weigh = request.args.get('weigh', type=int)
        size = request.args.get('size', type=int)
        Config.Ticket_text.createFont(font, weigh, size)
        return AppResponse.created([f.to_dict() for f in Config.Ticket_text.getFonts()]).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/config/ticket/fonts. Catch: {e}.')
        return AppResponse.server_error("fonts could not been provided!").to_flask_tuple()