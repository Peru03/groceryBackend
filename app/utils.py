from passlib.context import CryptContext

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password_safe(password: str) -> str:
    """
    Hash password with bcrypt safely.
    Truncates to 72 bytes to avoid bcrypt errors.
    """
    password_bytes = password.encode("utf-8")[:72]
    safe_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(safe_password)

def verify_password_safe(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash, truncating to 72 bytes.
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    safe_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.verify(safe_password, hashed_password)
