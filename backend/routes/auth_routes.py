from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import User
from models.schemas import UserCreate, UserOut, Token
from services.auth_service import hash_password, verify_password, create_session, get_current_user, revoke_session
from utils.config import settings
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    username = payload.username.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "Username already taken")
    user = User(
        email=email,
        username=username,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email or username already exists")
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(response: Response, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    _, token = create_session(db, user)
    response.set_cookie(
        "access_token", token, httponly=True, secure=settings.COOKIE_SECURE,
        samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/",
    )
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    revoke_session(access_token, db)
    response.delete_cookie("access_token", path="/")
    response.status_code = 204
    return None
