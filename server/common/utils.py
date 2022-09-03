from common.config import settings
import hashlib


def get_hashed_password(password: str) -> str:
    """
    generate hash of password with salt (set in config.json)
    :param password: str
    :return: str
    """

    salt = hashlib.sha256(settings.SALT.encode()).hexdigest()

    return hashlib.sha256((salt + password).encode()).hexdigest()


def generate_session_token(username: str) -> str:
    """
    Generate session token
    :param username: str
    :return: str
    """

    salt = hashlib.sha256("salt".encode()).hexdigest()
    token = hashlib.sha256((salt + username).encode()).hexdigest()
    return token
