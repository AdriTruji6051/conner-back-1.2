from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.controlers.printers import Printers
from app.helpers.helpers import AppResponse
from app.routes_constants import (
    ROUTE_LIST_PRINTERS, ROUTE_DICT_PRINTERS, ROUTE_UPDATE_PRINTER
)

PRINTERS_MANAGER = Printers()

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
        return AppResponse.server_error("an error has ocurred").to_flask_tuple()
    
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
        return AppResponse.server_error("an error has ocurred").to_flask_tuple()
    
@routesPrinters.route(ROUTE_UPDATE_PRINTER, methods=['PUT'])
def update_printer(printer):
    try:
        ipv4 = request.remote_addr
        return AppResponse.success(PRINTERS_MANAGER.update_printer(printer, ipv4)).to_flask_tuple()
    except Exception as e:
        logging.info(f'/api/print/update/<string:printer>. Catch: {e}.')
        return AppResponse.server_error("an error has ocurred").to_flask_tuple()