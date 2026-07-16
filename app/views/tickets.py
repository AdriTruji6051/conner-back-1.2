from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.controlers.tickets import tickets_manager
from app.models.tickets import Tickets
from app.helpers.helpers import AppResponse, ValidationError, log_request_safely
from app.sockets.tickets import broadcast_ticket_update
from app.routes_constants import (
    ROUTE_QUICKSALE_TICKET, ROUTE_CREATE_TICKET, ROUTE_GET_TICKET_KEYS,
    ROUTE_GET_TICKET_KEYS_SHARED, ROUTE_SET_TICKET_SHARED, ROUTE_GET_TICKET, ROUTE_GET_TICKETS_BY_DATE,
    ROUTE_GET_PRODUCTS_IN_TICKET, ROUTE_TOOGLE_WHOLESALE, ROUTE_ADD_PRODUCT_TICKET,
    ROUTE_REMOVE_PRODUCT_TICKET, ROUTE_SAVE_TICKET, ROUTE_ADD_COMMON_PRODUCT_TICKET,
    ROUTE_MODIFY_SAVED_TICKET, ROUTE_SET_PRODUCT_QUANTITY, ROUTE_UPDATE_PRODUCT_WHOLESALE_PRICE,
    ROUTE_REPRINT_TICKET
)

TICKET_MANAGER = tickets_manager()

routesTickets = Blueprint('routes-tickets', __name__)

# UI note: these endpoints now return a list of ticket objects with `id` and `shared`.
# Example response body: [{"id": 1, "shared": false}, {"id": 2, "shared": true}]
def _serialize_ticket_keys(keys):
    return [
        {
            'id': key,
            'shared': bool(tickets_manager.tickets_dict.get(key, {}).get('shared', False))
        }
        for key in sorted(keys)
    ]

@routesTickets.route(ROUTE_CREATE_TICKET, methods=['POST'])
@jwt_required()
def create_ticket():
    try:
        current_user = get_jwt_identity()
        ipv4 = request.remote_addr
        ticket_key = TICKET_MANAGER.add(ipv4)
        log_request_safely(ROUTE_CREATE_TICKET, {'user': current_user, 'ticket_key': ticket_key})
        return AppResponse.created(ticket_key).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_CREATE_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error creating ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_TICKET_KEYS, methods=['GET'])
def get_keys_by_ipv4():
    try:
        ipv4 = request.remote_addr
        return AppResponse.success(_serialize_ticket_keys(TICKET_MANAGER.get_keys(ipv4))).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_TICKET_KEYS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error fetching ticket keys').to_flask_tuple()

@routesTickets.route(ROUTE_SET_TICKET_SHARED, methods=['PUT'])
def set_ticket_shared(ticket_key):
    try:
        data = request.get_json(silent=True) or {}
        shared = data.get('shared')
        if shared is None:
            shared = request.args.get('shared')
        if shared is None:
            raise ValueError('shared field is required')

        if isinstance(shared, str):
            cleaned = shared.strip().lower()
            if cleaned in ('true', '1', 'yes', 'y'):
                shared = True
            elif cleaned in ('false', '0', 'no', 'n'):
                shared = False
            else:
                raise ValueError('shared must be a boolean value')
        else:
            shared = bool(shared)

        result = TICKET_MANAGER.set_ticket_shared(ticket_key, shared, ipv4=request.remote_addr)
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_SET_TICKET_SHARED}. Catch: {e}. Ticket key: {ticket_key}.')
        return AppResponse.server_error('Unexpected error updating ticket shared status').to_flask_tuple()

@routesTickets.route(ROUTE_GET_TICKET_KEYS_SHARED, methods=['GET'])
def get_all_keys():
    try:
        shared_keys_only = request.args.get('sharedKeysOnly', 'false').lower() in ('true', '1', 'yes', 'y')
        print(f"Shared keys only: {shared_keys_only}")
        return AppResponse.success(_serialize_ticket_keys(TICKET_MANAGER.get_keys(shared_only=shared_keys_only))).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_TICKET_KEYS_SHARED}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error fetching shared ticket keys').to_flask_tuple()

@routesTickets.route(ROUTE_GET_TICKET, methods=['GET'])
def get_ticket(key):
    try:
        return AppResponse.success(TICKET_MANAGER.get_ticket_info(key)).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_TICKET}. Catch: {e}. Key: {key}.')
        return AppResponse.server_error('Unexpected error fetching ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_TICKETS_BY_DATE, methods=['GET'])
def get_tickets_date(date):
    try:
        # Get pagination parameters from query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 50
        
        # Get paginated results
        result = Tickets.list_created_at(date, page=page, per_page=per_page)
        
        return AppResponse.success({
            'tickets': [t.to_dict() for t in result['tickets']],
            'date': date,
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'total_pages': result['total_pages']
            }
        }).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_TICKETS_BY_DATE}. Catch: {e}. Date: {date}.')
        return AppResponse.server_error('Unexpected error fetching tickets by date').to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_PRODUCTS_IN_TICKET, methods=['GET'])
