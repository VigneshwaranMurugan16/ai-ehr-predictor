from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from app.models import User

# #In real production, move to env vars
# SECRET_KEY = "change-this-secret-in-env"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# pwd_context = CryptContext(
#     schemes=["pbkdf2_sha256"],
#     deprecated="auto",
# )


#Use argon2 instead of bcrypt for Python 3.13 compatibility
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

#Use argon2 (more modern, better for Python 3.13)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_claims(user: User) -> dict:
    return {"sub": user.username, "role": user.role}
