from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.controlers.tickets import Tickets_manager
from app.models.tickets import Tickets
from app.helpers.helpers import AppResponse
from app.routes_constants import (
    ROUTE_QUICKSALE_TICKET, ROUTE_CREATE_TICKET, ROUTE_GET_TICKET_KEYS,
    ROUTE_GET_TICKET_KEYS_SHARED, ROUTE_GET_TICKET, ROUTE_GET_TICKETS_BY_DATE,
    ROUTE_GET_PRODUCTS_IN_TICKET, ROUTE_TOOGLE_WHOLESALE, ROUTE_ADD_PRODUCT_TICKET,
    ROUTE_REMOVE_PRODUCT_TICKET, ROUTE_SAVE_TICKET
)

TICKET_MANAGER = Tickets_manager()

routesTickets = Blueprint('routes-tickets', __name__)

@routesTickets.route(ROUTE_QUICKSALE_TICKET, methods=['POST'])
def quicksale_ticket(amount):
    try:
        amount = float(amount)
        return AppResponse.created({'created_key': TICKET_MANAGER.quicksale(amount, request.remote_addr)}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/new. Catch: {e}.')
        return AppResponse.server_error("could not create new ticket").to_flask_tuple()

@routesTickets.route(ROUTE_CREATE_TICKET, methods=['POST'])
def create_ticket():
    try:
        return AppResponse.created({'created_key': Tickets_manager.add(request.remote_addr)}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/new. Catch: {e}.')
        return AppResponse.server_error("could not create new ticket").to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_TICKET_KEYS, methods=['GET'])
def get_keys_by_ipv4():
    try:
        ipv4 = request.remote_addr
        return AppResponse.success({'keys': list(TICKET_MANAGER.get_keys(ipv4))}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/get/keys. Catch: {e}. Key: {ipv4}.')
        return AppResponse.server_error(f"could not fetch the ticket keys for {ipv4}").to_flask_tuple()

@routesTickets.route(ROUTE_GET_TICKET_KEYS_SHARED, methods=['GET'])
def get_all_keys():
    try:
        return AppResponse.success({'keys': list(TICKET_MANAGER.get_keys())}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/get/keys/shared. Catch: {e}.')
        return AppResponse.server_error("could not fetch the shared ticket keys").to_flask_tuple()

@routesTickets.route(ROUTE_GET_TICKET, methods=['GET'])
def get_ticket(key):
    try:
        return AppResponse.success(TICKET_MANAGER.get_ticket_info(key)).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/get/<int:key>. Catch: {e}. Key: {key}. Avaliable keys: {TICKET_MANAGER.get_keys()}')
        return AppResponse.not_found("could not fetch the ticket").to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_TICKETS_BY_DATE, methods=['GET'])
def get_tickets_date(date):
    try:
        return AppResponse.success({
            'tickets': [t.to_dict() for t in Tickets.list_created_at(date)],
            'date': date
        }).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/get/date/<string:date>. Catch: {e}. Date: {date}.')
        return AppResponse.not_found(f"could not fetch the tickets with date {date}").to_flask_tuple()
    
@routesTickets.route(ROUTE_GET_PRODUCTS_IN_TICKET, methods=['GET'])
def get_products_in_ticket(id):
    try:
        return AppResponse.success({
            'products': [p.to_dict() for p in Tickets.Product_in_ticket.get_by_ticket(id)],
            'id': id
        }).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/get/date/<string:date>. Catch: {e}. Id: {id}.')
        return AppResponse.not_found(f"could not fetch the products in ticket with date {id}").to_flask_tuple()

@routesTickets.route(ROUTE_TOOGLE_WHOLESALE, methods=['POST'])
def toogle_wholesale(ticket_key):
    try:
        return AppResponse.success(TICKET_MANAGER.toogle_ticket_wholesale(ticket_key)).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/toogle/wholesale/<int>. Catch: {e}. Ticket key: {ticket_key}. Avaliable keys: {TICKET_MANAGER.get_keys()}')
        return AppResponse.server_error(f"could not save toogle wholesale at ticket with key {ticket_key}").to_flask_tuple()
    
@routesTickets.route(ROUTE_ADD_PRODUCT_TICKET, methods=['POST'])
def add_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        return AppResponse.success(TICKET_MANAGER.add_product(ticket_key, product_code, cantity)).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/add. Catch: {e}. Product_code: {product_code}. Ticket_key: {ticket_key}. Cantity: {cantity}')
        return AppResponse.bad_request("could not add product to ticket").to_flask_tuple()
    
@routesTickets.route(ROUTE_REMOVE_PRODUCT_TICKET, methods=['POST'])
def remove_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        return AppResponse.success(TICKET_MANAGER.remove_product(ticket_key, product_code, cantity)).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/remove. Catch: {e}. Product_code: {product_code}. Ticket_key: {ticket_key}')
        return AppResponse.bad_request("could not remove product from ticket").to_flask_tuple()
    
@routesTickets.route(ROUTE_SAVE_TICKET, methods=['POST'])
def save_ticket():
    try:
        notes = request.args.get('notes')
        ticket_key = request.args.get('ticket_key', type=int)
        total = request.args.get('total', type=float)
        print_many = request.args.get('print', type=int)
        return AppResponse.success(TICKET_MANAGER.save(notes=notes, ticket_key=ticket_key, total=total, print_many=print_many)).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/ticket/save. Catch: {e}. Notes: {notes}. Ticket_key: {ticket_key}. Total: {total}')
        return AppResponse.bad_request("could not save ticket").to_flask_tuple()