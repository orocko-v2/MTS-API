import bcrypt, configparser, DatabaseConnector, Requests, config_path_file
from Exceptions import UserRegisterException

@staticmethod
def generateHash(password_str):
    """
    Generates hash from user password
    :param password_str: User password in string format
    :return:
    """
    return bcrypt.hashpw(password_str.encode('utf-8'), bcrypt.gensalt())

def checkHash(userpassword, hash):
    """
    Check if inputted password and stored hash are similar
    :param userpassword: inputted password
    :param hash: stored hash
    :return: True of False
    """
    try:
        return bcrypt.checkpw(password=userpassword.encode('utf-8'), hashed_password=hash)
    except Exception as e:
        print(e.args[0])
        try:
            return bcrypt.checkpw(password=userpassword, hashed_password=hash)
        except Exception as e:
            print(e.args[0])
            return False

def RegisterNewUser(login, password):
    """
    Add user login and password to a database
    :param login: user login
    :param password: user password
    """
    if isinstance(Requests.getAccessToken(login, password), str):
        hash_password_str = generateHash(password).decode("utf-8")
        DatabaseConnector.addDataToDatabase((login, hash_password_str), 'mtsapi.users')
    else:
        raise UserRegisterException()

def LoginUser(login, password):
    """
    Get password from database to log user in
    :param login: login inputted by user
    :param password: password inputted by user
    """
    conn = DatabaseConnector.connectToDatabase()
    with conn.cursor() as cursor:
        query = "SELECT user_password_hash from mtsapi.users where user_login = %s"
        cursor.execute(query, [login])
        db_password = cursor.fetchone()[0]
    if checkHash(password, db_password.encode('utf-8')):
        print("Success")
        global _login
        _login = login
        global _password
        _password = password
        Requests.token = Requests.getAccessToken(login, password)
        return Requests.token
    else:
        return None
