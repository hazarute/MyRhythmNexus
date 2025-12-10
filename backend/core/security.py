from passlib.context import CryptContext
from passlib.exc import UnknownHashError
import bcrypt
# Monkey-patch bcrypt for passlib compatibility (bcrypt >= 4.0.0 removed __about__)
if not hasattr(bcrypt, "__about__"):
    try:
        bcrypt.__about__ = type("About", (object,), {"__version__": bcrypt.__version__})
    except Exception:
        pass

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

    # Lower limit to 50 to be absolutely safe from bcrypt off-by-one or null-terminator issues
    if len(b) > 50:
        logger.info("Password length %d > 50; using pbkdf2_sha256 fallback to avoid bcrypt limits.", len(b))
        # Use the original string (or decoded bytes) for pbkdf2, no need to truncate strictly to 72
        # unless we want to enforce a limit. But pbkdf2 handles long passwords fine.
        # We'll use the string form to be consistent.
        from passlib.context import CryptContext as _CryptContext
        fallback_ctx = _CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        return fallback_ctx.hash(str(password))

    # Safe to hash the original string form
    try:
        return pwd_context.hash(str(password))
    except Exception as e:
        logger.warning("bcrypt hashing failed: %s. Falling back to pbkdf2_sha256.", e)
        from passlib.context import CryptContext as _CryptContext
        fallback_ctx = _CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        return fallback_ctx.hash(str(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against stored hash.

    Tries the configured `pwd_context` (bcrypt) first. If the stored hash
    cannot be identified (legacy or different scheme), fall back to
    `pbkdf2_sha256` verification so older hashes still work.
    """
    if not hashed_password:
        return False

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # Try a fallback verifier for older hashes
        try:
            fallback_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            if fallback_ctx.verify(plain_password, hashed_password):
                logger.info("Password verified using pbkdf2_sha256 fallback; consider re-hashing to bcrypt.")
                return True
        except Exception as e:
            logger.warning("Fallback password verify failed: %s", e)
        return False
    except Exception as e:
        logger.exception("Error verifying password: %s", e)
        return False


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=60)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
