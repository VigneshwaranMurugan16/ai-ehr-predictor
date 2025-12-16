from datetime import datetime, timedelta
from typing import List, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User, AuditLog
from app.auth import SECRET_KEY, ALGORITHM, get_user_claims, create_access_token, verify_password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ----- DB dependency -----

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----- User helpers -----

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username=username)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(required_roles: List[str]) -> Callable:
    def _inner(user: User = Depends(get_current_user)):
        if user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user
    return _inner


# ----- Audit logging -----

def log_action(
    db: Session,
    user: User,
    action: str,
    details: str | None = None,
) -> None:
    entry = AuditLog(
        user_id=user.id,
        action=action,
        details=details,
    )
    db.add(entry)
    # caller decides when to commit
