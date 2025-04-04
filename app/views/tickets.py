from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.controlers.tickets import Tickets_manager

routesTickets = Blueprint('routes-products', __name__)

@routesTickets.route('/api/ticket/new', methods=['POST'])
def create_ticket():
    try:
        return jsonify({
            'created_key': Tickets_manager.add(request.remote_addr)
        })
    except Exception as e:
        logging.info(f'/api/ticket/new. Catch: {e}.')
        return jsonify({"error": "could not create new ticket"}), 500
    
@routesTickets.route('/api/ticket/add', methods=['POST'])
def add_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        return jsonify(Tickets_manager.add_product(ticket_key, product_code, cantity))
    except Exception as e:
        logging.info(f'/api/ticket/add. Catch: {e}. Product_code: {product_code}. Ticket_key: {ticket_key}. Cantity: {cantity}')
        return jsonify({"error": "could not add product to ticket"}), 400
    
@routesTickets.route('/api/ticket/remove', methods=['POST'])
def remove_product():
    try:
        product_code = request.args.get('product_code')
        ticket_key = request.args.get('ticket_key', type=int)
        cantity = request.args.get('cantity', type=float)
        return jsonify(Tickets_manager.remove_product(ticket_key, product_code, cantity))
    except Exception as e:
        logging.info(f'/api/ticket/remove. Catch: {e}. Product_code: {product_code}. Ticket_key: {ticket_key}')
        return jsonify({"error": "could not remove product from ticket"}), 400