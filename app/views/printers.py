from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.controlers.printers import Printers

PRINTERS_MANAGER = Printers()

routesPrinters = Blueprint('routes-printers', __name__)

@routesPrinters.route('/api/print/list', methods=['GET'])
def list_printers():
    try:
        ipv4 = request.remote_addr

        return jsonify({
            'host': ipv4,
            'printers': PRINTERS_MANAGER.list(ipv4)
        })
    
    except ConnectionRefusedError:
        return jsonify({
            'host': ipv4,
            'printers': []
        })
    except Exception as e:
        logging.info(f'/api/print/list. Catch: {e}.')
        return jsonify({"error": "an error has ocurred"}), 500
    
@routesPrinters.route('/api/print/dict', methods=['GET'])
def dict_printers():
    try:
        ipv4 = request.remote_addr

        return jsonify({
            'host': ipv4,
            'printers': PRINTERS_MANAGER.dict(ipv4)
        })
    
    except ConnectionRefusedError:
        return jsonify({
            'host': ipv4,
            'printers': {}
        })
    except Exception as e:
        logging.info(f'/api/print/dict. Catch: {e}.')
        return jsonify({"error": "an error has ocurred"}), 500
    
@routesPrinters.route('/api/print/update/<string:printer>', methods=['PUT'])
def update_printer(printer):
    try:
        ipv4 = request.remote_addr

        return jsonify(PRINTERS_MANAGER.update_printer(printer, ipv4))
    
    except Exception as e:
        logging.info(f'/api/print/update/<string:printer>. Catch: {e}.')
        return jsonify({"error": "an error has ocurred"}), 500