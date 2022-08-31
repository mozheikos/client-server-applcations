from common.config import settings
import hashlib


def get_hashed_password(password: str) -> str:
    salt = hashlib.sha256(settings.SALT.encode()).hexdigest()

    return hashlib.sha256((salt + password).encode()).hexdigest()


def generate_session_token(username: str) -> str:
    """Generate session token"""

    salt = hashlib.sha256("salt".encode()).hexdigest()
    token = hashlib.sha256((salt + username).encode()).hexdigest()
    return token
