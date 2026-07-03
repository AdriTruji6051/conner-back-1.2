from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging
import socket
from sqlalchemy.exc import IntegrityError

from app.models.config import Config
from app.helpers.helpers import AppResponse, ValidationError
from config.config import Config as AppConfig
from app.routes_constants import (
    ROUTE_STATUS,
    ROUTE_GET_USERS, ROUTE_LOGIN_USER, ROUTE_CREATE_USER, ROUTE_UPDATE_USER, ROUTE_DELETE_USER,
    ROUTE_UPDATE_USER_LANGUAGE,
    ROUTE_GET_HEADERS, ROUTE_UPDATE_HEADERS, ROUTE_GET_FOOTERS, ROUTE_UPDATE_FOOTERS,
    ROUTE_GET_FONTS, ROUTE_CREATE_FONT, ROUTE_GET_BODY_FONT, ROUTE_SET_BODY_FONT,
    ROUTE_GET_HEADER_FONT, ROUTE_SET_HEADER_FONT, ROUTE_GET_PRINT_FULL_ROW, ROUTE_SET_PRINT_FULL_ROW,
    ROUTE_UPLOAD_PHOTO, ROUTE_GET_PHOTO_CONFIG, ROUTE_UPDATE_PHOTO_CONFIG, ROUTE_DELETE_PHOTO, ROUTE_GET_PHOTO_DATA,
    ROUTE_GET_CURRENCY, ROUTE_SET_CURRENCY,
    ROUTE_GET_PRICE_TAG_SETTINGS, ROUTE_UPDATE_PRICE_TAG_SETTINGS, ROUTE_PRINT_PRICE_TAG
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

@routesConfig.route(ROUTE_STATUS, methods=['GET'])
def status():
    """Health check endpoint to verify API is operational."""
    return AppResponse.success({
        'status': 'ok',
        'message': 'API is running'
    }).to_flask_tuple()


def get_local_ip():
    """
    Get the local IP address of the machine.
    Returns '127.0.0.1' as fallback if detection fails.
    """
    try:
        # Create temporary socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


@routesConfig.route('/api/config', methods=['GET'])
def get_server_config():
    """
    Endpoint to get server configuration.
    Returns the base API URL so frontend can connect dynamically.
    This endpoint does not require authentication.
    """
    try:
        local_ip = get_local_ip()
        port = AppConfig.PORT
        
        return AppResponse.success(
            message="Server configuration retrieved",
            data={
                "apiUrl": f"http://{local_ip}:{port}",
                "socketUrl": f"http://{local_ip}:{port}",
                "version": "1.2.0"
            }
        ).to_flask_tuple()
    except Exception as e:
        logging.exception(f'/api/config. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving server configuration').to_flask_tuple()

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
    

@routesConfig.route(ROUTE_UPDATE_USER_LANGUAGE, methods=['PUT'])
def update_user_language():
    """Update the language preference for the authenticated user."""
    try:
        from flask_jwt_extended import get_jwt_identity
        from app.helpers.error_codes import ErrorCodes
        
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        
        # Get language from request
        data = dict(request.get_json())
        language = data.get('language_preference')
        
        if not language:
            return AppResponse.validation_error([
                {'language_preference': 'Language preference is required'}
            ]).to_flask_tuple()
        
        # Update language preference
        Config.Users.update_language_preference(user_id, language)
        
        return AppResponse.success({
            'status': 'Language preference updated successfully',
            'language_preference': language
        }, error_code=ErrorCodes.SETTINGS_LANGUAGE_CHANGED).to_flask_tuple()
        
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_USER_LANGUAGE}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating language preference').to_flask_tuple()
    

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


@routesConfig.route(ROUTE_GET_CURRENCY, methods=['GET'])
def get_currency():
    """Get the current currency setting."""
    try:
        currency = Config.Ticket_text.get_currency()
        return AppResponse.success({'currency': currency}).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_CURRENCY}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving currency').to_flask_tuple()


@routesConfig.route(ROUTE_SET_CURRENCY, methods=['PUT'])
def set_currency():
    """Set the currency code."""
    try:
        data = dict(request.get_json())
        if 'currency' not in data:
            return AppResponse.validation_error([{'currency': 'Currency field is required'}]).to_flask_tuple()
        
        currency = data['currency']
        Config.Ticket_text.set_currency(currency)
        return AppResponse.success({'status': 'Currency updated successfully', 'currency': currency}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_SET_CURRENCY}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating currency').to_flask_tuple()



