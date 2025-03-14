from flask import jsonify, Blueprint, request
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
        logging.info(f'/api/product/id/<string:id>: {e}')
        return jsonify({"error": "not product finded"}), 404
    
@routesProducts.route('/api/product/description/<string:des>', methods=['GET'])
def search_products_by_description(des):
    try:
        ans = Products.search_by_description(des)
        if len(ans) < 1:
            raise 'Not finded'
        
        return jsonify(ans)
    except Exception as e:
        logging.info(f'/api/product/description/<string:des>: {e}')
        return jsonify({"error": "not product finded"}), 404
    
@routesProducts.route('/api/product/create', methods=['POST'])
def create_product():
    try:
        data = dict(request.get_json())
        Products.create(data)
        return jsonify({'message' : 'product created'})
    
    except Exception as e:
        logging.error(f'/api/product/description/<string:des>: {e}. Data recieved: {data}')
        return jsonify({"error": "not product created"}), 400