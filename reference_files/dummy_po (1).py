from alabaster import DbConnect
import pyodbc
import random
from datetime import datetime, timedelta
import sys
import parse_timestamp as pt

# Database configuration
DB_HOST = DbConnect.DB_HOST
DB_NAME = DbConnect.DB_NAME
DB_USER = DbConnect.DB_USER
DB_PASSWORD = DbConnect.DB_PASSWORD

LOCAL_FOLDER = 'C:/ProLink/Dummy Docs'

connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_HOST};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
)

today = datetime.now().date()
formatted_date = today.strftime("%m/%d/%y")
filename_date = datetime.now().strftime('%Y%m%d%H%M%S')

# given the data above, I need to create a CSV file with dummy data. For practical purposes, I will create a CSV file with 5 rows of data.
def get_random_division():
    sql = """
        SELECT TOP 1 division_id
        FROM p21_view_division
        WHERE supplier_id = 26242
            AND delete_flag = 'N'
        ORDER BY NEWID();
    """

    with pyodbc.connect(connection_string) as cn:
        cur = cn.cursor()
        cur.execute(sql)
        return list(cur.fetchone())[0]
    

def get_random_items(num_items, division_id):    
    sql = f'SELECT TOP {num_items}'
    sql += " RIGHT(M.item_id, LEN(M.item_id) - 2) AS 'item_id', M.default_selling_unit AS 'unit_of_measure', "
    sql += "L.qty_on_hand - L.qty_allocated AS 'qty_available' "
    sql += """FROM p21_view_inv_mast M INNER JOIN p21_view_inv_loc L ON M.inv_mast_uid = L.inv_mast_uid
            INNER JOIN p21_view_inventory_supplier X ON M.inv_mast_uid = X.inv_mast_uid
            INNER JOIN p21_view_inventory_supplier_x_loc W ON
                (X.inventory_supplier_uid = W.inventory_supplier_uid
                    AND L.location_id = W.location_id
                    AND W.primary_supplier = 'Y')
            INNER JOIN p21_view_division D ON X.supplier_id = D.supplier_id
        WHERE M.delete_flag = 'N'
            AND L.location_id = 1075
            AND L.qty_on_hand - L.qty_allocated > 0
            """
    sql += f"AND D.division_id = {division_id} ORDER BY NEWID();"
    
    with pyodbc.connect(connection_string) as cn:
        cur = cn.cursor()
        cur.execute(sql)
        return list(cur.fetchall())


def create_random_order_id():
    # the 9 at the beginning helps me identify a bogus order number
    last_five = random.randint(10000, 99999)
    return int(f'98{last_five}')


def create_csv_file():
    division = get_random_division()
    items = get_random_items(random.randint(7, 20), division)
    order_id = create_random_order_id()

    with open(f'{LOCAL_FOLDER}/Prolink_943_{order_id}_{filename_date}.csv', 'w') as csvfile:
        line_num = 10
        for item in items:
            random_qty = random.randint(1, int(item.qty_available))

            write_string = f'N|PLC|{order_id}|{order_id}|{formatted_date}||LT|{line_num}|{item.item_id}|{random_qty}|CS|'

            csvfile.write(write_string+'\n')

            line_num += 10


if __name__ == '__main__':
    for i in range(5):
        create_csv_file()
        print('File created successfully.')