"""
Custom exceptions
"""


class DatabaseException(Exception):
    """Base database exveption"""
    pass


class NoSuchDatabaseError(DatabaseException):
    """Raises when database not exist"""
    pass


class AlreadyExist(DatabaseException):
    """Raises when any database instance already exist"""
    pass


class NotExist(DatabaseException):
    """Raises when required database instance not exist"""
    pass


class NotAuthorised(Exception):
    """Raises when session tokens not same (used in login_requires decorator)"""
    pass
