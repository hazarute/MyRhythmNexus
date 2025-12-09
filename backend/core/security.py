from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte input limit. If a password (utf-8) is longer,
    # truncate to 72 bytes to avoid ValueError from the bcrypt backend.
    # Ensure we have bytes to measure length reliably
    if isinstance(password, bytes):
        b = password
    else:
        b = str(password).encode("utf-8")

    if len(b) > 72:
        logger.warning("Password longer than 72 bytes; truncating for bcrypt compatibility.")
        truncated = b[:72].decode("utf-8", "ignore")
        try:
            return pwd_context.hash(truncated)
        except Exception as e:
            logger.warning("bcrypt hashing failed after truncation: %s. Falling back to pbkdf2_sha256.", e)
            from passlib.context import CryptContext as _CryptContext
            fallback_ctx = _CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            return fallback_ctx.hash(truncated)

    # Safe to hash the original string form
    try:
        return pwd_context.hash(str(password))
    except Exception as e:
        logger.warning("bcrypt hashing failed: %s. Falling back to pbkdf2_sha256.", e)
        from passlib.context import CryptContext as _CryptContext
        fallback_ctx = _CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        return fallback_ctx.hash(str(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=60)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
