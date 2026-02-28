from flask import Blueprint, request
import logging
from sqlalchemy.exc import IntegrityError

from app.models.products import Products
from app.helpers.helpers import AppResponse, ValidationError
from app.routes_constants import (
    ROUTE_GET_PRODUCT_BY_CODE, ROUTE_GET_PRODUCT_BY_DESCRIPTION,
    ROUTE_GET_PRODUCT_SIBLINGS, ROUTE_CREATE_PRODUCT, ROUTE_UPDATE_PRODUCT, ROUTE_DELETE_PRODUCT,
    ROUTE_UPDATE_INVENTORY, ROUTE_ADD_INVENTORY, ROUTE_REMOVE_INVENTORY,
    ROUTE_GET_ALL_DEPARTMENTS, ROUTE_GET_DEPARTMENT, ROUTE_CREATE_DEPARTMENT,
    ROUTE_UPDATE_DEPARTMENT, ROUTE_DELETE_DEPARTMENT,
    ROUTE_GET_ASSOCIATES_RAW_DATA, ROUTE_CREATE_ASSOCIATE, ROUTE_UPDATE_ASSOCIATE, ROUTE_DELETE_ASSOCIATE
)

routesProducts = Blueprint('routes-products', __name__)


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

@routesProducts.route(ROUTE_GET_PRODUCT_BY_CODE, methods=['GET'])
def get_product_by_id(code):
    try:
        return AppResponse.success(Products.get(code)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_PRODUCT_BY_CODE}: {e}. Code: {code}')
        return AppResponse.server_error('Unexpected error retrieving product').to_flask_tuple()
    
@routesProducts.route(ROUTE_GET_PRODUCT_BY_DESCRIPTION, methods=['GET'])
def get_product_by_description(description):
    try:
        description = description.strip()
        page, page_size = _parse_pagination_args(request.args)
        ans = Products.get_by_description(description, page=page, page_size=page_size)
        return AppResponse.success(ans).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_PRODUCT_BY_DESCRIPTION}. Error: {e}. Data recieved: {description}')
        return AppResponse.server_error('Unexpected error searching products').to_flask_tuple()
    
@routesProducts.route(ROUTE_GET_PRODUCT_SIBLINGS, methods=['GET'])
def get_siblings(code):
    try:
        return AppResponse.success(Products.get_siblings(code)).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_PRODUCT_SIBLINGS}. Error: {e}. Data recieved: {code}')
        return AppResponse.server_error('Unexpected error retrieving siblings').to_flask_tuple()
    
