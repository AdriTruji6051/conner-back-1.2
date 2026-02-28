from flask import jsonify, Blueprint, request
from flask_jwt_extended import jwt_required
import logging

from app.models.analytics import Analytics
from app.controlers.printers import Printers
from app.helpers.helpers import AppResponse, ValidationError
from app.routes_constants import (
    ROUTE_INSERT_CASH_INFLOW, ROUTE_INSERT_CASH_OUTFLOW, ROUTE_INSERT_CASH_PAYMENT,
    ROUTE_GET_DRAWER_LOG, ROUTE_GET_DRAWER_LOG_BY_DATE,
    ROUTE_GET_PRODUCT_CHANGES, ROUTE_GET_PRODUCT_CHANGES_BY_DATE
)

PRINTERS_MANAGER = Printers()

routesAnalitycs = Blueprint('routes-analitycs', __name__)

@routesAnalitycs.route(ROUTE_INSERT_CASH_INFLOW, methods=['POST'])
def insert_inflow():
    try:
        amount = request.args.get('amount', type=float)
        drawer = request.args.get('drawer')
        description = request.args.get('description')

        Analytics.Cash_flow.insert(amount=amount, in_or_out=1, is_payment=0, description=description)
        return AppResponse.success(PRINTERS_MANAGER.open_drawer()).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_INSERT_CASH_INFLOW} Error: {e}.')
        return AppResponse.server_error('Unexpected error registering inflow').to_flask_tuple()
    
@routesAnalitycs.route(ROUTE_INSERT_CASH_OUTFLOW, methods=['POST'])
def insert_ouflow():
    try:
        amount = request.args.get('amount', type=float)
        drawer = request.args.get('drawer')
        description = request.args.get('description')
        Analytics.Cash_flow.insert(amount=amount, in_or_out=0, is_payment=0, description=description)
        return AppResponse.success(PRINTERS_MANAGER.open_drawer()).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_INSERT_CASH_OUTFLOW}. Error: {e}.')
        return AppResponse.server_error('Unexpected error registering cash outflow').to_flask_tuple()
    
@routesAnalitycs.route(ROUTE_INSERT_CASH_PAYMENT, methods=['POST'])
def insert_payment():
    try:
        amount = request.args.get('amount', type=float)
        drawer = request.args.get('drawer')
        description = request.args.get('description')
        Analytics.Cash_flow.insert(amount=amount, in_or_out=0, is_payment=1, description=description)
        return AppResponse.success(PRINTERS_MANAGER.open_drawer()).to_flask_tuple()
    except ValidationError as e:
        return AppResponse.validation_error(e.errors).to_flask_tuple()
    except ValueError as e:
        return AppResponse.unprocessable(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_INSERT_CASH_PAYMENT}. Error: {e}.')
        return AppResponse.server_error('Unexpected error registering cash payment').to_flask_tuple()


@routesAnalitycs.route(ROUTE_GET_DRAWER_LOG, methods=['GET'])
def get_drawer_log(id):
    try:
        return AppResponse.success(Analytics.Drawer_logs.get(id).to_dict()).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_DRAWER_LOG}. Error: {e}. Id: {id}')
        return AppResponse.server_error('Unexpected error retrieving drawer log').to_flask_tuple()
    
@routesAnalitycs.route(ROUTE_GET_DRAWER_LOG_BY_DATE, methods=['GET'])
def get_drawer_log_date_date(date):
    try:
        return AppResponse.success({'logs': [l.to_dict() for l in Analytics.Drawer_logs.get_all(date)]}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_DRAWER_LOG_BY_DATE}. Error: {e}. Date: {date}')
        return AppResponse.server_error('Unexpected error retrieving drawer logs by date').to_flask_tuple()
    
@routesAnalitycs.route(ROUTE_GET_PRODUCT_CHANGES, methods=['GET'])
def get_changes_log(id: int):
    try:
        return AppResponse.success([c.to_dict() for c in Analytics.Products_changes.get(id)]).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_PRODUCT_CHANGES}. Error: {e}. Id: {id}')
        return AppResponse.server_error('Unexpected error retrieving product changes').to_flask_tuple()
    
@routesAnalitycs.route(ROUTE_GET_PRODUCT_CHANGES_BY_DATE, methods=['GET'])
def get_changes_log_date(date: str):
    try:
        return AppResponse.success({'logs': [c.to_dict() for c in Analytics.Products_changes.get_all(date)]}).to_flask_tuple()
    except ValueError as e:
        return AppResponse.not_found(str(e)).to_flask_tuple()
    except Exception as e:
        logging.error(f'{ROUTE_GET_PRODUCT_CHANGES_BY_DATE}. Error: {e}. Date: {date}')
        return AppResponse.server_error('Unexpected error retrieving product changes by date').to_flask_tuple()