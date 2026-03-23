from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth.auth_utils import hash_password, verify_password, create_token
from models.models import SuccessDB, UserDB, CategoryDB
from schemas import UserNote, SuccessNote, UpdateSNote, CategoryNote
from database import SessionLocal,get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, summary="Регистрация пользователя")
def create_user(user_data: UserNote, db: Session = Depends(get_db)):
    check_user = db.query(UserDB).filter(UserDB.username == user_data.username).first()
    if check_user:
        raise HTTPException(
            status_code=400, detail="Пользователь с таким именем уже существует"
        )
    hashed_password = hash_password(user_data.password)
    new_user = UserDB(username=user_data.username, hashed_pass=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Пользователь успешно зарегистрирован"}


@router.post("/signin", status_code=status.HTTP_202_ACCEPTED, summary="Вход в систему")
def login_user(user_data:OAuth2PasswordRequestForm=Depends(), db:Session=Depends(get_db)):
    check_user = db.query(UserDB).filter(UserDB.username == user_data.username).first()
    if not check_user or not verify_password(user_data.password, check_user.hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверное имя пользователя или пароль"
        )
    
    if verify_password(user_data.password, check_user.hashed_pass):
        access_token = create_token(data={"sub":user_data.username})

    return {"access_token": access_token, "token_type": "bearer"}