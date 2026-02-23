from datetime import datetime

from sqlalchemy import event

from app.extensions import db
from app.models.analytics import Analytics, create_products_changes_keys
from app.helpers.helpers import profit_percentage, raise_exception_if_missing_keys
from app.models.core_classes import Product, AssociateCode, Department

QUICKSALE_CODE = 'QUICKSALE'
COMMONSALE_CODE = 'COMMONSALE'
DEFAULT_DEPARTMENT_DESCRIPTION = '___'
PROTECTED_CODE_ERROR = 'Protected placeholder products cannot be used as associate.'

_DEFAULT_DEPARTMENT_CODE: int | None = None


def _is_quicksale_code(code: str | None) -> bool:
    return bool(code) and code == QUICKSALE_CODE


def _is_protected_placeholder_code(code: str | None) -> bool:
    """Check if code is a protected placeholder (QUICKSALE or COMMONSALE)."""
    return bool(code) and code in (QUICKSALE_CODE, COMMONSALE_CODE)


def ensure_default_department() -> Department:
    """Ensure the placeholder department exists and cache its code."""
    global _DEFAULT_DEPARTMENT_CODE

    dept = Department.query.filter_by(description=DEFAULT_DEPARTMENT_DESCRIPTION).first()
    if not dept:
        dept = Department(description=DEFAULT_DEPARTMENT_DESCRIPTION)
        db.session.add(dept)
        db.session.commit()

    _DEFAULT_DEPARTMENT_CODE = dept.code
    return dept


def is_protected_department(candidate: Department | int | None) -> bool:
    if candidate is None:
        return False

    default_code = _DEFAULT_DEPARTMENT_CODE
    candidate_code = candidate.code if isinstance(candidate, Department) else candidate

    if default_code is not None and candidate_code == default_code:
        return True

    if isinstance(candidate, Department):
        return candidate.description == DEFAULT_DEPARTMENT_DESCRIPTION

    dept = Department.query.get(candidate_code)
    return bool(dept and dept.description == DEFAULT_DEPARTMENT_DESCRIPTION)


def ensure_quicksale_product() -> Product:
    """Ensure the placeholder product used for quick sales exists."""
    placeholder = Product.query.get(QUICKSALE_CODE)
    if placeholder:
        if placeholder.inventory is not None:
            placeholder.inventory = None
            db.session.commit()
        return placeholder

    placeholder = Product(
        code=QUICKSALE_CODE,
        description='QUICKSALE',
        sale_type='U',
        cost=0,
        sale_price=0,
        department=None,
        wholesale_price=0,
        priority=0,
        inventory=None,
        parent_code=None,
        profit_margin=0,
        modified_at=datetime.now().strftime('%Y-%m-%d'),
    )
    db.session.add(placeholder)
    db.session.commit()
    return placeholder

def ensure_common_product() -> Product:
    """Ensure the placeholder product used for common sales exists."""
    placeholder = Product.query.get(COMMONSALE_CODE)
    if placeholder:
        if placeholder.inventory is not None:
            placeholder.inventory = None
            db.session.commit()
        return placeholder

    placeholder = Product(
        code=COMMONSALE_CODE,
        description='COMMONSALE',
        sale_type='U',
        cost=0,
        sale_price=0,
        department=None,
        wholesale_price=0,
        priority=0,
        inventory=None,
        parent_code=None,
        profit_margin=0,
        modified_at=datetime.now().strftime('%Y-%m-%d'),
    )
    db.session.add(placeholder)
    db.session.commit()
    return placeholder

# Keys for validation
create_product_keys = ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "parent_code"]
update_product_keys = ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "parent_code", "original_code"]
update_department_keys = ["description", "code"]
create_associates_codes_keys = ["code", "parent_code", "tag"]
update_associates_codes_keys = ["code", "parent_code", "tag", "original_code"]
update_siblings_keys = ["sale_type", "cost", "sale_price", "department", "wholesale_price", "parent_code"]


