from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import bcrypt
from jose import JWTError, jwt
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import AuthSession, User
from utils.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, session_id: str | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now, "sid": session_id})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_session(db: Session, user: User) -> tuple[AuthSession, str]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    session = AuthSession(id=str(uuid.uuid4()), user_id=user.id, expires_at=expires_at)
    db.add(session)
    db.commit()
    token = create_access_token({"sub": str(user.id), "role": user.role}, session_id=session.id)
    return session, token

def get_current_user(
    bearer_token: str | None = Depends(oauth2_scheme),
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = bearer_token or access_token
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        if user_id is None or session_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    session = db.query(AuthSession).filter(
        AuthSession.id == session_id,
        AuthSession.user_id == int(user_id),
        AuthSession.revoked_at.is_(None),
    ).first()
    if not session:
        raise credentials_exception
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def revoke_session(token: str | None, db: Session) -> None:
    if not token:
        return
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        session_id = payload.get("sid")
    except JWTError:
        return
    if not session_id:
        return
    session = db.query(AuthSession).filter(AuthSession.id == session_id).first()
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
