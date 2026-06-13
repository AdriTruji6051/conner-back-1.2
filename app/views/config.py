from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging
from sqlalchemy.exc import IntegrityError

from app.models.config import Config
from app.helpers.helpers import AppResponse, ValidationError
from app.routes_constants import (
    ROUTE_GET_USERS, ROUTE_LOGIN_USER, ROUTE_CREATE_USER, ROUTE_UPDATE_USER, ROUTE_DELETE_USER,
    ROUTE_GET_HEADERS, ROUTE_UPDATE_HEADERS, ROUTE_GET_FOOTERS, ROUTE_UPDATE_FOOTERS,
    ROUTE_GET_FONTS, ROUTE_CREATE_FONT, ROUTE_GET_BODY_FONT, ROUTE_SET_BODY_FONT,
    ROUTE_GET_HEADER_FONT, ROUTE_SET_HEADER_FONT, ROUTE_GET_PRINT_FULL_ROW, ROUTE_SET_PRINT_FULL_ROW,
    ROUTE_UPLOAD_PHOTO, ROUTE_GET_PHOTO_CONFIG, ROUTE_UPDATE_PHOTO_CONFIG, ROUTE_DELETE_PHOTO, ROUTE_GET_PHOTO_DATA
)

routesConfig = Blueprint('routes-config', __name__)

def _parse_pagination_args(args, default_page: int = 1, default_page_size: int = 10, max_page_size: int = 500) -> tuple[int, int]:
    """Parse pagination query params, coercing to safe bounds instead of raising."""
    try:
        page = int(args.get('page', default_page))
    except (TypeError, ValueError):
        page = default_page

    try:
        page_size = int(args.get('page_size', args.get('pageSize', default_page_size)))
    except (TypeError, ValueError):
        page_size = default_page_size

    # Coerce into valid ranges
    if page < 1:
        page = default_page
    if page_size < 1:
        page_size = default_page_size
    if page_size > max_page_size:
        page_size = max_page_size

    return page, page_size

@routesConfig.route(ROUTE_GET_USERS, methods=['GET'])
def get_users():
    try:
        page, page_size = _parse_pagination_args(request.args)
        result = Config.Users.get_all(page=page, page_size=page_size)
        return AppResponse.success(result).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_USERS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving users').to_flask_tuple()
    
@routesConfig.route(ROUTE_LOGIN_USER, methods=['POST'])
def login():
    try:
        data = dict(request.get_json())
        return AppResponse.success(Config.Users.login(data['user'], data['password'])).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except (ValueError, KeyError):
        return AppResponse.unauthorized('Username or password incorrect').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_LOGIN_USER}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error during login').to_flask_tuple()
    
