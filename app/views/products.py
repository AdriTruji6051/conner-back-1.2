from flask import Blueprint, request
import logging
from sqlalchemy.exc import IntegrityError
from app.auth import jwt_protected, get_current_user

from app.models.products import Products
from app.helpers.helpers import AppResponse, ValidationError, log_request_safely
from app.routes_constants import (
    ROUTE_GET_PRODUCT_BY_CODE, ROUTE_GET_PRODUCT_BY_DESCRIPTION,
    ROUTE_GET_PRODUCT_SIBLINGS, ROUTE_CREATE_PRODUCT, ROUTE_UPDATE_PRODUCT, ROUTE_DELETE_PRODUCT,
    ROUTE_UPDATE_INVENTORY, ROUTE_ADD_INVENTORY, ROUTE_REMOVE_INVENTORY,
    ROUTE_GET_ALL_DEPARTMENTS, ROUTE_GET_DEPARTMENT, ROUTE_CREATE_DEPARTMENT,
    ROUTE_UPDATE_DEPARTMENT, ROUTE_DELETE_DEPARTMENT,
    ROUTE_GET_ASSOCIATES_RAW_DATA, ROUTE_CREATE_ASSOCIATE, ROUTE_UPDATE_ASSOCIATE, ROUTE_DELETE_ASSOCIATE
)

routesProducts = Blueprint('routes-products', __name__)


def _parse_pagination_args(args, default_page: int = 1, default_page_size: int = 10, max_page_size: int = 100) -> tuple[int, int]:
    """Parse pagination query params, coercing to safe bounds instead of raising.
    
    Max page size reduced to 100 to prevent performance issues with large result sets.
    """
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
        logging.exception(f'{ROUTE_GET_PRODUCT_BY_CODE}: {e}. Code: {code}')
        return AppResponse.server_error('Unexpected error retrieving product').to_flask_tuple()
    
@routesProducts.route(ROUTE_GET_PRODUCT_BY_DESCRIPTION, methods=['GET'])
def get_product_by_description(description):
    try:
        description = description.strip()
        # Force pagination for all searches to prevent performance issues
        page, page_size = _parse_pagination_args(request.args, default_page_size=20)
        ans = Products.get_by_description(description, page=page, page_size=page_size)
        return AppResponse.success(ans).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_PRODUCT_BY_DESCRIPTION}. Error: {e}. Data recieved: {description}')
        return AppResponse.server_error('Unexpected error searching products').to_flask_tuple()
    
@routesProducts.route(ROUTE_GET_PRODUCT_SIBLINGS, methods=['GET'])
def get_siblings(code):
    try:
        return AppResponse.success(Products.get_siblings(code)).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_PRODUCT_SIBLINGS}. Error: {e}. Data recieved: {code}')
        return AppResponse.server_error('Unexpected error retrieving siblings').to_flask_tuple()
    
