from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.models.products import Products

routesProducts = Blueprint('routes-products', __name__)

@routesProducts.route('/api/products', methods=['GET'])
def get_all_products():
    try:
        return jsonify(Products.getAll())
    except Exception as e:
        logging.info(f'/api/products: {e}.')
        return jsonify({"error": "could not fetch products"}), 404

@routesProducts.route('/api/product/code/<string:code>', methods=['GET'])
def get_product_by_id(code):
    try:
        return jsonify(Products.get(code))
    except Exception as e:
        logging.info(f'/api/product/code/<string:id>: {e}. Code: {code}')
        return jsonify({"error": "not product finded"}), 404
    
@routesProducts.route('/api/product/description/<string:description>', methods=['GET'])
def get_product_by_description(description):
    try:
        ans = Products.get_by_description(description)
        
        return jsonify(ans)
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.info(f'/api/product/description/<string:description>. Error: {e}. Data recieved: {description}')
        return jsonify({"error": "not product finded"}), 404
    
@routesProducts.route('/api/product/siblings/<string:code>', methods=['GET'])
def get_siblings(code):
    try:
        return jsonify(Products.get_siblings(code))
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/siblings/<string:code>. Error: {e}. Data recieved: {code}')
        return jsonify({"error": "siblings not found"}), 404
    
@routesProducts.route('/api/product/create', methods=['POST'])
def create_product():
    try:
        data = dict(request.get_json())
        Products.create(data)
        return jsonify({'message' : 'product created'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/create. Error: {e}. Data recieved: {data}')
        return jsonify({"error": "not product created"}), 400
    
@routesProducts.route('/api/product/update', methods=['PUT'])
def update_product():
    try:
        data = dict(request.get_json())
        Products.update(data)
        return jsonify({'message' : 'product updated'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/create. Error: {e}. Data recieved: {data}')
        return jsonify({"error": "not product updated"}), 400
    
@routesProducts.route('/api/product/<string:code>/update/inventory/<float:cantity>', methods=['PUT'])
def update_inventory(code: str, cantity: float):
    try:
        Products.update_inventory(code, cantity)
        return jsonify({'message' : 'product inventory updated'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/<string:code>/update/inventory/<float:cantity>. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return jsonify({"error": "product inventory not updated"}), 400
    
@routesProducts.route('/api/product/<string:code>/add/inventory/<float:cantity>', methods=['PUT'])
def add_inventory(code: str, cantity: float):
    try:
        Products.add_inventory(code, cantity)
        return jsonify({'message' : 'product inventory added'})

    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/<string:code>/add/inventory/<float:cantity>. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return jsonify({"error": "product inventory not added"}), 400
    
@routesProducts.route('/api/product/<string:code>/remove/inventory/<float:cantity>', methods=['PUT'])
def remove_inventory(code: str, cantity: float):
    try:
        Products.remove_inventory(code, cantity)
        return jsonify({'message' : 'product inventory added'})

    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/<string:code>/remove/inventory/<float:cantity>. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return jsonify({"error": "product inventory not removed"}), 400
    
@routesProducts.route('/api/product/delete/<string:code>', methods=['DELETE'])
def delete_product(code):
    try:
        Products.delete(code)
        return jsonify({'message' : 'product deleted'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/delete/<string:code>. Error: {e}. Data recieved: {code}')
        return jsonify({"error": "not product deleted"}), 400

@routesProducts.route('/api/product/departments', methods=['GET'])
def get_all_departments():
    try:
        return jsonify({
            'departments': Products.Departments.get_all()
        })
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.info(f'/api/product/departments: {e}.')
        return jsonify({"error": "not product finded"}), 500
    
@routesProducts.route('/api/product/departments/<int:code>', methods=['GET'])
def get_department(code):
    try:
        return jsonify(Products.Departments.get(code))
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.info(f'/api/product/departments/<int:code>: {e}. Code: {code}')
        return jsonify({"error": "not product finded"}), 500


@routesProducts.route('/api/product/departments/create/<string:description>', methods=['POST'])
def create_department(description):
    try:
        Products.Departments.create(description)
        return jsonify({'message' : 'department created'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/departments/create/<string:description>. Error: {e}. Data recieved: {description}')
        return jsonify({"error": "department could not be created"}), 500

@routesProducts.route('/api/product/departments/update/<string:code>/description/<int:description>', methods=['PUT'])
def update_department(code: int, description: str):
    try:
        Products.Departments.update(code, description)
        return jsonify({'message' : 'department updated'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/departments/update/<string:code>/description/<int:description>. Error: {e}. Data recieved: {description}')
        return jsonify({"error": "department could not be updated"}), 404
    
@routesProducts.route('/api/product/departments/delete/<int:code>', methods=['DELETE'])
def delete_department(code: int):
    try:
        Products.Departments.delete(code)
        return jsonify({'message' : 'department deleted'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/departments/delete/<int:code>. Error: {e}. Data recieved: {code}')
        return jsonify({"error": "department could not be delted"}), 404
    
@routesProducts.route('/api/product/associates/parent/<string:parent_code>', methods=['GET'])
def get_raw_data(parent_code: str):
    try:
        return jsonify(Products.Associates_codes.get_raw_data(parent_code))
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/associates/parent/<string:parent_code>. Error: {e}. Data recieved: {parent_code}')
        return jsonify({"error": "associate code cuold not be fetched"}), 404    
    
@routesProducts.route('/api/product/associates/create', methods=['POST'])
def create_associate():
    try:
        data = {
            'code': request.args.get('code'),
            'parent_code': request.args.get('parent'),
            'tag': request.args.get('tag')
        }

        Products.Associates_codes.create(data)
        return jsonify({'message' : 'associate product created'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/associates/create. Error: {e}. Data recieved: {data}')
        return jsonify({"error": "associate code cuold not be created"}), 400    
    
@routesProducts.route('/api/product/associates/update', methods=['PUT'])
def update_associate():
    try:
        data = {
            'code': request.args.get('code'),
            'parent_code': request.args.get('parent'),
            'tag': request.args.get('tag'),
            'original_code': request.args.get('originalCode')
        }
        Products.Associates_codes.update(data)
        return jsonify({'message' : 'associate product updated'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/associates/update. Error: {e}. Data recieved: {data}')
        return jsonify({"error": "associate code cuold not be updated"}), 400 
    
@routesProducts.route('/api/product/associates/delete/<string:code>', methods=['DELETE'])
def delete_associate(code: str):
    try:
        Products.Associates_codes.delete(code)
        return jsonify({'message' : 'associate product deleted'})
    
    except ValueError as e:
        return jsonify({'error': f'{e}'}), 422
    except Exception as e:
        logging.error(f'/api/product/associates/delete/<string:code>. Error: {e}. Data recieved: {code}')
        return jsonify({"error": "associate code cuold not be deleted"}), 500 