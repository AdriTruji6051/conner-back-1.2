from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.controlers.tickets import Tickets_manager
from app.models.tickets import Tickets
from app.helpers.helpers import AppResponse, ValidationError
from app.sockets.tickets import broadcast_ticket_update
from app.routes_constants import (
    ROUTE_QUICKSALE_TICKET, ROUTE_CREATE_TICKET, ROUTE_GET_TICKET_KEYS,
    ROUTE_GET_TICKET_KEYS_SHARED, ROUTE_GET_TICKET, ROUTE_GET_TICKETS_BY_DATE,
    ROUTE_GET_PRODUCTS_IN_TICKET, ROUTE_TOOGLE_WHOLESALE, ROUTE_ADD_PRODUCT_TICKET,
    ROUTE_REMOVE_PRODUCT_TICKET, ROUTE_SAVE_TICKET, ROUTE_ADD_COMMON_PRODUCT_TICKET,
    ROUTE_MODIFY_SAVED_TICKET
)

TICKET_MANAGER = Tickets_manager()

routesTickets = Blueprint('routes-tickets', __name__)

@routesTickets.route(ROUTE_CREATE_TICKET, methods=['POST'])
def create_ticket():
    try:
        return AppResponse.created(TICKET_MANAGER.add(request.remote_addr)).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_CREATE_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error creating ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_TICKET_KEYS, methods=['GET'])
def get_keys_by_ipv4():
    try:
        ipv4 = request.remote_addr
        return AppResponse.success(list(TICKET_MANAGER.get_keys(ipv4))).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_TICKET_KEYS}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error fetching ticket keys').to_flask_tuple()

@routesTickets.route(ROUTE_GET_TICKET_KEYS_SHARED, methods=['GET'])
def get_all_keys():
    try:
        return AppResponse.success(list(TICKET_MANAGER.get_keys())).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_TICKET_KEYS_SHARED}. Catch: {e}.')
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
        logging.error(f'{ROUTE_GET_TICKET}. Catch: {e}. Key: {key}.')
        return AppResponse.server_error('Unexpected error fetching ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_TICKETS_BY_DATE, methods=['GET'])
def get_tickets_date(date):
    try:
        return AppResponse.success({
            'tickets': [t.to_dict() for t in Tickets.list_created_at(date)],
            'date': date
        }).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_TICKETS_BY_DATE}. Catch: {e}. Date: {date}.')
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
        logging.error(f'{ROUTE_GET_PRODUCTS_IN_TICKET}. Catch: {e}. Id: {id}.')
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
        logging.error(f'{ROUTE_TOOGLE_WHOLESALE}. Catch: {e}. Ticket key: {ticket_key}.')
        return AppResponse.server_error('Unexpected error toggling wholesale').to_flask_tuple()
    
@routesTickets.route(ROUTE_ADD_PRODUCT_TICKET, methods=['POST'])
def add_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        result = TICKET_MANAGER.add_product(ticket_key, product_code, cantity, ipv4=request.remote_addr)
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_ADD_PRODUCT_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error adding product to ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_ADD_COMMON_PRODUCT_TICKET, methods=['POST'])
def add_common_product():
    try:
        ticket_key = request.args.get('ticket_key', type=int)
        price = request.args.get('price', type=float)
        cantity = request.args.get('cantity', type=float, default=1)
        description = request.args.get('description', default='COMMONSALE')
        result = TICKET_MANAGER.add_common_product(ticket_key, price, cantity, description, ipv4=request.remote_addr)
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_ADD_COMMON_PRODUCT_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error adding common product to ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_REMOVE_PRODUCT_TICKET, methods=['POST'])
def remove_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        result = TICKET_MANAGER.remove_product(ticket_key, product_code, cantity, ipv4=request.remote_addr)
        broadcast_ticket_update(ticket_key)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_REMOVE_PRODUCT_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error removing product from ticket').to_flask_tuple()
    
@routesTickets.route(f'{ROUTE_SAVE_TICKET}/<int:ticket_key>', methods=['POST'])
def save_ticket(ticket_key):
    try:
        data = request.get_json(silent=True) or {}
        notes = data.get('notes')
        
        total = data.get('total')
        if total is not None:
            total = float(total)
            
        print_many = data.get('print')
        if print_many is not None:
            print_many = int(print_many)
            
        printer_name = data.get('printer_name')

        return AppResponse.success(TICKET_MANAGER.save(notes=notes, ticket_key=ticket_key, total=total, ipv4=request.remote_addr, print_many=print_many, printer_name=printer_name)).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_SAVE_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error saving ticket').to_flask_tuple()
    
@routesTickets.route(ROUTE_MODIFY_SAVED_TICKET, methods=['PUT'])
def modify_saved_ticket(ticket_id):
    try:
        data = request.get_json(silent=True) or {}
        data['id'] = ticket_id
        result = Tickets.modify(data)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        msg = str(e)
        if 'not found' in msg.lower():
            return AppResponse.not_found(msg).to_flask_tuple()
        return AppResponse.unprocessable(msg).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_MODIFY_SAVED_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error modifying saved ticket').to_flask_tuple()

@routesTickets.route(ROUTE_QUICKSALE_TICKET, methods=['POST'])
def quicksale_ticket(amount):
    try:
        amount = float(amount)
        data = request.get_json(silent=True) or {}
        printer_name = data.get('printer_name')
        return AppResponse.created(TICKET_MANAGER.quicksale(amount=amount, ipv4=request.remote_addr, printer_name=printer_name)).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_QUICKSALE_TICKET}. Catch: {e}.')
        return AppResponse.server_error('Unexpected error creating quicksale ticket').to_flask_tuple()