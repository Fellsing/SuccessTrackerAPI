from fastapi import APIRouter, Depends, HTTPException
import math
from sqlalchemy import desc
from sqlalchemy.orm import Session
from database import get_db
from models.models import SuccessDB, CategoryDB, UserDB
from auth.auth_utils import get_current_user
from schemas import SuccessNote, UpdateSNote, SuccessCreate

router = APIRouter(prefix="/successes", tags=["Successes"])


@router.post("/add_success")
async def create_note(
    note: SuccessCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    category = (
        db.query(CategoryDB)
        .filter(CategoryDB.category_name == note.category_name)
        .first()
    )
    # Если нет категории, то добавляем ее
    if not category:
        category = CategoryDB(category_name=note.category_name)
        db.add(category)
        db.commit()
        db.refresh(category)
    note_data = note.model_dump(exclude={"category_name"})
    # Создаем объект для базы на основе полученных данных
    new_entry = SuccessDB(
        **note_data, category_id=category.id, owner_id=current_user.id
    )
    if (
        db.query(SuccessDB)
        .filter(
            SuccessDB.header == new_entry.header, SuccessDB.owner_id == current_user.id
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Ты это уже делал!!!")
    # 2. Добавляем и сохраняем
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {"status": "Saved to DB", "id": new_entry.id}


@router.get("/success/{note_id}")
async def read_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_note = db.query(SuccessDB).filter(SuccessDB.id == note_id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    if db_note.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="У текущего пользователя нет такой заметки"
        )
    return db_note


@router.get("/get_successes")
async def read_notes(
    db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    # Запрос к базе: "выбрать все записи из таблицы SuccessDB"
    notes = (
        db.query(SuccessDB)
        .filter(SuccessDB.owner_id == current_user.id)
        .order_by(desc(SuccessDB.creation_date))
        .all()
    )
    return notes


@router.get("/get_successes_pagination")
async def read_notes_by_page(
    page: int = 1,
    lim: int = 3,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    # Запрос к базе: "выбрать все записи из таблицы SuccessDB"
    total_count = (
        db.query(SuccessDB).filter(SuccessDB.owner_id == current_user.id).count()
    )
    total_pages = math.ceil(total_count / lim)
    skip = (page - 1) * lim

    notes = (
        db.query(SuccessDB)
        .filter(SuccessDB.owner_id == current_user.id)
        .offset(skip)
        .limit(lim)
        .all()
    )
    return {
        "текущие_записи": notes,
        "всего_страниц": total_pages,
        "текущая_страница": page,
        "всего_записей": total_count,
    }


@router.delete("/delete_successes/{note_id}")
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_note = db.query(SuccessDB).filter(SuccessDB.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=400, detail="Такой записи не существует!")
    if db_note.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="У текущего пользователя нет такой заметки"
        )
    db.delete(db_note)
    db.commit()
    return {"status": "Deleted from DB", "id": db_note.id}


# изменение всех данных в заметке(кроме ИД, разумеется)
@router.put("/update_successes/{note_id}", response_model=UpdateSNote)
async def update_success(
    note_id: int,
    note: SuccessNote,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_note = db.query(SuccessDB).filter(SuccessDB.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=400, detail="Такой записи не существует!")
    if db_note.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="У текущего пользователя нет такой заметки"
        )
    db_note.title = note.title
    db_note.description = note.description
    db_note.priority = note.priority
    db.commit()
    db.refresh(db_note)
    return {"status": "Updated", "data": db_note}


# изменение только тех полей, которые буду внесены (кроме ИД, разумеется)
@router.patch("/success/patched_update/{id}", response_model=UpdateSNote)
async def newUpdate(
    id: int,
    note: UpdateSNote,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_note = db.query(SuccessDB).filter(SuccessDB.id == id).first()
    if not db_note:
        raise HTTPException(status_code=400, detail="Такой записи не существует!")
    if db_note.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="У текущего пользователя нет такой заметки"
        )
    cng_note = note.model_dump(exclude_unset=True)
    for key, value in cng_note.items():
        setattr(db_note, key, value)

    db.commit()
    db.refresh(db_note)
    return db_note


# поиск заметки по названию заголовка
@router.get("/successess/search/")
async def filter_successes(
    search_query: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    notes = (
        db.query(SuccessDB)
        .filter(
            SuccessDB.title.icontains(search_query),
            current_user.id == SuccessDB.owner_id,
        )
        .all()
    )
    if not notes:
        return {
            "status": "OK",
            "message": f"По ключевому слову '{search_query}' не найдено записей.",
        }
    else:
        return notes
