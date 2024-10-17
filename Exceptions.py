class FlagDoesNotExistsException(Exception):
    """
    Exception raised when make not allowed request
    """
    def __init__(self, flag, message="Флаг не существует"):
        self.flag = flag
        self.message = message
        super().__init__(self.message)


class UserRegisterException(Exception):
    """
    Exception raised when login and password are incorrect
    """
    def __init__(self, message="Невозможно получить токен при помощи введенных данных"):
        self.message = message
        super().__init__(self.message)

class WrongPasswordException(Exception):
    def __init__(self, message="Неправильный логин или пароль"):
        self.message = message
        super().__init__(self.message)


