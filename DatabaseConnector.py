import psycopg2, config_path_file, configparser
from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2 import errors

from Exceptions import DatabaseConnectionException


def connectToDatabase():
    """
    Connect to a database
    :return: database connection
    """
    config = configparser.ConfigParser()
    config.read(config_path_file.CONFIG_PATH)
    dbname = config['database']['dbname']
    user = config['database']['user']
    password = config['database']['password']
    host = config['database']['host']
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        return conn
    except:
        raise DatabaseConnectionException


#rename to addLogPass or let add all data
def addDataToDatabase(data, table_name):
    """
    Add data to database
    :param data: data to add
    :param table_name: table where to add data
    """
    conn = connectToDatabase()
    with conn.cursor() as cursor:
        query = "INSERT INTO %s (user_id, user_login, user_password_hash) values (DEFAULT, %%s, %%s);" % table_name
        try:
            cursor.execute(query, data)
        except errors.lookup(UNIQUE_VIOLATION) as e:
            raise e('Login already exists')
        cursor.close()
    conn.commit()
    conn.close()

def getDataFromDatabase(table_name):
    """
    Get * from table
    :param table_name: table to get info from
    :return: data
    """
    conn = connectToDatabase()
    with conn.cursor() as cursor:
        query = f'select * from {table_name}'
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
    conn.close()
    return data