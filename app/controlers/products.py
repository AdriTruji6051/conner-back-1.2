from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
from app.connections.connections import DB_manager
import logging

from app.models.products import Products

routesProducts = Blueprint('routes-products', __name__)

@routesProducts.route('/api/product/code/<string:code>', methods=['GET'])
def get_product_by_id(code):
    try:
        return jsonify(Products.get(code))
    except Exception as e:
        logging.info(f'/api/product/id/<string:id>: {e}. Code: {code}')
        return jsonify({"error": "not product finded"}), 404
    
@routesProducts.route('/api/product/description/<string:description>', methods=['GET'])
def search_products_by_description(description):
    try:
        ans = Products.search_by_description(description)
        if len(ans) < 1:
            raise 'Not finded'
        
        return jsonify(ans)
    except Exception as e:
        logging.info(f'/api/product/description/<string:description>. Error: {e}. Data recieved: {description}')
        return jsonify({"error": "not product finded"}), 404
    
@routesProducts.route('/api/product/create', methods=['POST'])
def create_product():
    try:
        data = dict(request.get_json())
        Products.create(data)
        return jsonify({'message' : 'product created'})
    
    except Exception as e:
        logging.error(f'/api/product/create. Error: {e}. Data recieved: {data}')
        return jsonify({"error": "not product created"}), 400
    
@routesProducts.route('/api/product/update', methods=['PUT'])
def update_product():
    try:
        data = dict(request.get_json())
        Products.update(data)
        return jsonify({'message' : 'product updated'})
    
    except Exception as e:
        logging.error(f'/api/product/create. Error: {e}. Data recieved: {data}')
        return jsonify({"error": "not product updated"}), 400
    
@routesProducts.route('/api/product/delete/<string:code>', methods=['DELETE'])
def delete_product(code):
    try:
        Products.delete(code)
        return jsonify({'message' : 'product deleted'})
    
    except Exception as e:
        logging.error(f'/api/product/delete/<string:code>. Error: {e}. Data recieved: {code}')
        return jsonify({"error": "not product deleted"}), 400