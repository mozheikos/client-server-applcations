class DatabaseException(Exception):
    pass


class NoSuchDatabaseError(DatabaseException):
    pass


class UserAlreadyExist(DatabaseException):
    pass


class UserNotExist(DatabaseException):
    pass


class DatabaseNotExist(Exception):
    pass


class StopSendingError(Exception):
    pass
