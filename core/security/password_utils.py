# Simple password utilities using Passlib for hashing and verification
from passlib.context import CryptContext

# Initialize Passlib CryptContext with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes the given password using bcrypt via Passlib."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the given hash using Passlib."""
    return pwd_context.verify(plain_password, hashed_password)
