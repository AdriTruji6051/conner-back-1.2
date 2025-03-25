create_products_keys_good= ["code", "description", "sale_type", "cost", "sale_price", "department", "wholesale_price", "priority", "inventory", "parent_code"]

products_create_good_array = [
    {
        'code': '1',
        'description': 'TEST1',
        'sale_type': 'D',
        'cost': 23,
        'sale_price': 30,
        'department' : None,
        'wholesale_price': 25,
        'priority': 1,
        'inventory': 1,
        'parent_code': None
    },
    {
        'code': '2',
        'description': 'TEST2',
        'sale_type': 'U',
        'cost': 230,
        'sale_price': 300,
        'department' : None,
        'wholesale_price': 250,
        'priority': 0,
        'inventory': 100,
        'parent_code': None
    },
    {
        'code': '3',
        'description': 'TEST3',
        'sale_type': 'D',
        'cost': 423,
        'sale_price': 430,
        'department' : None,
        'wholesale_price': 425,
        'priority': 0,
        'inventory': 41,
        'parent_code': None
    },
    {
        'code': '4',
        'description': 'TEST4',
        'sale_type': 'U',
        'cost': 45230,
        'sale_price': 45300,
        'department' : None,
        'wholesale_price': 45250,
        'priority': 0,
        'inventory': 45100,
        'parent_code': None
    },
]

products_update_good_array = [
    {
        'code': '11',
        'description': 'TEST1-1-U',
        'sale_type': 'U',
        'cost': 40,
        'sale_price': 100,
        'department' : None,
        'wholesale_price': 85,
        'priority': 1,
        'inventory': 16,
        'parent_code': None,
        'original_code': '1'
    },
    {
        'code': '22',
        'description': 'TEST2-2-U',
        'sale_type': 'U',
        'cost': 405,
        'sale_price': 1005,
        'department' : None,
        'wholesale_price': 855,
        'priority': 1,
        'inventory': 165,
        'parent_code': None,
        'original_code': '2'
    },
    {
        'code': '33',
        'description': 'TEST3-3-3-U',
        'sale_type': 'U',
        'cost': 4053,
        'sale_price': 10053,
        'department' : None,
        'wholesale_price': 8553,
        'priority': 0,
        'inventory': 1653,
        'parent_code': None,
        'original_code': '3'
    },
    {
        'code': '44',
        'description': 'TEST4-4-U',
        'sale_type': 'U',
        'cost': 4054,
        'sale_price': 10054,
        'department' : None,
        'wholesale_price': 8554,
        'priority': 1,
        'inventory': 1654,
        'parent_code': None,
        'original_code': '4'
    }
]

products_create_bad_array = [
    {
        'code': 'BADTESTCODE123',
        'description': 'BADTESTDESCRIPTION123',
        'sale_type': 'I',
        'cost': 230,
        'sale_price': 30,
        'priority': 1,
        'parent_code': None
    },
    {
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
]

associates_codes_create_before_update = [
    {
        'code' : 'ass_1', 
        'parent_code' : '1',
        'tag' : 'test tag 1'
    },
        {
        'code' : 'ass_2', 
        'parent_code' : '2',
        'tag' : 'test tag 2'
    },
        {
        'code' : 'ass_3', 
        'parent_code' : '3',
        'tag' : 'test tag 3'
    },
        {
        'code' : 'ass_4', 
        'parent_code' : '4',
        'tag' : 'test tag 4'
    },
]

associates_codes_create_after_update = [
    {
        'code' : 'ass_1_AU', 
        'parent_code' : '11',
        'tag' : 'test tag 1_AU'
    },
        {
        'code' : 'ass_2_AU', 
        'parent_code' : '22',
        'tag' : 'test tag 2_AU'
    },
        {
        'code' : 'ass_3_AU', 
        'parent_code' : '33',
        'tag' : 'test tag 3_AU'
    },
        {
        'code' : 'ass_4_AU', 
        'parent_code' : '44',
        'tag' : 'test tag 4_AU'
    },
]

associates_codes_update_before_update = [
    {
        'code' : 'ass_1_U_4', 
        'parent_code' : '4',
        'tag' : 'test tag 1_U_4',
        'original_code' : 'ass_1',
    },
    {
        'code' : 'ass_2_U_3', 
        'parent_code' : '3',
        'tag' : 'test tag 2_U_3',
        'original_code' : 'ass_2',
    },
        {
        'code' : 'ass_3_U_2', 
        'parent_code' : '2',
        'tag' : 'test tag 3_U_2',
        'original_code' : 'ass_3',
    },
        {
        'code' : 'ass_4_U_1', 
        'parent_code' : '1',
        'tag' : 'test tag 4_U_1',
        'original_code' : 'ass_4',
    },
]

associates_codes_update_after_update = [
    {
        'code' : 'ass_1_AU_4', 
        'parent_code' : '11',
        'tag' : 'test tag 1_AU_4',
        'original_code' : 'ass_1_AU',
    },
        {
        'code' : 'ass_2-AU_3', 
        'parent_code' : '22',
        'tag' : 'test tag 2_AU_3',
        'original_code' : 'ass_2_AU',
    },
        {
        'code' : 'ass_3_AU_2', 
        'parent_code' : '33',
        'tag' : 'test tag 3_AU_2',
        'original_code' : 'ass_3_AU',
    },
        {
        'code' : 'ass_4_AU_1', 
        'parent_code' : '44',
        'tag' : 'test tag 4_AU_1',
        'original_code' : 'ass_4_AU',
    },
]

users_create_array = [
    {
        'user': 'erika123', 
        'user_name': 'Erika Trujillo', 
        'password': '123456', 
        'role_type': 'user', 
    },
    {
        'user': 'adrian123', 
        'user_name': 'Adrian Ramirez', 
        'password': '654321', 
        'role_type': 'admin', 
    },
    {
        'user': '12jimin34', 
        'user_name': 'Jimin Robles', 
        'password': 'password', 
        'role_type': 'invited', 
    },
]

users_update_array_missing_id = [
    {
        'user': 'erika123_UPDATE', 
        'user_name': 'Erika Trujillo UPDATE', 
        'password': '123456UPDATE', 
        'role_type': 'admin', 
    },
    {
        'user': 'adrian123UPDATE', 
        'user_name': 'Adrian Ramirez UPDATE', 
        'password': '654321', 
        'role_type': 'admin', 
    },
    {
        'user': '12jimin34UPDATE', 
        'user_name': 'Jimin Robles UPDATE', 
        'password': 'passwordUPDATE', 
        'role_type': 'admin', 
    },
]

