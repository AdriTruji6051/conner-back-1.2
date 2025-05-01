from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.controlers.tickets import Tickets_manager
from app.models.tickets import Tickets

TICKET_MANAGER = Tickets_manager()

routesTickets = Blueprint('routes-tickets', __name__)

@routesTickets.route('/api/ticket/quicksale/<amount>', methods=['POST'])
def quicksale_ticket(amount):
    try:
        amount = float(amount)
        return jsonify({
            'created_key': TICKET_MANAGER.quicksale(amount, request.remote_addr)
        })
    except Exception as e:
        logging.info(f'/api/ticket/new. Catch: {e}.')
        return jsonify({"error": "could not create new ticket"}), 500

@routesTickets.route('/api/ticket/new', methods=['POST'])
def create_ticket():
    try:
        return jsonify({
            'created_key': Tickets_manager.add(request.remote_addr)
        })
    except Exception as e:
        logging.info(f'/api/ticket/new. Catch: {e}.')
        return jsonify({"error": "could not create new ticket"}), 500
    
@routesTickets.route('/api/ticket/get/keys', methods=['GET'])
def get_keys_by_ipv4():
    try:
        ipv4 = request.remote_addr
        return jsonify(
            {'keys' : list(TICKET_MANAGER.get_keys(ipv4))}
        )
    except Exception as e:
        logging.info(f'/api/ticket/get/keys. Catch: {e}. Key: {ipv4}.')
        return jsonify({"error": f"could not fetch the ticket keys for {ipv4}"}), 500

@routesTickets.route('/api/ticket/get/keys/shared', methods=['GET'])
def get_all_keys():
    try:
        return jsonify(
            {'keys' : list(TICKET_MANAGER.get_keys())}
        )
    except Exception as e:
        logging.info(f'/api/ticket/get/keys/shared. Catch: {e}.')
        return jsonify({"error": "could not fetch the shared ticket keys"}), 500

@routesTickets.route('/api/ticket/get/<int:key>', methods=['GET'])
def get_ticket(key):
    try:
        return jsonify(
            TICKET_MANAGER.get_ticket_info(key)
        )
    except Exception as e:
        logging.info(f'/api/ticket/get/<int:key>. Catch: {e}. Key: {key}. Avaliable keys: {TICKET_MANAGER.get_keys()}')
        return jsonify({"error": "could not fetch the ticket"}), 404
    
@routesTickets.route('/api/ticket/get/date/<string:date>', methods=['GET'])
def get_tickets_date(date):
    try:
        return jsonify({
            'tickets': Tickets.list_created_at(date),
            'date': date
        })
    except Exception as e:
        logging.info(f'/api/ticket/get/date/<string:date>. Catch: {e}. Date: {date}.')
        return jsonify({"error": f"could not fetch the tickets with date {date}"}), 404
    
@routesTickets.route('/api/ticket/get/products/id/<int:id>', methods=['GET'])
def get_products_in_ticket(id):
    try:
        return jsonify({
            'products': Tickets.Product_in_ticket.get_by_ticket(id),
            'id': id
        })
    except Exception as e:
        logging.info(f'/api/ticket/get/date/<string:date>. Catch: {e}. Id: {id}.')
        return jsonify({"error": f"could not fetch the products in ticket with date {id}"}), 404

@routesTickets.route('/api/ticket/toogle/wholesale/<int:ticket_key>', methods=['POST'])
def toogle_wholesale(ticket_key):
    try:
        return jsonify(
            TICKET_MANAGER.toogle_ticket_wholesale(ticket_key)
        )
    except Exception as e:
        logging.info(f'/api/ticket/toogle/wholesale/<int>. Catch: {e}. Ticket key: {ticket_key}. Avaliable keys: {TICKET_MANAGER.get_keys()}')
        return jsonify({"error": f"could not save toogle wholesale at ticket with key {ticket_key}"}), 500
    
@routesTickets.route('/api/ticket/add', methods=['POST'])
def add_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        return jsonify(
            TICKET_MANAGER.add_product(ticket_key, product_code, cantity)
        )
    except Exception as e:
        logging.info(f'/api/ticket/add. Catch: {e}. Product_code: {product_code}. Ticket_key: {ticket_key}. Cantity: {cantity}')
        return jsonify({"error": "could not add product to ticket"}), 400
    
@routesTickets.route('/api/ticket/remove', methods=['POST'])
def remove_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        return jsonify(
            TICKET_MANAGER.remove_product(ticket_key, product_code, cantity)
        )
    except Exception as e:
        logging.info(f'/api/ticket/remove. Catch: {e}. Product_code: {product_code}. Ticket_key: {ticket_key}')
        return jsonify({"error": "could not remove product from ticket"}), 400
    
@routesTickets.route('/api/ticket/save', methods=['POST'])
def save_ticket():
    try:
        notes = request.args.get('notes')
        ticket_key = request.args.get('ticket_key', type=int)
        total = request.args.get('total', type=float)
        print_many = request.args.get('print', type=int)
        
        return jsonify(
            TICKET_MANAGER.save(notes=notes, ticket_key=ticket_key, total=total, print_many=print_many)
        )
    except Exception as e:
        logging.info(f'/api/ticket/save. Catch: {e}. Notes: {notes}. Ticket_key: {ticket_key}. Total: {total}')
        return jsonify({"error": "could not save ticket"}), 400