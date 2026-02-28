from datetime import datetime

from app.extensions import db
from app.models.core_classes import DrawerLog, ProductChange, CashFlow
from app.helpers.helpers import raise_exception_if_missing_keys, ValidationError, collect_missing_keys

allowed_methods = ['POST', 'PUT', 'DELETE']
create_drawer_logs_keys = ['open_at', 'user_id', 'method', 'transaction_type', 'transaction_id']
create_products_changes_keys = ['code', 'cost', 'sale_price', 'wholesale_price', 'original_code', 'modified_at', 'method']
create_cash_flow_keys = ['description', 'amount', 'date', 'in_or_out', 'is_payment']


def raise_exception_if_invalid_drawer_log(data: dict):
    v = ValidationError()
    v.errors.extend(collect_missing_keys(data, create_drawer_logs_keys, 'create drawer_logs'))

    if v.has_errors:
        raise v

    if data['method'] not in allowed_methods:
        v.add('method', f'Must be one of {allowed_methods}')

    v.raise_if_errors()


class Analytics:
    class Drawer_logs:
        @staticmethod
        def get(id: int) -> DrawerLog:
            log = DrawerLog.query.get(id)
            if not log:
                raise ValueError(f'Drawer log with the id {id} not exist')
            return log

        @staticmethod
        def get_all(date: str = '') -> list[DrawerLog]:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')

            logs = DrawerLog.query.filter(DrawerLog.open_at.like(f'{date}%')).all()
            return logs

        @staticmethod
        def create(data: dict):
            raise_exception_if_invalid_drawer_log(data)

            log = DrawerLog(
                open_at=data['open_at'],
                user_id=data['user_id'],
                method=data['method'],
                transaction_type=data['transaction_type'],
                transaction_id=data.get('transaction_id'),
            )
            db.session.add(log)
            db.session.commit()

    class Products_changes:
        @staticmethod
        def get(code: str) -> list[ProductChange]:
            changes = ProductChange.query.filter_by(code=code).all()
            if not changes:
                raise ValueError(f'Products changes with code {code} not exist')
            return changes

        @staticmethod
        def get_all(date: str = '', exclude_delete: bool = True) -> list[ProductChange]:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')

            query = ProductChange.query.filter(ProductChange.modified_at.like(f'{date}%'))

            if exclude_delete:
                query = query.filter(ProductChange.method != 'DELETE')

            return query.all()

        @staticmethod
        def create(data: dict):
            raise_exception_if_missing_keys(data, create_products_changes_keys, 'Create products_changes keys')

            change = ProductChange(
                code=data['code'],
                cost=data.get('cost'),
                sale_price=data['sale_price'],
                wholesale_price=data.get('wholesale_price'),
                original_code=data.get('original_code'),
                modified_at=data['modified_at'],
                method=data.get('method'),
            )
            db.session.add(change)
            db.session.commit()

    class Cash_flow:
        @staticmethod
        def get(id: int) -> CashFlow:
            flow = CashFlow.query.get(id)
            if not flow:
                raise ValueError(f'Cash_flow with the id {id} not exist')
            return flow

        @staticmethod
        def get_date(date: str) -> list[CashFlow]:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')

            return CashFlow.query.filter(CashFlow.date.like(f'{date}%')).all()

        @staticmethod
        def insert(amount: float, in_or_out: int, is_payment: int = 0, description: str = 'None'):
            """Amount of money. 1 if inflow, 0 if outflow. 1 if is payment 0 if not."""
            v = ValidationError()

            if amount is None or amount < 0:
                v.add('amount', 'Must be greater than or equal to zero')
            if in_or_out not in [0, 1]:
                v.add('in_or_out', 'Must have a value of 1 or 0')
            if is_payment not in [0, 1]:
                v.add('is_payment', 'Must have a value of 1 or 0')

            v.raise_if_errors()

            flow = CashFlow(
                description=description,
                amount=amount,
                date=datetime.now().strftime('%Y-%m-%d'),
                in_or_out=in_or_out,
                is_payment=is_payment,
            )
            db.session.add(flow)
            db.session.commit()
        