@routesProducts.route(ROUTE_CREATE_PRODUCT, methods=['POST'])
def create_product():
    try:
        data = dict(request.get_json())
        Products.create(data)
        return AppResponse.created({'message': 'product created'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A product with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_CREATE_PRODUCT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error creating product').to_flask_tuple()
    
@routesProducts.route(ROUTE_UPDATE_PRODUCT, methods=['PUT'])
def update_product():
    try:
        data = dict(request.get_json())
        Products.update(data)
        return AppResponse.success({'message': 'product updated'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A product with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_UPDATE_PRODUCT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error updating product').to_flask_tuple()
    
@routesProducts.route(ROUTE_UPDATE_INVENTORY, methods=['PUT'])
def update_inventory(code: str, cantity: float):
    try:
        Products.update_inventory(code, cantity)
        return AppResponse.success({'message': 'product inventory updated'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_UPDATE_INVENTORY}. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return AppResponse.server_error('Unexpected error updating inventory').to_flask_tuple()
    
@routesProducts.route(ROUTE_ADD_INVENTORY, methods=['PUT'])
def add_inventory(code: str, cantity: float):
    try:
        Products.add_inventory(code, cantity)
        return AppResponse.success({'message': 'product inventory added'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_ADD_INVENTORY}. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return AppResponse.server_error('Unexpected error adding inventory').to_flask_tuple()
    
@routesProducts.route(ROUTE_REMOVE_INVENTORY, methods=['PUT'])
def remove_inventory(code: str, cantity: float):
    try:
        Products.remove_inventory(code, cantity)
        return AppResponse.success({'message': 'product inventory removed'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_REMOVE_INVENTORY}. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return AppResponse.server_error('Unexpected error removing inventory').to_flask_tuple()
    
@routesProducts.route(ROUTE_DELETE_PRODUCT, methods=['DELETE'])
def delete_product(code):
    try:
        Products.delete(code)
        return AppResponse.success({'message': 'product deleted'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_DELETE_PRODUCT}. Error: {e}. Data recieved: {code}')
        return AppResponse.server_error('Unexpected error deleting product').to_flask_tuple()

@routesProducts.route(ROUTE_GET_ALL_DEPARTMENTS, methods=['GET'])
def get_all_departments():
    try:
        page, page_size = _parse_pagination_args(request.args)
        result = Products.Departments.get_all(page, page_size)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_ALL_DEPARTMENTS}: {e}.')
        return AppResponse.server_error('Unexpected error retrieving departments').to_flask_tuple()
    
@routesProducts.route(ROUTE_GET_DEPARTMENT, methods=['GET'])
def get_department(code):
    try:
        return AppResponse.success(Products.Departments.get(code).to_dict()).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_DEPARTMENT}: {e}. Code: {code}')
        return AppResponse.server_error('Unexpected error retrieving department').to_flask_tuple()


@routesProducts.route(ROUTE_CREATE_DEPARTMENT, methods=['POST'])
def create_department(description):
    try:
        Products.Departments.create(description)
        return AppResponse.created({'message': 'department created'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A department with that description already exists').to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_CREATE_DEPARTMENT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error creating department').to_flask_tuple()

@routesProducts.route(ROUTE_UPDATE_DEPARTMENT, methods=['PUT'])
def update_department(code: int, description: str):
    try:
        Products.Departments.update(code, description)
        return AppResponse.success({'message': 'department updated'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_UPDATE_DEPARTMENT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error updating department').to_flask_tuple()
    
@routesProducts.route(ROUTE_DELETE_DEPARTMENT, methods=['DELETE'])
def delete_department(code: int):
    try:
        Products.Departments.delete(code)
        return AppResponse.success({'message': 'department deleted'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_DELETE_DEPARTMENT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error deleting department').to_flask_tuple()
    
@routesProducts.route(ROUTE_GET_ASSOCIATES_RAW_DATA, methods=['GET'])
def get_raw_data(parent_code: str):
    try:
        page, page_size = _parse_pagination_args(request.args)
        result = Products.Associates_codes.get_raw_data(parent_code, page, page_size)
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_ASSOCIATES_RAW_DATA}. Error: {e}.')
        return AppResponse.server_error('Unexpected error retrieving associate codes').to_flask_tuple()    
    
@routesProducts.route(ROUTE_CREATE_ASSOCIATE, methods=['POST'])
def create_associate():
    try:
        data = {
            'code': request.args.get('code'),
            'parent_code': request.args.get('parent'),
            'tag': request.args.get('tag')
        }

        Products.Associates_codes.create(data)
        return AppResponse.created({'message': 'associate product created'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('An associate with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_CREATE_ASSOCIATE}. Error: {e}.')
        return AppResponse.server_error('Unexpected error creating associate code').to_flask_tuple()    
    
@routesProducts.route(ROUTE_UPDATE_ASSOCIATE, methods=['PUT'])
def update_associate():
    try:
        data = {
            'code': request.args.get('code'),
            'parent_code': request.args.get('parent'),
            'tag': request.args.get('tag'),
            'original_code': request.args.get('originalCode')
        }
        Products.Associates_codes.update(data)
        return AppResponse.success({'message': 'associate product updated'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('An associate with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_UPDATE_ASSOCIATE}. Error: {e}.')
        return AppResponse.server_error('Unexpected error updating associate code').to_flask_tuple() 
    
@routesProducts.route(ROUTE_DELETE_ASSOCIATE, methods=['DELETE'])
def delete_associate(code: str):
    try:
        Products.Associates_codes.delete(code)
        return AppResponse.success({'message': 'associate product deleted'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_DELETE_ASSOCIATE}. Error: {e}.')
        return AppResponse.server_error('Unexpected error deleting associate code').to_flask_tuple() 