class TokenExpiryException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class NoMoreTweetsError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class TokenNotFoundError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class AccessError(Exception):
    pass