@routesConfig.route(ROUTE_GET_PRICE_TAG_SETTINGS, methods=['GET'])
def get_price_tag_settings():
    """Get current price tag settings."""
    try:
        return AppResponse.success(Config.PriceTag.get_settings()).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_PRICE_TAG_SETTINGS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error retrieving price tag settings').to_flask_tuple()


@routesConfig.route(ROUTE_UPDATE_PRICE_TAG_SETTINGS, methods=['PUT'])
def update_price_tag_settings():
    """Update price tag settings."""
    try:
        data = dict(request.get_json())
        Config.PriceTag.update_settings(data)
        return AppResponse.success({'status': 'Price tag settings updated successfully'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_PRICE_TAG_SETTINGS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating price tag settings').to_flask_tuple()


@routesConfig.route(ROUTE_PRINT_PRICE_TAG, methods=['POST'])
def print_price_tag():
    """Print a price tag with product information.
    
    Expected JSON body:
    {
        "code": "product_code",
        "description": "Product description",
        "price": 99.99,
        "wholesale_price": 79.99  // optional
    }
    """
    try:
        data = dict(request.get_json())
        
        # Validate required fields
        v = ValidationError()
        if 'code' not in data or not data['code']:
            v.add('code', 'Product code is required')
        if 'description' not in data or not data['description']:
            v.add('description', 'Product description is required')
        if 'price' not in data:
            v.add('price', 'Price is required')
        if 'printer_name' not in data or not data['printer_name']:
            v.add('printer_name', 'Printer name is required')
        v.raise_if_errors()
        
        # Get settings
        settings = Config.PriceTag.get_settings()
        
        # Get font configurations
        code_font = Config.PriceTag.get_font_config(settings['code_font_config']) if settings['code_font_config'] else None
        desc_font = Config.PriceTag.get_font_config(settings['description_font_config']) if settings['description_font_config'] else None
        price_font = Config.PriceTag.get_font_config(settings['price_font_config']) if settings['price_font_config'] else None
        wholesale_font = Config.PriceTag.get_font_config(settings['wholesale_price_font_config']) if settings['wholesale_price_font_config'] else None
        
        # Build print context
        print_context = {
            'code': data['code'],
            'description': data['description'],
            'price': data['price'],
            'wholesale_price': data.get('wholesale_price'),
            'show_wholesale_price': settings['show_wholesale_price'] and data.get('wholesale_price') is not None,
            'enable_cut_row': settings['enable_cut_row'],
            'show_barcode': settings['show_barcode'],
            'barcode_height': settings['barcode_height'],
            'barcode_width': settings['barcode_width'],
            'fonts': {
                'code': code_font,
                'description': desc_font,
                'price': price_font,
                'wholesale_price': wholesale_font
            }
        }
        
        # Generate barcode if enabled
        if settings['show_barcode']:
            try:
                import barcode
                from barcode.writer import ImageWriter
                import io
                import base64
                
                # Try to create barcode (Code128 is most versatile)
                code_class = barcode.get_barcode_class('code128')
                barcode_instance = code_class(data['code'], writer=ImageWriter())
                
                # Generate barcode image with height < 0.5cm (5mm)
                # Use reasonable module width for scanning while keeping compact
                buffer = io.BytesIO()
                barcode_instance.write(buffer, options={
                    'module_height': 4.0,   # 4mm height (< 0.5cm requirement)
                    'module_width': 0.15,   # 0.15mm per module (scannable minimum)
                    'quiet_zone': 1.0,      # 1mm quiet zone for scanning
                    'text_distance': 1,
                    'font_size': 6,
                    'write_text': False     # Disable text below barcode to save space
                })
                
                # Convert to base64 for transmission
                buffer.seek(0)
                barcode_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                print_context['barcode_image'] = f'data:image/png;base64,{barcode_base64}'
                
            except Exception as barcode_error:
                logging.warning(f'Failed to generate barcode: {barcode_error}')
                print_context['barcode_image'] = None
        
        # Send to printer service with printer name
        from app.helpers.helpers import send_to_printer_service
        result = send_to_printer_service(
            command={
                'action': 'printer/price_tag',
                'printContext': print_context
            },
            printer_name=data['printer_name']
        )
        
        return AppResponse.success({
            'status': 'Price tag sent to printer',
            'printer_response': result
        }).to_flask_tuple()
        
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_PRINT_PRICE_TAG}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error printing price tag').to_flask_tuple()
