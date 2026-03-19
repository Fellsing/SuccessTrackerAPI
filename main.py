from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from auth.router import router as auth_router
from routers.successes import router as successes_router
from database import SessionLocal, get_db, engine,Base
from models.models import  SuccessDB, CategoryDB ,create_tables, UserDB
from schemas import SuccessNote, CategoryNote, UpdateSNote




@asynccontextmanager
async def lifespan(app:FastAPI):
    create_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(successes_router)



@app.post("/categories")
async def add_category(nte:CategoryNote, db:Session = Depends(get_db)):
    db_note = CategoryDB(category_name=nte.category_name)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return {"status": "Saved to DB", "id": db_note.id}

@app.get("/")
async def root():
    return {"message": "Привет! Твой сервер FastAPI запущен и работает"}

@app.get("/successes/average_priority")
async def read_average(db:Session=Depends(get_db)):
    note = db.query(func.avg(SuccessDB.priority)).scalar()
    return {"average_priority":round(note,2) if note else 0}

@app.get("/successess/filter/")
async def filter_successes(min_value:int =5, db:Session =Depends(get_db)):
    notes = db.query(SuccessDB).filter(SuccessDB.priority<=min_value).all()
    return notes