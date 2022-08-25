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
