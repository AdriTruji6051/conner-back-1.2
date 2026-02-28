from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.controlers.printers import Printers
from app.helpers.helpers import AppResponse, ValidationError
from app.routes_constants import (
    ROUTE_LIST_PRINTERS, ROUTE_DICT_PRINTERS, ROUTE_UPDATE_PRINTER
)

PRINTERS_MANAGER = Printers()
ERROR_MESSAGE = "A printer error has ocurred"

routesPrinters = Blueprint('routes-printers', __name__)

@routesPrinters.route(ROUTE_LIST_PRINTERS, methods=['GET'])
def list_printers():
    try:
        ipv4 = request.remote_addr
        return AppResponse.success({
            'host': ipv4,
            'printers': PRINTERS_MANAGER.list(ipv4)
        }).to_flask_tuple()
    except ConnectionRefusedError:
        ipv4 = request.remote_addr
        return AppResponse.success({
            'host': ipv4,
            'printers': []
        }).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/print/list. Catch: {e}.')
        return AppResponse.server_error(ERROR_MESSAGE).to_flask_tuple()
    
@routesPrinters.route(ROUTE_DICT_PRINTERS, methods=['GET'])
def dict_printers():
    try:
        ipv4 = request.remote_addr
        return AppResponse.success({
            'host': ipv4,
            'printers': PRINTERS_MANAGER.dict(ipv4)
        }).to_flask_tuple()
    except ConnectionRefusedError:
        ipv4 = request.remote_addr
        return AppResponse.success({
            'host': ipv4,
            'printers': {}
        }).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/print/dict. Catch: {e}.')
        return AppResponse.server_error(ERROR_MESSAGE).to_flask_tuple()
    
@routesPrinters.route(ROUTE_UPDATE_PRINTER, methods=['PUT'])
def update_printer(printer):
    try:
        ipv4 = request.remote_addr
        return AppResponse.success(PRINTERS_MANAGER.update_printer(printer, ipv4)).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except ConnectionRefusedError:
        return AppResponse.server_error('Printer service is not reachable').to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_UPDATE_PRINTER}. Catch: {e}.')
        return AppResponse.server_error(ERROR_MESSAGE).to_flask_tuple()