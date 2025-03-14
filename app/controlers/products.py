from flask import jsonify, Blueprint
from flask_jwt_extended import jwt_required
from app.connections.connections import DB_manager
import logging

from app.models.products import Products

routesProducts = Blueprint('routes-products', __name__)

@routesProducts.route('/api/product/id/<string:id>', methods=['GET'])
def get_product_by_id(id):
    try:
        return jsonify(Products.get_by_id(id))
    except Exception as e:
        logging.error(f'/api/product/id/<string:id>: {e}')
        return jsonify({"error": "not product finded"}), 404