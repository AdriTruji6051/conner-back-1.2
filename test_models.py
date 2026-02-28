import unittest
from datetime import datetime

from test_models_data import (
    products_create_good_array,
    products_update_good_array,
    associates_codes_create_before_update,
    associates_codes_update_before_update,
    associates_codes_create_after_update,
    associates_codes_update_after_update,
    products_create_bad_array,
    users_create_array,
    users_update_array_missing_id,
    users_create_bad_array,
    font_configs_create,
    drawer_logs_create_array,
    tickets_create_array,
    tickets_create_bad_array,
)

from run import create_app
from app.models.products import Products
from app.models.analytics import Analytics
from app.models.config import Config
from app.models.tickets import Tickets

from app.connections.connections import init_db
from app.helpers.helpers import ValidationError

SHOW_GET_LOGS = True
LOGS_CHAR_LEN = None

def db_builder():
    app = create_app()
    with app.app_context():
        init_db()

def show_logs(logs_obj_name: str, logs: list):
    if SHOW_GET_LOGS:
        print(f'\n\n{logs_obj_name} OBJECT tests results:')
        for i in range(len(logs)):
            print(f'Log {i + 1}° -> {str(logs[i])[:LOGS_CHAR_LEN]} ... LOG TYPE: {type(logs[i])}')

class main_test(unittest.TestCase):
    app = create_app()

    def get_users_id(self):
        users_id = []

        with self.app.app_context():
            # get the users if exist to delete to avoid problems at testing
            try:
                users = Config.Users.get_all()
                users_id = [user.id for user in users]
            except Exception as e:
                print(e)
                users_id = []
        
        return users_id
    
    def test_b_Products_obj(self):
        with self.app.app_context():
            #Delete test codes if data base already were running
            logs = []
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
                Products.Associates_codes.delete(obj['code'])

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
            
            show_logs('Products', logs)

    def test_Config_obj(self):
        with self.app.app_context():
            logs = []
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

            for user in users_create_bad_array:
                with self.assertRaises(Exception):
                    Config.Users.create(user)
                    ans = Config.Users.login(user['user'], user['password'])
                    logs.append(ans)

            for font in font_configs_create:
                Config.Ticket_text.createFont(font['font'], font['weigh'], font['size'])
            
            if(len(Config.Ticket_text.getFonts()) < 2): 
                raise ValueError('There are not enough fonts in the database')

            show_logs('Config', logs)

    def test_Analitycs_obj(self):
        # Product_changes sub object is not tested there because it is called
        # and tested by Products object
        with self.app.app_context():
            logs = []
            for obj in drawer_logs_create_array:
                Analytics.Drawer_logs.create(obj)
            
            ans1 = Analytics.Drawer_logs.get_all('YYYY-MM-DD')
            ans2 = Analytics.Drawer_logs.get(ans1[0].id)
            logs.append(ans1)
            logs.append(ans2)

            show_logs('Analytics', logs)

    
    def test_z_Tickets_obj(self):
        with self.app.app_context():
            logs = []
            tickets = Tickets.list_created_at(datetime.now().strftime('%Y-%m-%d'))
            logs.append(tickets)
            
            for ticket in tickets:
                Tickets.delete(ticket.id)

            for ticket in tickets_create_array:
                logs.append(Tickets.create(ticket))

            # Delete a product in ticket should not raise an error
            Products.delete(products_update_good_array[0]['code'])
            
            with self.assertRaises(ValidationError):
                for ticket in tickets_create_bad_array:
                    Tickets.create(ticket)


        
        show_logs('Tickets', logs)

if __name__ == "__main__":
    SHOW_GET_LOGS = False
    LOGS_CHAR_LEN = None
    db_builder()

    unittest.main()