def get_products_in_ticket(id):
    try:
        return AppResponse.success({
            'products': [p.to_dict() for p in Tickets.Product_in_ticket.get_by_ticket(id)],
            'id': id
        }).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_PRODUCTS_IN_TICKET}. Catch: {e}. Id: {id}.')
        return AppResponse.server_error('Unexpected error fetching products in ticket').to_flask_tuple()

@routesTickets.route(ROUTE_TOOGLE_WHOLESALE, methods=['POST'])
def toogle_wholesale(ticket_key):
    try:
        result = TICKET_MANAGER.toogle_ticket_wholesale(ticket_key, ipv4=request.remote_addr)
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_TOOGLE_WHOLESALE}. Catch: {e}. Ticket key: {ticket_key}.')
        return AppResponse.server_error('Unexpected error toggling wholesale').to_flask_tuple()
    
@routesTickets.route(ROUTE_ADD_PRODUCT_TICKET, methods=['POST'])
@jwt_required()
def add_product():
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        product_code = data.get('product_code')
        
        try:
            ticket_key = int(data.get('ticket_key')) if data.get('ticket_key') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'ticket_key': f'Must be a valid integer: {str(e)}'}]).to_flask_tuple()
        
        try:
            cantity = float(data.get('cantity')) if data.get('cantity') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'cantity': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        result = TICKET_MANAGER.add_product(ticket_key, product_code, cantity, ipv4=request.remote_addr)
        log_request_safely(ROUTE_ADD_PRODUCT_TICKET, {'user': current_user, 'ticket_key': ticket_key, 'product_code': product_code})
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_ADD_PRODUCT_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error adding product to ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_ADD_COMMON_PRODUCT_TICKET, methods=['POST'])
@jwt_required()
def add_common_product():
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        
        try:
            ticket_key = int(data.get('ticket_key')) if data.get('ticket_key') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'ticket_key': f'Must be a valid integer: {str(e)}'}]).to_flask_tuple()
        
        try:
            price = float(data.get('price')) if data.get('price') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'price': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        try:
            cantity = float(data.get('cantity', 1))
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'cantity': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        description = data.get('description', 'COMMONSALE')
        
        result = TICKET_MANAGER.add_common_product(ticket_key, price, cantity, description, ipv4=request.remote_addr)
        log_request_safely(ROUTE_ADD_COMMON_PRODUCT_TICKET, {'user': current_user, 'ticket_key': ticket_key, 'price': price})
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_ADD_COMMON_PRODUCT_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error adding common product to ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_REMOVE_PRODUCT_TICKET, methods=['POST'])
@jwt_required()
def remove_product():
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        product_code = data.get('product_code')
        
        try:
            ticket_key = int(data.get('ticket_key')) if data.get('ticket_key') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'ticket_key': f'Must be a valid integer: {str(e)}'}]).to_flask_tuple()
        
        try:
            cantity = float(data.get('cantity')) if data.get('cantity') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'cantity': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        result = TICKET_MANAGER.remove_product(ticket_key, product_code, cantity, ipv4=request.remote_addr)
        log_request_safely(ROUTE_REMOVE_PRODUCT_TICKET, {'user': current_user, 'ticket_key': ticket_key, 'product_code': product_code})
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_REMOVE_PRODUCT_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error removing product from ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_SET_PRODUCT_QUANTITY, methods=['POST'])
@jwt_required()
def set_product_quantity():
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        product_code = data.get('product_code')
        
        try:
            ticket_key = int(data.get('ticket_key')) if data.get('ticket_key') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'ticket_key': f'Must be a valid integer: {str(e)}'}]).to_flask_tuple()
        
        try:
            quantity = float(data.get('quantity')) if data.get('quantity') is not None else None
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'quantity': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        result = TICKET_MANAGER.set_product_quantity(ticket_key, product_code, quantity, ipv4=request.remote_addr)
        log_request_safely(ROUTE_SET_PRODUCT_QUANTITY, {'user': current_user, 'ticket_key': ticket_key, 'product_code': product_code})
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_SET_PRODUCT_QUANTITY}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error setting product quantity in ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_UPDATE_PRODUCT_WHOLESALE_PRICE, methods=['POST'])
@jwt_required()
def update_product_wholesale_price():
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        product_code = data.get('product_code')
        ticket_key = int(data.get('ticket_key')) if data.get('ticket_key') is not None else None
        wholesale_price = float(data.get('new_wholesale_price')) if data.get('new_wholesale_price') is not None else None

        result = TICKET_MANAGER.set_product_wholesale_price(ticket_key, product_code, wholesale_price, ipv4=request.remote_addr)
        log_request_safely(ROUTE_UPDATE_PRODUCT_WHOLESALE_PRICE, {'user': current_user, 'ticket_key': ticket_key, 'product_code': product_code})
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_PRODUCT_WHOLESALE_PRICE}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error updating wholesale price in ticket').to_flask_tuple()
    
