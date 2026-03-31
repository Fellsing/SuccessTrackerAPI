from passlib.context import CryptContext
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
import datetime
from datetime import timedelta, timezone, datetime
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session


from typing import Optional


from database import get_db
from models.models import UserDB

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    print(f"DEBUG: Тип пароля: {type(password)}, Длина: {len(password)}")
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict):
    data_copy = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    data_copy["exp"] = expire
    return jwt.encode(data_copy, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Не удалось подтвердить учетные данные",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        user = db.query(UserDB).filter(UserDB.username == username).first()
        if user is None:
            raise credentials_exception

        return user
    except JWTError:
        raise credentials_exception


def get_user_id_from_cookie(request: Request, db: Session) -> Optional[int]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")

    try:
        scheme, _, param = token.partition(" ")
        payload = jwt.decode(
            param if param else scheme, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        user = (
            db.query(UserDB)
            .filter((UserDB.username == username) | (UserDB.email == username))
            .first()
        )
        return int(user.id) if user else None
    except (JWTError, ValueError):
        return None