def update_siblings_products(data: dict, siblings_codes: list[str]):
    if len(siblings_codes):
        for sibling_code in siblings_codes:
            try:
                product = Product.query.get(sibling_code)
                if product:
                    for key in update_siblings_keys:
                        setattr(product, key, data[key])
                    db.session.commit()
            except Exception:
                continue


def build_product_log_dict(data: dict, method: str, modified_date: str) -> dict:
    change_log = {}
    for key in create_products_changes_keys[:len(create_products_changes_keys) - 3]:
        change_log[key] = data[key]

    change_log['original_code'] = None
    change_log['modified_at'] = modified_date
    change_log['method'] = method
    if 'original_code' in data:
        change_log['original_code'] = data['original_code']

    return change_log


class Products:
    @staticmethod
    def product_data_is_valid(data: dict, check_update_product_keys: bool = False) -> None:
        raise_exception_if_missing_keys(data, create_product_keys, 'create product')

        if check_update_product_keys:
            raise_exception_if_missing_keys(data, update_product_keys, 'update product')

        if data['cost'] < 0:
            raise ValueError('Data sended is invalid -> Cost must be greater than zero')

        if type(data['inventory']) not in [float, int] and data['inventory'] is not None:
            raise ValueError('Data sended is invalid -> Inventory must be NULL, or NUMBER')

        if data['cost'] > data['sale_price']:
            raise ValueError('Data sended is invalid -> sale_price must be greater than cost')

        if data['wholesale_price'] > data['sale_price']:
            raise ValueError('Data sended is invalid -> sale_price must be greater than wholesale_price')

        if data['sale_type'] != 'U' and data['sale_type'] != 'D':
            raise ValueError('Data sended is invalid -> sale_type must have values of "U" or "D"')

    @staticmethod
    def get_update_inventory_params(data: list[dict]) -> list[tuple]:
        """Check if the data could be enough to validate the data -> Product {}"""
        update_inventory_params_array = []

        for product_data in data:
            product_inventory = None
            try:
                product_obj = Product.query.get(product_data['code'])
                if product_obj:
                    product_inventory = product_obj.inventory
            except Exception:
                product_inventory = None
            
            # Fixed logic: only check inventory for products that track it (not None)
            if product_inventory is not None:
                if product_inventory < product_data['cantity']:
                    raise ValueError(f'Inventory insuficient for product! {product_data["code"], product_data["description"]}')
                new_inventory = product_inventory - product_data['cantity']
                update_inventory_params_array.append((new_inventory, product_data['code']))

        return update_inventory_params_array

    @staticmethod
    def enough_inventory(code: str, cantity: float) -> bool:
        """Check if the product with the given code has at least the given cantity in stock."""
        if cantity < 0:
            raise ValueError('Cantity must be greater than zero.')

        try:
            product = Product.query.get(code)
            if not product:
                # Also check if it's an associate code
                assoc = AssociateCode.query.get(code)
                if assoc:
                    product = Product.query.get(assoc.parent_code)
            
            if not product:
                return True

            if product.inventory is None:
                return True

            return product.inventory >= cantity
        except Exception:
            return True

    @staticmethod
    def get(code: str) -> Product:
        """Get a product by code. If code is an associate, returns the parent product
        with modified description and associate metadata."""
        tag = ''
        id_associate = code
        is_associate = False

        assoc = AssociateCode.query.get(code)
        if assoc:
            tag = ' ' + (assoc.tag or '')
            code = assoc.parent_code
            is_associate = True

        product = Product.query.get(code)
        if not product:
            raise ValueError('Product not found')

        # Return a dict-like representation with the associate info merged
        result = product.to_dict(is_associate=is_associate)
        result['description'] += tag
        result['code'] = id_associate
        return result

    @staticmethod
    def get_by_description(description: str, called_before: bool = False, page: int | None = None, page_size: int | None = None):
        description_split = description.split()
        base_query = Product.query.filter(
            Product.code != QUICKSALE_CODE,
            Product.code != COMMONSALE_CODE
        )

        if len(description_split) < 2:
            query = base_query.filter(Product.description.ilike(f'%{description}%')).order_by(
                Product.priority.desc(),
                db.case(
                    (Product.description.ilike(f'{description}%'), 0),
                    else_=1
                ),
                Product.description
            )
        else:
            query = base_query
            for word in description_split:
                query = query.filter(Product.description.ilike(f'%{word}%'))

            query = query.order_by(
                Product.priority.desc(),
                db.case(
                    (Product.description.ilike(f'{description}%'), 0),
                    (Product.description.ilike(f'{description_split[0]}%'), 1),
                    else_=2
                ),
                Product.description
            )

        if page is not None and page_size is not None:
            pagination = query.paginate(page=page, per_page=page_size, error_out=False)
            return {
                'items': [p.to_dict() for p in pagination.items],
                'page': page,
                'page_size': page_size,
                'total': pagination.total,
                'pages': pagination.pages,
            }

        products = query.all()
        ans = [p.to_dict() for p in products]

        # Handle ñ/Ñ for better Spanish search results when not paginating
        if 'ñ' in description and not called_before:
            ans.extend(Products.get_by_description(description.replace('ñ', 'Ñ'), True))
        elif 'Ñ' in description and not called_before:
            ans.extend(Products.get_by_description(description.replace('Ñ', 'ñ'), True))

        return ans

    @staticmethod
    def get_siblings(code: str) -> dict:
        siblings_rows = Product.query.filter_by(parent_code=code).all()

        if not len(siblings_rows):
            child = Product.query.get(code)
            if not child:
                raise ValueError('Product not exist')

            code = child.parent_code
            if not code:
                raise ValueError('Product has not parent linked')

            siblings_rows = Product.query.filter_by(parent_code=code).all()
            if not len(siblings_rows):
                raise ValueError('Product has not parent linked')

        childs = [p.to_dict() for p in siblings_rows]
        parent = Products.get(code)

        return {
            'parent_product': parent,
            'child_products': childs
        }

    @staticmethod
    def create(data: dict):
        Products.product_data_is_valid(data)
        if _is_protected_placeholder_code(data['code']):
            raise ValueError('This code is reserved for system use.')
        if _is_protected_placeholder_code(data.get('parent_code')):
            raise ValueError('Protected placeholder products cannot be used as parent.')
        modified_date = datetime.now().strftime('%Y-%m-%d')

        product = Product(
            code=data['code'],
            description=data['description'],
            sale_type=data['sale_type'],
            cost=data['cost'],
            sale_price=data['sale_price'],
            department=data['department'],
            wholesale_price=data['wholesale_price'],
            priority=data['priority'],
            inventory=data['inventory'],
            parent_code=data['parent_code'],
            profit_margin=profit_percentage(data['cost'], data['sale_price']),
            modified_at=modified_date,
        )

        db.session.add(product)
        db.session.commit()

        Analytics.Products_changes.create(build_product_log_dict(data, 'POST', modified_date))

        if 'siblings_codes' in data:
            update_siblings_products(data, data['siblings_codes'])

    @staticmethod
    def update(data: dict):
        Products.product_data_is_valid(data=data, check_update_product_keys=True)
        modified_date = datetime.now().strftime('%Y-%m-%d')

        original_code = data['original_code']
        if _is_protected_placeholder_code(original_code) or _is_protected_placeholder_code(data['code']):
            raise ValueError('Protected placeholder products cannot be modified.')
        if _is_protected_placeholder_code(data.get('parent_code')):
            raise ValueError('Protected placeholder products cannot be used as parent.')
        product = Product.query.get(original_code)
        if not product:
            raise ValueError(f'Product with code {original_code} not found')

        # If code is being changed, handle it
        if original_code != data['code']:
            # Create new product with new code, copy all data
            new_product = Product(
                code=data['code'],
                description=data['description'],
                sale_type=data['sale_type'],
                cost=data['cost'],
                sale_price=data['sale_price'],
                department=data['department'],
                wholesale_price=data['wholesale_price'],
                priority=data['priority'],
                inventory=data['inventory'],
                parent_code=data['parent_code'],
                profit_margin=profit_percentage(data['cost'], data['sale_price']),
                modified_at=modified_date,
            )
            db.session.delete(product)
            db.session.flush()
            db.session.add(new_product)
        else:
            product.description = data['description']
            product.sale_type = data['sale_type']
            product.cost = data['cost']
            product.sale_price = data['sale_price']
            product.department = data['department']
            product.wholesale_price = data['wholesale_price']
            product.priority = data['priority']
            product.inventory = data['inventory']
            product.parent_code = data['parent_code']
            product.profit_margin = profit_percentage(data['cost'], data['sale_price'])
            product.modified_at = modified_date

        db.session.commit()

        Analytics.Products_changes.create(build_product_log_dict(data, 'PUT', modified_date))

        if 'siblings_codes' in data:
            update_siblings_products(data, data['siblings_codes'])

    @staticmethod
    def update_inventory(code: str, cantity: float):
        if cantity < 0:
            raise ValueError('Inventory cannot be zero or lower.')
        if _is_protected_placeholder_code(code):
            raise ValueError('Protected placeholder inventory cannot be modified manually.')
        product = Product.query.get(code)
        if not product:
            raise ValueError(f'Product with code {code} not found')
        product.inventory = cantity
        db.session.commit()

    @staticmethod
    def delete(code: str):
        if not code:
            raise ValueError('Not code sended.')
        if _is_protected_placeholder_code(code):
            raise ValueError('Protected placeholder products cannot be deleted.')
        product = Product.query.get(code)
        if not product:
            raise ValueError(f'Product with code {code} not found')
        db.session.delete(product)
        db.session.commit()

    @staticmethod
    def add_inventory(code: str, cantity: float):
        """Product code and cantity to add."""
        try:
            product = Product.query.get(code)
            if not product:
                # Check if it's an associate
                assoc = AssociateCode.query.get(code)
                if assoc:
                    product = Product.query.get(assoc.parent_code)
            
            if not product or product.inventory is None:
                return

            product.inventory += cantity
            db.session.commit()
        except Exception:
            return

    @staticmethod
    def remove_inventory(code: str, cantity: float):
        """Product code and cantity to substract."""
        if not Products.enough_inventory(code, cantity):
            raise ValueError(f'Not enough inventory for product with code: {code}')

        try:
            product = Product.query.get(code)
            if not product:
                assoc = AssociateCode.query.get(code)
                if assoc:
                    product = Product.query.get(assoc.parent_code)

            if not product or product.inventory is None:
                return

            product.inventory -= cantity
            db.session.commit()
        except Exception:
            return

    class Departments:
        @staticmethod
        def get(code: int) -> Department:
            dept = Department.query.get(code)
            if not dept:
                raise ValueError('Not department finded')
            return dept

        @staticmethod
        def get_all(page: int | None = None, page_size: int | None = None):
            query = Department.query
            if page is not None and page_size is not None:
                pagination = query.paginate(page=page, per_page=page_size, error_out=False)
                return {
                    'items': [d.to_dict() for d in pagination.items],
                    'page': page,
                    'page_size': page_size,
                    'total': pagination.total,
                    'pages': pagination.pages,
                }

            return query.all()

        @staticmethod
        def create(description: str):
            if description == DEFAULT_DEPARTMENT_DESCRIPTION:
                raise ValueError('Default no-department already exists.')
            dept = Department(description=description)
            db.session.add(dept)
            db.session.commit()

        @staticmethod
        def update(code: int, description: str):
            if description == DEFAULT_DEPARTMENT_DESCRIPTION:
                raise ValueError('Description reserved for default department.')
            dept = Department.query.get(code)
            if not dept:
                raise ValueError(f'Department with code {code} not found')
            if is_protected_department(dept):
                raise ValueError('Default department cannot be updated')
            dept.description = description
            db.session.commit()

        @staticmethod
        def delete(code: int):
            if is_protected_department(code):
                raise ValueError('Default department cannot be deleted')
            dept = Department.query.get(code)
            if not dept:
                raise ValueError(f'Department with code {code} not found')
            db.session.delete(dept)
            db.session.commit()