@routesProducts.route(ROUTE_CREATE_PRODUCT, methods=['POST'])
@jwt_protected()
def create_product():
    try:
        current_user = get_current_user()
        data = dict(request.get_json())
        Products.create(data)
        log_request_safely(ROUTE_CREATE_PRODUCT, {'user': current_user, 'code': data.get('code')})
        return AppResponse.created({'message': 'product created'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A product with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_CREATE_PRODUCT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error creating product').to_flask_tuple()
    
@routesProducts.route(ROUTE_UPDATE_PRODUCT, methods=['PUT'])
@jwt_protected()
def update_product():
    try:
        current_user = get_current_user()
        data = dict(request.get_json())
        Products.update(data)
        log_request_safely(ROUTE_UPDATE_PRODUCT, {'user': current_user, 'code': data.get('code')})
        return AppResponse.success({'message': 'product updated'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A product with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_PRODUCT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error updating product').to_flask_tuple()
    
@routesProducts.route(ROUTE_UPDATE_INVENTORY, methods=['PUT'])
@jwt_protected()
def update_inventory(code: str, cantity: str):
    try:
        current_user = get_current_user()
        try:
            cantity_float = float(cantity)
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'cantity': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        result = Products.update_inventory(code, cantity_float)
        log_request_safely(ROUTE_UPDATE_INVENTORY, {'user': current_user, 'code': code, 'cantity': cantity})
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_INVENTORY}. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return AppResponse.server_error('Unexpected error updating inventory').to_flask_tuple()
    
@routesProducts.route(ROUTE_ADD_INVENTORY, methods=['PUT'])
@jwt_protected()
def add_inventory(code: str, cantity: str):
    try:
        current_user = get_current_user()
        try:
            cantity_float = float(cantity)
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'cantity': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        result = Products.add_inventory(code, cantity_float)
        log_request_safely(ROUTE_ADD_INVENTORY, {'user': current_user, 'code': code, 'cantity': cantity})
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_ADD_INVENTORY}. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return AppResponse.server_error('Unexpected error adding inventory').to_flask_tuple()
    
@routesProducts.route(ROUTE_REMOVE_INVENTORY, methods=['PUT'])
@jwt_protected()
def remove_inventory(code: str, cantity: str):
    try:
        current_user = get_current_user()
        try:
            cantity_float = float(cantity)
        except (TypeError, ValueError) as e:
            return AppResponse.validation_error([{'cantity': f'Must be a valid number: {str(e)}'}]).to_flask_tuple()
        
        result = Products.remove_inventory(code, cantity_float)
        log_request_safely(ROUTE_REMOVE_INVENTORY, {'user': current_user, 'code': code, 'cantity': cantity})
        return AppResponse.success(result).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_REMOVE_INVENTORY}. Error: {e}. Product code: {code}. Cantity: {cantity}')
        return AppResponse.server_error('Unexpected error removing inventory').to_flask_tuple()
    
@routesProducts.route(ROUTE_DELETE_PRODUCT, methods=['DELETE'])
@jwt_protected()
def delete_product(code):
    try:
        current_user = get_current_user()
        Products.delete(code)
        log_request_safely(ROUTE_DELETE_PRODUCT, {'user': current_user, 'code': code})
        return AppResponse.success({'message': 'product deleted'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_DELETE_PRODUCT}. Error: {e}. Data recieved: {code}')
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
        logging.exception(f'{ROUTE_GET_ALL_DEPARTMENTS}: {e}.')
        return AppResponse.server_error('Unexpected error retrieving departments').to_flask_tuple()
    
@routesProducts.route(ROUTE_GET_DEPARTMENT, methods=['GET'])
def get_department(code):
    try:
        return AppResponse.success(Products.Departments.get(code).to_dict()).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_GET_DEPARTMENT}: {e}. Code: {code}')
        return AppResponse.server_error('Unexpected error retrieving department').to_flask_tuple()


@routesProducts.route(ROUTE_CREATE_DEPARTMENT, methods=['POST'])
@jwt_protected()
def create_department(description):
    try:
        current_user = get_current_user()
        Products.Departments.create(description)
        log_request_safely(ROUTE_CREATE_DEPARTMENT, {'user': current_user, 'description': description})
        return AppResponse.created({'message': 'department created'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('A department with that description already exists').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_CREATE_DEPARTMENT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error creating department').to_flask_tuple()

@routesProducts.route(ROUTE_UPDATE_DEPARTMENT, methods=['PUT'])
@jwt_protected()
def update_department(code: int, description: str):
    try:
        current_user = get_current_user()
        Products.Departments.update(code, description)
        log_request_safely(ROUTE_UPDATE_DEPARTMENT, {'user': current_user, 'code': code})
        return AppResponse.success({'message': 'department updated'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_DEPARTMENT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error updating department').to_flask_tuple()
    
@routesProducts.route(ROUTE_DELETE_DEPARTMENT, methods=['DELETE'])
@jwt_protected()
def delete_department(code: int):
    try:
        current_user = get_current_user()
        Products.Departments.delete(code)
        log_request_safely(ROUTE_DELETE_DEPARTMENT, {'user': current_user, 'code': code})
        return AppResponse.success({'message': 'department deleted'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_DELETE_DEPARTMENT}. Error: {e}.')
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
        logging.exception(f'{ROUTE_GET_ASSOCIATES_RAW_DATA}. Error: {e}.')
        return AppResponse.server_error('Unexpected error retrieving associate codes').to_flask_tuple()    
    
@routesProducts.route(ROUTE_CREATE_ASSOCIATE, methods=['POST'])
@jwt_protected()
def create_associate():
    try:
        current_user = get_current_user()
        data = {
            'code': request.args.get('code'),
            'parent_code': request.args.get('parent'),
            'tag': request.args.get('tag')
        }

        Products.Associates_codes.create(data)
        log_request_safely(ROUTE_CREATE_ASSOCIATE, {'user': current_user, 'code': data.get('code')})
        return AppResponse.created({'message': 'associate product created'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('An associate with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_CREATE_ASSOCIATE}. Error: {e}.')
        return AppResponse.server_error('Unexpected error creating associate code').to_flask_tuple()    
    
@routesProducts.route(ROUTE_UPDATE_ASSOCIATE, methods=['PUT'])
@jwt_protected()
def update_associate():
    try:
        current_user = get_current_user()
        data = {
            'code': request.args.get('code'),
            'parent_code': request.args.get('parent'),
            'tag': request.args.get('tag'),
            'original_code': request.args.get('originalCode')
        }
        Products.Associates_codes.update(data)
        log_request_safely(ROUTE_UPDATE_ASSOCIATE, {'user': current_user, 'code': data.get('code')})
        return AppResponse.success({'message': 'associate product updated'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except IntegrityError:
        return AppResponse.conflict('An associate with that code already exists').to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_UPDATE_ASSOCIATE}. Error: {e}.')
        return AppResponse.server_error('Unexpected error updating associate code').to_flask_tuple() 
    
@routesProducts.route(ROUTE_DELETE_ASSOCIATE, methods=['DELETE'])
@jwt_protected()
def delete_associate(code: str):
    try:
        current_user = get_current_user()
        Products.Associates_codes.delete(code)
        log_request_safely(ROUTE_DELETE_ASSOCIATE, {'user': current_user, 'code': code})
        return AppResponse.success({'message': 'associate product deleted'}).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.exception(f'{ROUTE_DELETE_ASSOCIATE}. Error: {e}.')
        return AppResponse.server_error('Unexpected error deleting associate code').to_flask_tuple() 