from fastapi import APIRouter, Depends, HTTPException
import math
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from database import get_db
from models.models import SuccessDB, CategoryDB, UserDB
from auth.auth_utils import get_current_user
from schemas import SuccessNote, UpdateSNote, SuccessCreate, CategoryStat

router = APIRouter(prefix="/successes", tags=["Successes"])


@router.post("/add_success", summary="Создать новый успех")
async def create_note(
    note: SuccessCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    category = (
        db.query(CategoryDB)
        .filter(CategoryDB.category_name == note.category_name.strip().capitalize())
        .first()
    )
    # Если нет категории, то добавляем ее
    if not category:
        category = CategoryDB(category_name=note.category_name.strip().capitalize())
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

    return new_entry


@router.get(
    "/get_stats",
    response_model=list[CategoryStat],
    summary="Вывести статистику",
    description="Выводит статистику по количеству успехов, принадлежащим к каждой категории авторизованному пользователю",
)
async def get_stats(
    db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    stats = (
        db.query(
            CategoryDB.category_name.label("category"),
            func.count(SuccessDB.id).label("count"),
        )
        .join(SuccessDB)
        .filter(SuccessDB.owner_id == current_user.id)
        .group_by(CategoryDB.category_name)
        .all()
    )
    return stats


@router.get(
    "/success/{note_id}",
    summary="Вывести успех по Id",
    description="Выводит успех по Id, принадлежащий авторизованному пользователю",
)
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


@router.get(
    "/get_successes",
    summary="Вывести все успехи",
    description="Выводит все успехи, принадлежащие авторизованному пользователю",
)
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


@router.get(
    "/get_successes_pagination",
    summary="Вывести успехи c пагинацией",
    description="Выводит все успехи, принадлежащие авторизованному пользователю, с учетом пагинации",
)
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
        .order_by(desc(SuccessDB.creation_date))
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


@router.delete("/delete_successes/{note_id}", summary="Удалить успех по ИД")
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
@router.put(
    "/update_successes/{note_id}",
    response_model=UpdateSNote,
    summary="Изменение всех данных в заметке",
    description="Изменение всех данных в заметке. Все поля обязательны к заполнению",
)
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
    db_note.header = note.header
    db_note.description = note.description
    db_note.priority = note.priority
    db.commit()
    db.refresh(db_note)
    return {"status": "Updated", "data": db_note}


# изменение только тех полей, которые буду внесены (кроме ИД, разумеется)
@router.patch(
    "/success/patched_update/{id}",
    response_model=UpdateSNote,
    summary="Изменение части данных в заметке",
    description="Изменение части данных в заметке. В частности изменение всех доступных полей",
)
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
@router.get(
    "/successess/search/",
    summary="Поиск по заголовку",
    description="Поиск ключевой строки в названии заголовка и вывод записей",
)
async def filter_successes(
    search_query: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    notes = (
        db.query(SuccessDB)
        .filter(
            SuccessDB.header.icontains(search_query),
            current_user.id == SuccessDB.owner_id,
        )
        .all()
    )
    if not notes:
        return {
            "status": "OK",
            "message": f"По ключевому слову '{search_query}' не найдено записей.",
            "data": [],
        }
    else:
        return notes


@router.get("/by_category/{category_id}", summary="Вывод по заданной категории")
async def by_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    notes = (
        db.query(SuccessDB)
        .filter(
            SuccessDB.owner_id == current_user.id, SuccessDB.category_id == category_id
        )
        .all()
    )
    if not notes:
        raise HTTPException(status_code=404, detail="В этой категории нет записей")
    return notes
