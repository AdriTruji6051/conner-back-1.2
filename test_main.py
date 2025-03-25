import unittest

from test_data import *

from run import create_app
from app.models.products import Products
from app.models.config import Config
from app.connections.connections import DB_manager

SHOW_GET_LOGS = False
LOGS_CHAR_LEN = 40

def db_builder():
    app = create_app()
    with app.app_context():
        if(not DB_manager.all_db_exist()):
            DB_manager.create_missing_db()

class Main_test(unittest.TestCase):
    app = create_app()

    def get_users_id(self):
        users_id = list()

        with self.app.app_context():
            # get the users if exist to delete to avoid problems at testing
            try:
                users = Config.Users.get_all()
                users_id = [user['id'] for user in users]
            except:
                users_id = []
        
        return users_id
    
    def test_Products_obj(self):
        with self.app.app_context():
            #Delete test codes if data base already were running
            logs = list()
            for obj in products_create_good_array:
                Products.delete(obj['code'])
            
            for obj in products_update_good_array:
                Products.delete(obj['code'])

            for obj in products_create_good_array:
                Products.create(obj)
                ans1 = Products.get(obj['code'])
                ans2 = Products.get_by_description(obj['description'])

                logs.append(ans1)
                logs.append(ans2)

            for obj in associates_codes_create_before_update:
                Products.Associates_codes.create(obj)
                ans = Products.Associates_codes.get(obj['code'])

                logs.append(ans)

            for obj in associates_codes_update_before_update:
                Products.Associates_codes.update(obj)
                ans = Products.Associates_codes.get(obj['code'])

                logs.append(ans)
            
            for obj in products_update_good_array:
                Products.update(obj)
                ans1 = Products.get(obj['code'])
                ans2 = Products.get_by_description(obj['description'])

                logs.append(ans1)
                logs.append(ans2)
            
            for obj in associates_codes_create_after_update:
                Products.Associates_codes.create(obj)
                ans = Products.Associates_codes.get(obj['code'])

                logs.append(ans)

            for obj in associates_codes_update_after_update:
                Products.Associates_codes.update(obj)
                ans = Products.Associates_codes.get(obj['code'])

                logs.append(ans)

            for obj in products_create_bad_array:
                with self.assertRaises(Exception):
                    Products.create(obj)
                    Products.update(obj)

            with self.assertRaises(Exception):
                Products.create()
                Products.update()
                Products.delete()
            
            if SHOW_GET_LOGS:
                print('\n\nProducts OBJECT tests results:')
                for i in range(len(logs)):
                    print(f'Log {i + 1}° -> {str(logs[i])[:LOGS_CHAR_LEN]} ... LOG TYPE: {type(logs[i])}')

    def test_Config_obj(self):
        with self.app.app_context():
            logs = list()
            # delete users if data base already where running
            users_id = self.get_users_id()

            for id in users_id:
                Config.Users.delete(id)

            for user in users_create_array:
                Config.Users.create(user)
                ans = Config.Users.login(user['user'], user['password'])
                logs.append(ans)

            # update the users and check if there are enough ids in bd
            users_id = self.get_users_id()

            for i in range(len(users_id)):
                if len(users_update_array_missing_id) > i:
                    users_update_array_missing_id[i]['id'] = users_id[i]
                    user = users_update_array_missing_id[i]
                    Config.Users.update(user)
                    ans = Config.Users.login(user['user'], user['password'])
                    logs.append(ans)

            if SHOW_GET_LOGS:
                print('\n\nProducts USERS tests results:')
                for i in range(len(logs)):
                    print(f'Log {i + 1}° -> {str(logs[i])[:LOGS_CHAR_LEN]} ... LOG TYPE: {type(logs[i])}')

if __name__ == "__main__":
    # db builder is not inside test because data bases must 
    # be initialized before tests execution
    db_builder()
    unittest.main()