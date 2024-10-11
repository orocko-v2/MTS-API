class FlagDoesNotExistsException(Exception):
    """
    Exception raised when make not allowed request
    """
    def __init__(self, flag, message="Flag does not exists"):
        self.flag = flag
        self.message = message
        super().__init__(self.message)


class UserRegisterException(Exception):
    """
    Exception raised when login and password are incorrect
    """
    def __init__(self, message="Can't get token using current login and password"):
        super.__init__(self.message)