@routesTickets.route(f'{ROUTE_SAVE_TICKET}/<int:ticket_key>', methods=['POST'])
@jwt_required()
def save_ticket(ticket_key):
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        notes = data.get('notes')
        
        total = data.get('total')
        if total is not None:
            try:
                total = float(total)
            except (TypeError, ValueError) as e:
                return AppResponse.validation_error([{'total': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
            
        print_many = data.get('print')
        if print_many is not None:
            try:
                print_many = int(print_many)
            except (TypeError, ValueError) as e:
                return AppResponse.validation_error([{'print': f'Must be a valid integer: {str(e)}'}]).to_flask_tuple()
            
        printer_name = data.get('printer_name')
        language = data.get('language', 'es-MX')  # Default to Spanish

        saved_id = TICKET_MANAGER.save(
            notes=notes, 
            ticket_key=ticket_key, 
            total=total, 
            ipv4=request.remote_addr,
            user_id=current_user.get('id', 0) if isinstance(current_user, dict) else 0,
            print_many=print_many, 
            printer_name=printer_name, 
            language=language
        )
        log_request_safely(ROUTE_SAVE_TICKET, {'user': current_user, 'ticket_key': ticket_key, 'saved_id': saved_id})
        # Notify any subscribed clients that the ticket was finalized/updated
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(saved_id).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_SAVE_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error saving ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_MODIFY_SAVED_TICKET, methods=['PUT'])
@jwt_required()
def modify_saved_ticket(ticket_id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        data['id'] = ticket_id
        result = Tickets.modify(data)
        log_request_safely(ROUTE_MODIFY_SAVED_TICKET, {'user': current_user, 'ticket_id': ticket_id})
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        msg = str(e)
        if 'not found' in msg.lower():
            return AppResponse.not_found(msg).to_flask_tuple()
        return AppResponse.unprocessable(msg).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_MODIFY_SAVED_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error modifying saved ticket').to_flask_tuple()

@routesTickets.route(ROUTE_QUICKSALE_TICKET, methods=['POST'])
@jwt_required()
def quicksale_ticket(amount):
    try:
        current_user = get_jwt_identity()
        amount = float(amount)
        data = request.get_json(silent=True) or {}
        printer_name = data.get('printer_name')
        ticket_id = TICKET_MANAGER.quicksale(
            amount=amount, 
            ipv4=request.remote_addr,
            user_id=current_user.get('id', 0) if isinstance(current_user, dict) else 0,
            printer_name=printer_name
        )
        log_request_safely(ROUTE_QUICKSALE_TICKET, {'user': current_user, 'amount': amount, 'ticket_id': ticket_id})
        return AppResponse.created(ticket_id).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_QUICKSALE_TICKET}. Catch: {e}.')

@routesTickets.route(ROUTE_REPRINT_TICKET, methods=['POST'])
@jwt_required()
def reprint_ticket(ticket_id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        printer_name = data.get('printer_name')
        print_many = data.get('print', 1)
        language = data.get('language', 'es-MX')  # Default to Spanish
        
        if print_many is not None:
            print_many = int(print_many)
        
        if not printer_name:
            raise ValueError('printer_name is required')
        
        # Get ticket from database
        ticket = Tickets.get(ticket_id)
        log_request_safely(ROUTE_REPRINT_TICKET, {'user': current_user, 'ticket_id': ticket_id})
        
        # Get products in ticket
        products = Tickets.Product_in_ticket.get_by_ticket(ticket_id)
        
        # Calculate total_price for each product (not stored in DB)
        products_list = []
        for p in products:
            product_dict = p.to_dict()
            # Calculate total_price = sale_price * cantity
            product_dict['total_price'] = round(p.sale_price * p.cantity, 2)
            products_list.append(product_dict)
        
        # Structure ticket info for printing
        ticket_info = {
            'products': products_list,
            'products_count': ticket.products_count,
            'articles_count': len(products),
            'sub_total': ticket.sub_total,
            'discount': ticket.discount if ticket.discount else 0.0,
            'wholesale_active': False,  # Not stored in DB, set to False for reprints
            'profit': ticket.profit,
            'total': ticket.total,
            'notes': ticket.notes or '',
        }
        
        # Print ticket with language support
        from app.controlers.printers import Printers
        printers = Printers()
        printers.print_ticket(ticket_info, ticket_id, ticket.notes or '', printer_name, request.remote_addr, print_many, language)
        
        return AppResponse.success({'ticket_id': ticket_id, 'printed': print_many}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        msg = str(e)
        if 'not found' in msg.lower():
            return AppResponse.not_found(msg).to_flask_tuple()
        return AppResponse.unprocessable(msg).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_REPRINT_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error reprinting ticket').to_flask_tuple()

        return AppResponse.server_error('Unexpected error creating quicksale ticket').to_flask_tuple()