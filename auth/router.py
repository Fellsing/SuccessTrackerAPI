import os
import shutil
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth.auth_utils import (
    get_current_user,
    get_user_id_from_cookie,
    hash_password,
    verify_password,
    create_token,
)
from models.models import SuccessDB, UserDB, CategoryDB
from schemas import UserNote, SuccessNote, UpdateSNote, CategoryNote
from database import SessionLocal, get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup", status_code=status.HTTP_201_CREATED, summary="Регистрация пользователя"
)
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

    return {
        "message": "Пользователь успешно зарегистрирован",
        "username": new_user.username,
    }


@router.post("/signin", status_code=status.HTTP_202_ACCEPTED, summary="Вход в систему")
def login_user(user_data: UserNote, db: Session = Depends(get_db)):
    check_user = db.query(UserDB).filter(UserDB.username == user_data.username).first()
    if not check_user or not verify_password(
        user_data.password, check_user.hashed_pass
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )

    if verify_password(user_data.password, check_user.hashed_pass):
        access_token = create_token(data={"sub": user_data.username})
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Успешный вход",
        }
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,  # Защита от кражи токена через JS
        max_age=1800,  # Время жизни (30 мин)
        samesite="lax",
    )

    return response


@router.post("/upload_avatar")
async def upload_avatar(
    request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    user_id = get_user_id_from_cookie(request, db)
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Только jpeg, jpg или png")
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user.avatar_path:
        old_file_path = user.avatar_path.lstrip("/")
        if os.path.exists(old_file_path):
            os.remove(old_file_path)
    file_extension = file.filename.split(".")[-1]
    file_name = f"user_{user_id}.{file_extension}"
    file_path = f"static/avatars/{file_name}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    user.avatar_path = f"/{file_path}"
    db.commit()
    return {"msg": "Автар обновлен", "path": user.avatar_path}


@router.delete("/delete_account")
async def delete_acc(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_id_from_cookie(request, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user.avatar_path:
        avatar_path = user.avatar_path.lstrip("/")
        if os.path.exists(avatar_path):
            try:
                os.remove(avatar_path)
            except Exception as e:
                return f"Error while removing file: {e}"
    db.delete(user)
    db.commit()
    response = JSONResponse(content={"msg": "Аккаунт полностью удален"})
    response.delete_cookie("access_token") 
    return response
    # return {"msg": "Пользователь удален", "user_id": user_id}
