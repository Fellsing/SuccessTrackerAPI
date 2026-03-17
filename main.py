from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import math
from database import SessionLocal
from models.models import SuccessDB, CategoryDB ,create_tables
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from schemas import SuccessNote, CategoryNote, UpdateSNote

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_tables()
    yield

app = FastAPI(lifespan=lifespan)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

@app.get("/success/count")
async def read_count(db: Session=Depends(get_db)):
    note=db.query(SuccessDB).count()
    return {"total_successes":note}

@app.get("/success/{note_id}")
async def read_note(note_id: int, db: Session = Depends(get_db) ):
    db_note=db.query(SuccessDB).filter(SuccessDB.id==note_id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return db_note




@app.get("/get_successes")
async def read_notes(db: Session = Depends(get_db)):
    # Запрос к базе: "выбрать все записи из таблицы SuccessDB"
    notes = db.query(SuccessDB).order_by(desc(SuccessDB.creation_date)).all()
    return notes


@app.get("/get_successes_pagination")
async def read_notes(page:int=1, lim:int = 3, db: Session = Depends(get_db)):
    # Запрос к базе: "выбрать все записи из таблицы SuccessDB"
    total_count = db.query(SuccessDB).count()
    total_pages = math.ceil(total_count/lim)
    skip = (page-1)*lim

    notes = db.query(SuccessDB).offset(skip).limit(lim).all()
    return {
        "текущие_записи": notes,
        "всего_страниц": total_pages,
        "текущая_страница": page,
        "всего_записей": total_count
    }

@app.get("/successes/average_priority")
async def read_average(db:Session=Depends(get_db)):
    note = db.query(func.avg(SuccessDB.priority)).scalar()
    return {"average_priority":round(note,2) if note else 0}


@app.post("/add_success")
async def create_note(note: SuccessNote, db: Session = Depends(get_db)):
    # 1. Создаем объект для базы на основе полученных данных
    new_entry = SuccessDB(
        title=note.title,
        description=note.description,
        priority=note.priority,
        category_id = note.category_id
    )
    if db.query(SuccessDB).filter(SuccessDB.title==new_entry.title).first():
        raise HTTPException(status_code=400, detail='Ты это уже делал!!!')
    elif not db.query(CategoryDB).filter(CategoryDB.id==note.category_id).first():
        raise HTTPException(status_code=400, detail=f'Категории с ИД {note.category_id} не существует')
    # 2. Добавляем и сохраняем
    else:
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

    return {"status": "Saved to DB", "id": new_entry.id}



@app.delete("/delete_successes/{note_id}")
async def delete_note(note_id: int, note: SuccessNote, db: Session = Depends(get_db)):
    db_note = db.query(SuccessDB).filter(SuccessDB.id==note_id).first()
    if not db_note:
        return {"error": "Запись не найдена"}
    db.delete(db_note)
    db.commit()
    return {"status": "Deleted from DB", "id": db_note.id}



@app.put("/update_successes/{note_id}")
async def update_success(note_id: int, note: SuccessNote, db: Session = Depends(get_db)):
    db_note = db.query(SuccessDB).filter(SuccessDB.id==note_id).first()
    if not db_note:
        return {"error": "Запись не найдена"}
    db_note.title=note.title
    db_note.description=note.description
    db_note.priority=note.priority
    db.commit()
    db.refresh(db_note)
    return {"status": "Updated", "data": db_note}



@app.get("/successess/filter/")
async def filter_successes(min_value:int =5, db:Session =Depends(get_db)):
    notes = db.query(SuccessDB).filter(SuccessDB.priority<=min_value).all()
    return notes



@app.get("/successess/search/")
async def filter_successes(search_query:str, db:Session =Depends(get_db)):
    notes = db.query(SuccessDB).filter(SuccessDB.title.icontains(search_query)).all()
    return notes



@app.patch("/success/patched_update/{id}", response_model=UpdateSNote)
async def newUpdate(id:int, note:UpdateSNote, db:Session = Depends(get_db)):
    db_note = db.query(SuccessDB).filter(SuccessDB.id==id).first()
    if not db_note:
        raise HTTPException(status_code=400, detail="Такой записи не существует!")
    cng_note = note.model_dump(exclude_unset=True)
    for key, value in cng_note.items():
        setattr(db_note, key, value)

    db.commit()
    db.refresh(db_note)
    return db_note