@event.listens_for(Department, 'before_update')
def _prevent_default_department_update(mapper, connection, target):
    if is_protected_department(target):
        raise ValueError('Default department cannot be updated.')


@event.listens_for(Department, 'before_delete')
def _prevent_default_department_delete(mapper, connection, target):
    if is_protected_department(target):
        raise ValueError('Default department cannot be deleted.')

    class Associates_codes: # NOSONAR TODO: Check implementation
        @staticmethod
        def get(code: str) -> dict:
            assoc = AssociateCode.query.get(code)
            if not assoc:
                raise ValueError('Not associate_code finded')

            parent = Product.query.get(assoc.parent_code)
            if not parent:
                raise ValueError('Parent product not found')

            result = parent.to_dict(is_associate=True)
            result['code'] = assoc.code
            result['tag'] = assoc.tag
            return result

        @staticmethod
        def get_raw_data(parent_code: str, page: int | None = None, page_size: int | None = None):
            """Return associate products with optional pagination."""
            query = AssociateCode.query.filter_by(parent_code=parent_code)
            if page is not None and page_size is not None:
                pagination = query.paginate(page=page, per_page=page_size, error_out=False)
                return {
                    'items': [a.to_dict() for a in pagination.items],
                    'page': page,
                    'page_size': page_size,
                    'total': pagination.total,
                    'pages': pagination.pages,
                }

            associates = query.all()
            return [a.to_dict() for a in associates]

        @staticmethod
        def create(data: dict):
            raise_exception_if_missing_keys(data, create_associates_codes_keys, 'create associate_codes')
            if _is_protected_placeholder_code(data['code']) or _is_protected_placeholder_code(data['parent_code']):
                raise ValueError(PROTECTED_CODE_ERROR)
            assoc = AssociateCode(
                code=data['code'],
                parent_code=data['parent_code'],
                tag=data['tag'],
            )
            db.session.add(assoc)
            db.session.commit()

        @staticmethod
        def update(data: dict):
            raise_exception_if_missing_keys(data, update_associates_codes_keys, 'update associate_codes')
            if _is_protected_placeholder_code(data['code']) or _is_protected_placeholder_code(data['parent_code']) or _is_protected_placeholder_code(data['original_code']):
                raise ValueError(PROTECTED_CODE_ERROR)
            original_code = data['original_code']
            assoc = AssociateCode.query.get(original_code)
            if not assoc:
                raise ValueError(f'Associate code {original_code} not found')

            if original_code != data['code']:
                db.session.delete(assoc)
                db.session.flush()
                new_assoc = AssociateCode(
                    code=data['code'],
                    parent_code=data['parent_code'],
                    tag=data['tag'],
                )
                db.session.add(new_assoc)
            else:
                assoc.parent_code = data['parent_code']
                assoc.tag = data['tag']

            db.session.commit()

        @staticmethod
        def delete(code: str):
            if not code:
                raise ValueError('Not code sended')
            if _is_protected_placeholder_code(code):
                raise ValueError(PROTECTED_CODE_ERROR)
            assoc = AssociateCode.query.get(code)
            if not assoc:
                raise ValueError(f'Associate code {code} not found')
            db.session.delete(assoc)
            db.session.commit()