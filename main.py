import os
import time
from jose import jwt, JWTError

from auth.auth_utils import SECRET_KEY, ALGORITHM
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from loguru import logger

from contextlib import asynccontextmanager
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from auth.auth_utils import get_user_id_from_cookie
from auth.router import router as auth_router
from core.celery_config import send_welcome_email
from routers.successes import router as successes_router
from routers.categories import router as cat_router
from database import SessionLocal, get_db, engine, Base
from models.models import SuccessDB, CategoryDB, create_tables, UserDB
from schemas import SuccessNote, CategoryNote, UpdateSNote


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_tables()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Success Tracker API",
    description="API для отслеживания личных достижений и категорий успеха",
    version="1.0.0",
    contact={"name": "Tamir", "url": "https://github.com/Fellsing/SuccessTrackerAPI"},
)

app.include_router(auth_router)
app.include_router(successes_router)
app.include_router(cat_router)


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger.add(
    os.path.join(LOG_DIR, "app.log"),
    serialize=True,
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    compression="zip",
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    user_identity = "Anon"
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split()[-1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_identity = payload.get("sub")
        except JWTError:
            user_identity = "Invalid token"

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    response.headers["X-Process-Time"] = str(process_time)

    log_msg = f"User {user_identity} | {request.method} | {request.url.path} | Time: {process_time:.4f}s"
    if process_time > 0.5:
        logger.warning(f"Slow request: {log_msg}")
    else:
        logger.info(f"{log_msg}")

    return response


@app.exception_handler(ValueError)
async def valueError_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={
            "Status": "Error",
            "message": "Ошибка валидации данных",
            "details": exc.errors(),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception(f"Database error at {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Ошибка базы данных. Попробуйте позже или свяжитесь с поддержкой."
        },
    )


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_id_from_cookie(request, db)
    if not user_id:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "notes": [],
                "stats": [],
                "user_id": "Войдите в систему",
            },
        )
    notes = (
        db.query(SuccessDB)
        .filter(SuccessDB.owner_id == user_id)
        .order_by(SuccessDB.creation_date.desc())
        .all()
    )

    stats = (
        db.query(
            CategoryDB.category_name.label("category"),
            func.count(SuccessDB.id).label("count"),
        )
        .join(SuccessDB)
        .filter(SuccessDB.owner_id == user_id)
        .group_by(CategoryDB.category_name)
        .all()
    )
    avatar_path = db.query(UserDB).filter(UserDB.id == user_id).first().avatar_path
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notes": notes,
            "stats": stats,
            "user_id": user_id,
            "avatar_path": avatar_path,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/successes/average_priority")
async def read_average(db: Session = Depends(get_db)):
    note = db.query(func.avg(SuccessDB.priority)).scalar()
    return {"average_priority": round(note, 2) if note else 0}


@app.get("/successess/filter/")
async def filter_successes(min_value: int = 5, db: Session = Depends(get_db)):
    notes = db.query(SuccessDB).filter(SuccessDB.priority <= min_value).all()
    return notes


@app.post("/add_success_web")
async def add_success_web(
    header: str = Form(...),
    description: str = Form(None),
    priority: int = Form(...),
    category_name: str = Form(...),
    db: Session = Depends(get_db),
):
    category_name_clean = category_name.strip().capitalize()
    category = (
        db.query(CategoryDB)
        .filter(CategoryDB.category_name == category_name_clean)
        .first()
    )

    if not category:
        category = CategoryDB(category_name=category_name_clean)
        db.add(category)
        db.commit()
        db.refresh(category)

    new_entry = SuccessDB(
        header=header,
        description=description,
        priority=priority,
        category_id=category.id,
        owner_id=2,
    )

    db.add(new_entry)
    db.commit()

    return RedirectResponse(url="/", status_code=303)



@app.get("/test-celery")
async def test_celery(email: str = "test@example.com"):
    send_welcome_email.delay(email)
    return {"status": "Задача ушла в фон. Чек логи воркера через 10 секунд"}