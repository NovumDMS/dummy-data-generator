from alabaster import DbConnect, FilePaths, MODE
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
def get_random_customer():
    sql = """
        SELECT TOP 1 A.[name] AS 'ship_to_name', A.phys_address1, A.phys_city, A.phys_state, A.phys_postal_code
        FROM p21_view_ship_to S
            INNER JOIN p21_view_address A ON S.ship_to_id = A.id
        WHERE S.customer_id = 26242
            AND S.delete_flag = 'N'
            AND S.ship_to_id <> 26242
        ORDER BY NEWID();
    """

    with pyodbc.connect(connection_string) as cn:
        cur = cn.cursor()
        cur.execute(sql)
        return cur.fetchone()
    

def get_random_items(num_items):
    sql = f'SELECT TOP {num_items}'
    sql += " RIGHT(M.item_id, LEN(M.item_id) - 2) AS 'item_id', M.default_selling_unit AS 'unit_of_measure', "
    sql += "L.qty_on_hand - L.qty_allocated AS 'qty_available' FROM p21_view_inv_mast M "
    sql += "INNER JOIN p21_view_inv_loc L ON M.inv_mast_uid = L.inv_mast_uid "
    sql += "WHERE M.delete_flag = 'N' AND L.location_id = 1075 AND L.qty_on_hand - L.qty_allocated > 0"
    sql += "ORDER BY NEWID();" # randomize the results

    with pyodbc.connect(connection_string) as cn:
        cur = cn.cursor()
        cur.execute(sql)
        return list(cur.fetchall())


def create_random_order_id():
    # the 9 at the beginning helps me identify a bogus order number
    last_four = random.randint(1000, 9999)
    return int(f'99{last_four}')


def create_csv_file():
    customer = get_random_customer()
    items = get_random_items(random.randint(1, 11))
    order_id = create_random_order_id()

    with open(f'{LOCAL_FOLDER}/Prolink_940_{order_id}_{filename_date}.csv', 'w') as csvfile:
        line_num = 10
        for item in items:
            random_qty = random.randint(1, int(item.qty_available))
            
            write_string = f'PLC|A|A|{order_id}|{order_id}|{formatted_date}||{formatted_date}|||RTE|LT|PP|||||||||||||'
            write_string += f'{customer.ship_to_name}|{customer.phys_address1}||{customer.phys_city}|{customer.phys_state}|'
            write_string += f'{customer.phys_postal_code}||{line_num}|{item.item_id}|{random_qty}|{item.unit_of_measure}|'

            csvfile.write(write_string+'\n')

            line_num += 10


if __name__ == '__main__':
    for i in range(3):
        create_csv_file()
        print('File created successfully.')