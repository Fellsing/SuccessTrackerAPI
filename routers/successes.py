import io
import os
from fastapi import APIRouter, Depends, HTTPException, Query
import math
from fastapi.responses import StreamingResponse
import pandas as pd
from pydantic import Field
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.crud import create_success_note, delete_success, update_success_note
from models.models import SuccessDB, CategoryDB, UserDB
from auth.auth_utils import get_current_user
from schemas import SuccessNote, UpdateSNote, SuccessCreate, CategoryStat
from schemas.success import SuccessRead

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

router = APIRouter(prefix="/successes", tags=["Successes"])


FONT_PATH = os.path.join(os.getcwd(), "fonts", "TIMES.TTF")
# Регистрация шрифта
try:
    pdfmetrics.registerFont(TTFont('TIMES', FONT_PATH))
except Exception as e:
    # Если шрифт не найден, логгируем ошибку, но не даем приложению упасть
    print(f"Font registration failed: {e}")



@router.post("/add_success", summary="Создать новый успех")
async def create_note(
    note: SuccessCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    return create_success_note(db, note, current_user.id)


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
        .outerjoin(
            SuccessDB,
            (SuccessDB.category_id == CategoryDB.id)
            & (SuccessDB.owner_id == current_user.id),
        )
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
    response_model=list[SuccessRead],
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
    page: int = Query(1, ge=1),
    lim: int = Query(3, ge=1, le=100),
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
        .options(joinedload(SuccessDB.category))
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
    return delete_success(db=db, user_id=current_user.id, success_id=note_id)


# изменение всех данных в заметке(кроме ИД, разумеется)
@router.put(
    "/update_successes/{note_id}",
    response_model=UpdateSNote,
    summary="Изменение всех данных в заметке",
    description="Изменение всех данных в заметке. Все поля обязательны к заполнению",
)
async def update_success(
    note_id: int,
    note: UpdateSNote,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    return update_success_note(db, current_user.id, note_id, note)


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


@router.get("/export/csv")
async def export_to_csv(db: Session = Depends(get_db), user=Depends(get_current_user)):
    successes = db.query(SuccessDB).filter(SuccessDB.owner_id == user.id).all()
    

    data = [
        {
            "Header": i.header,
            "Description":i.description,
            "Category": i.category.category_name,
            "Date": i.creation_date,
        }
        for i in successes
    ]
    df = pd.DataFrame(data)
    csv_str = df.to_csv(index=False, encoding='utf-8', sep=';')
    csv_bytes = csv_str.encode('utf-8')

    bom = b'\xef\xbb\xbf'
    final_content = bom + csv_bytes
    return StreamingResponse(
        io.BytesIO(final_content),
        media_type="text/csv",
        headers={"Content_Disposition": "attachment; filename=my_successes.csv"},
    )




@router.get("/export/pdf")
async def export_to_pdf(db: Session = Depends(get_db), user = Depends(get_current_user)):
    # 1. Получаем данные
    successes = db.query(SuccessDB).filter(SuccessDB.owner_id == user.id).all()
    
    # 2. Создаем байтовый буфер в памяти (io.BytesIO)
    buffer = io.BytesIO()
    
    # 3. Начинаем "рисовать" на холсте (Canvas) формата A4
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Устанавливаем шрифт для заголовка
    p.setFont("TIMES", 16)
    p.drawString(100, height - 50, f"Отчет об успехах пользователя: {user.username}")
    
    # Рисуем линию под заголовком
    p.line(100, height - 60, width - 100, height - 60)
    
    # Устанавливаем шрифт для основного текста
    p.setFont("TIMES", 12)
    y_position = height - 100
    
    for idx, item in enumerate(successes, 1):
        # Проверка на заполнение страницы
        if y_position < 100:
            p.showPage()  # Создаем новую страницу
            p.setFont("TIMES", 12)
            y_position = height - 50
            
        date_str = item.creation_date.strftime("%d.%m.%Y") if item.creation_date else "---"
        text = f"{idx}. [{date_str}] {item.header} — Категория: {item.category.category_name}"
        
        p.drawString(100, y_position, text)
        y_position -= 25 # Смещение вниз для следующей строки
        
    # 4. Завершаем PDF
    p.showPage()
    p.save()
    
    # 5. Возвращаем поток
    buffer.seek(0)
    return StreamingResponse(
        buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=success_report.pdf"}
    )
