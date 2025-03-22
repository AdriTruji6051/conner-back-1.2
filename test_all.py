import unittest

from run import create_app
from app.models.utyls import build_create_sql_sequence, build_update_sql_sequence
from app.models.products import raise_exception_if_missing_keys, Products
from app.connections.connections import DB_manager

keys_good= ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "parent_code"]
product_good = {
    'code': 'TESTCODE123',
    'description': 'TESTDESCRIPTION123',
    'sale_type': 'D',
    'cost': 23,
    'sale_price': 30,
    'department' : None,
    'wholesale_price': 25,
    'priority': 1,
    'inventory': 1,
    'parent_code': None
}

product_good_update = {
    'code': 'TESTUPDATE123',
    'description': 'TESTUPDATE123',
    'sale_type': 'U',
    'cost': 40,
    'sale_price': 100,
    'department' : None,
    'wholesale_price': 85,
    'priority': 1,
    'inventory': 16,
    'parent_code': None,
    'original_code': 'TESTCODE123'
}

# cost is invalid, sale_type is invalid. department, wholesale_price and inventory are missing
product_bad_keys = {
    'code': 'BADTESTCODE123',
    'description': 'BADTESTDESCRIPTION123',
    'sale_type': 'I',
    'cost': 230,
    'sale_price': 30,
    'priority': 1,
    'parent_code': None
}

product_bad = {
    'code': 'TESTUPDATE123',
    'description': 'TESTUPDATE123',
    'sale_type': 'I',
    'cost': 40000,
    'sale_price': 100,
    'department' : None,
    'wholesale_price': 85,
    'priority': 1,
    'inventory': 16,
    'parent_code': None,
    'original_code': 'TESTCODE123'
}


def test_db_builder():
    app = create_app()
    with app.app_context():
        if(not DB_manager.all_db_exist()):
            DB_manager.create_missing_db()

class TestProducts(unittest.TestCase):
    app = create_app()
    def test_db_builder(self):
        with self.app.app_context():
            if(not DB_manager.all_db_exist()):
                DB_manager.create_missing_db()

    # App context is used to manage the same db connections with flask, but used before of the app running 
    def test_not_in_class_func(self):
        Products.product_data_is_valid(product_good)
        with self.assertRaises(ValueError):
            Products.product_data_is_valid(product_bad)

        raise_exception_if_missing_keys(product_good, keys_good, 'test keys tag')
        with self.assertRaises(KeyError):
            raise_exception_if_missing_keys(product_bad_keys, keys_good, 'test keys tag')

    def test_products_crud_and_access(self):
        with self.app.app_context():
            Products.delete(product_good['code'])
            Products.delete(product_good_update['code'])
            Products.create(product_good)
            Products.update(product_good_update)

            # If you want to check that the changes has been applied, omit these functions
            Products.delete(product_good['code'])
            Products.delete(product_good_update['code'])

            # it´s possible to these could fail it theres not registers with the same id's in the database
            # Products.get(2)
            # Products.get(3)
            # Products.get_by_description('test')
            # Products.get_by_description('2 test')

            # TEST PRODUCTS SIBLINGS -> TO DO

    def test_departments_crud_and_access(self):
        with self.app.app_context():
            Products.Departments.create('testing department')
            ans = Products.Departments.get_all()
            ans = Products.Departments.get(ans[0]['code'])
            Products.Departments.update({'description':'testing update', 'code' : ans['code']})
            Products.Departments.delete(ans['code'])

    def test_associates_codes_crud_and_access(self):
        with self.app.app_context():
            Products.delete('1')
            new_good = dict(product_good)
            new_good['code'] = '1'
            Products.create(new_good)
            Products.Associates_codes.create({'code' : 'test_code', 'parent_code' : '1', 'tag' : 'test tag'})
            Products.Associates_codes.update({'code' : 'test_code_update', 'parent_code' : '1', 'tag' : 'test tag update', 'original_code' : 'test_code'})
            Products.Associates_codes.get('test_code_update')
            Products.Associates_codes.delete('test_code_update')
            Products.delete('1')

    def test_utyls(self):
        keys = ['code', 'original_code', 'cost', 'sale_price', 'wholesale_price', 'modified_at', 'method']
        build_create_sql_sequence('product_changes', keys)

        keys = ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "parent_code", "original_code"]
        build_update_sql_sequence('products', keys[:len(keys) - 1], 'code')

if __name__ == "__main__":
    # db builder is not inside test because data bases must 
    # be initialized before test execution
    test_db_builder()
    unittest.main()