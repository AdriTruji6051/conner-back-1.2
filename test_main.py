import unittest

from test_data import *

from run import create_app
from app.models.products import Products
from app.connections.connections import DB_manager

def db_builder():
    app = create_app()
    with app.app_context():
        if(not DB_manager.all_db_exist()):
            DB_manager.create_missing_db()

class Main_test(unittest.TestCase):
    app = create_app()
    
    def test_Products_obj(self):
        with self.app.app_context():
            #Delete test codes if data base already were running
            for obj in products_create_good_array:
                Products.delete(obj['code'])
            
            for obj in products_update_good_array:
                Products.delete(obj['code'])

            for obj in products_create_good_array:
                Products.create(obj)
                Products.get(obj['code'])
                Products.get_by_description(obj['description'])

            for obj in associates_codes_create_before_update:
                Products.Associates_codes.create(obj)
                Products.Associates_codes.get(obj['code'])

            for obj in associates_codes_update_before_update:
                Products.Associates_codes.update(obj)
                Products.Associates_codes.get(obj['code'])
            
            for obj in products_update_good_array:
                Products.update(obj)
                Products.get(obj['code'])
                Products.get_by_description(obj['description'])
            
            for obj in associates_codes_create_after_update:
                Products.Associates_codes.create(obj)
                Products.Associates_codes.get(obj['code'])

            for obj in associates_codes_update_after_update:
                Products.Associates_codes.update(obj)
                Products.Associates_codes.get(obj['code'])

            for obj in products_create_bad_array:
                with self.assertRaises(Exception):
                    Products.create(obj)
                    Products.update(obj)

            with self.assertRaises(Exception):
                Products.create()
                Products.update()
                Products.delete()
            
    
if __name__ == "__main__":
    # db builder is not inside test because data bases must 
    # be initialized before tests execution
    db_builder()
    unittest.main()