@routesConfig.route(ROUTE_CREATE_USER, methods=['POST'])
def create_user():
    try:
        data = dict(request.get_json())
        Config.Users.create(data)
        return AppResponse.created({'status': 'successfull user create'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A user with that username already exists').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_CREATE_USER}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error creating user').to_flask_tuple()
    
@routesConfig.route(ROUTE_UPDATE_USER, methods=['PUT'])
def update_user():
    try:
        data = dict(request.get_json())
        Config.Users.update(data)
        return AppResponse.success({'status': 'successfull user update'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A user with that username already exists').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_USER}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating user').to_flask_tuple()
    
@routesConfig.route(ROUTE_DELETE_USER, methods=['DELETE'])
def delete_user(id):
    try:
        Config.Users.delete(id)
        return AppResponse.success({'status': 'successfull user deleted'}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_DELETE_USER}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error deleting user').to_flask_tuple()
    
@routesConfig.route(ROUTE_GET_HEADERS, methods=['GET'])
def get_headers():
    try:
        return AppResponse.success(Config.Ticket_text.get_headers()).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_HEADERS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving headers').to_flask_tuple()
    
@routesConfig.route(ROUTE_GET_FOOTERS, methods=['GET'])
def get_footers():
    try:
        return AppResponse.success(Config.Ticket_text.get_footers()).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_FOOTERS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving footers').to_flask_tuple()

@routesConfig.route(ROUTE_UPDATE_HEADERS, methods=['PUT'])
def update_headers():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.update_headers(data['headers'])
        return AppResponse.success({'status': 'successfull headers update'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_HEADERS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating headers').to_flask_tuple()
    
@routesConfig.route(ROUTE_UPDATE_FOOTERS, methods=['PUT'])
def update_footers():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.update_footers(data['footers'])
        return AppResponse.success({'status': 'successfull footers update'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_FOOTERS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating footers').to_flask_tuple()
    
@routesConfig.route(ROUTE_GET_FONTS, methods=['GET'])
def get_fonts():
    try:
        return AppResponse.success([f.to_dict() for f in Config.Ticket_text.getFonts()]).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_FONTS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving fonts').to_flask_tuple()
    
@routesConfig.route(ROUTE_CREATE_FONT, methods=['POST'])
def create_font():
    try:
        font = request.args.get('font')
        weigh = request.args.get('weigh', type=int)
        size = request.args.get('size', type=int)
        Config.Ticket_text.createFont(font, weigh, size)
        return AppResponse.created([f.to_dict() for f in Config.Ticket_text.getFonts()]).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_CREATE_FONT}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error creating font').to_flask_tuple()


@routesConfig.route(ROUTE_GET_BODY_FONT, methods=['GET'])
def get_body_font():
    try:
        return AppResponse.success(Config.Ticket_text.get_body_font()).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_BODY_FONT}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving body font').to_flask_tuple()


@routesConfig.route(ROUTE_SET_BODY_FONT, methods=['PUT'])
def set_body_font():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.set_body_font(int(data['font_config_id']))
        return AppResponse.success({'status': 'successfull body font update'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except (ValueError, KeyError) as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_SET_BODY_FONT}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating body font').to_flask_tuple()


@routesConfig.route(ROUTE_GET_HEADER_FONT, methods=['GET'])
def get_header_font():
    try:
        return AppResponse.success(Config.Ticket_text.get_header_font()).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_HEADER_FONT}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving header font').to_flask_tuple()


@routesConfig.route(ROUTE_SET_HEADER_FONT, methods=['PUT'])
def set_header_font():
    try:
        data = dict(request.get_json())
        Config.Ticket_text.set_header_font(int(data['font_config_id']))
        return AppResponse.success({'status': 'successfull header font update'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except (ValueError, KeyError) as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_SET_HEADER_FONT}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating header font').to_flask_tuple()


@routesConfig.route(ROUTE_GET_PRINT_FULL_ROW, methods=['GET'])
def get_print_full_row():
    try:
        value = Config.Ticket_text.get_print_full_row()
        return AppResponse.success({'print_full_row': value}).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_PRINT_FULL_ROW}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving print_full_row setting').to_flask_tuple()


@routesConfig.route(ROUTE_SET_PRINT_FULL_ROW, methods=['PUT'])
def set_print_full_row():
    try:
        data = dict(request.get_json())
        if 'print_full_row' not in data:
            return AppResponse.validation_error([{'print_full_row': 'Field is required'}]).to_flask_tuple()
        
        value = data['print_full_row']
        if not isinstance(value, bool):
            return AppResponse.validation_error([{'print_full_row': 'Must be a boolean value'}]).to_flask_tuple()
        
        Config.Ticket_text.set_print_full_row(value)
        return AppResponse.success({'status': 'print_full_row setting updated successfully'}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_SET_PRINT_FULL_ROW}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating print_full_row setting').to_flask_tuple()


@routesConfig.route(ROUTE_UPLOAD_PHOTO, methods=['POST'])
def upload_photo():
    try:
        if 'photo' not in request.files:
            return AppResponse.validation_error([{'photo': 'Photo file is required'}]).to_flask_tuple()
        
        photo_file = request.files['photo']
        if photo_file.filename == '':
            return AppResponse.validation_error([{'photo': 'No file selected'}]).to_flask_tuple()
        
        # Get optional parameters
        position = request.form.get('position', 'header')
        height = request.form.get('height', type=int)
        width = request.form.get('width', type=int, default=640)
        
        # Read file data
        photo_data = photo_file.read()
        
        result = Config.Ticket_text.upload_photo(photo_data, position, height, width)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPLOAD_PHOTO}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error uploading photo').to_flask_tuple()


@routesConfig.route(ROUTE_GET_PHOTO_CONFIG, methods=['GET'])
def get_photo_config():
    try:
        return AppResponse.success(Config.Ticket_text.get_photo_config()).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_PHOTO_CONFIG}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving photo config').to_flask_tuple()


@routesConfig.route(ROUTE_UPDATE_PHOTO_CONFIG, methods=['PUT'])
def update_photo_config():
    try:
        data = dict(request.get_json())
        enabled = data.get('enabled')
        position = data.get('position')
        height = data.get('height')
        width = data.get('width')
        
        Config.Ticket_text.update_photo_config(enabled, position, height, width)
        return AppResponse.success({'status': 'photo config updated successfully'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_PHOTO_CONFIG}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating photo config').to_flask_tuple()


@routesConfig.route(ROUTE_DELETE_PHOTO, methods=['DELETE'])
def delete_photo():
    try:
        Config.Ticket_text.delete_photo()
        return AppResponse.success({'status': 'photo deleted successfully'}).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_DELETE_PHOTO}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error deleting photo').to_flask_tuple()


@routesConfig.route(ROUTE_GET_PHOTO_DATA, methods=['GET'])
def get_photo_data():
    try:
        photo_data = Config.Ticket_text.get_photo_data()
        if photo_data is None:
            return AppResponse.not_found('No photo configured').to_flask_tuple()
        
        from flask import send_file
        import io
        return send_file(io.BytesIO(photo_data), mimetype='image/png')
    except Exception as e:
        logging.exception(f'{ROUTE_GET_PHOTO_DATA}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving photo data').to_flask_tuple()
