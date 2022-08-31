class DatabaseException(Exception):
    pass


class NoSuchDatabaseError(DatabaseException):
    pass


class AlreadyExist(DatabaseException):
    pass


class StopSendingError(Exception):
    pass


class NotExist(Exception):
    pass


class NotKeyError(Exception):
    pass


class NotAuthorised(Exception):
    pass
