from fastapi import APIRouter, Depends, HTTPException
import math
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from database import get_db
from models.models import SuccessDB, CategoryDB, UserDB
from auth.auth_utils import get_current_user
from schemas import SuccessNote, UpdateSNote, SuccessCreate,CategoryStat,CategoryOut, CategoryNote
router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/categories_list",response_model=list[CategoryOut], summary="Вывести все категории")
async def get_categories(db:Session = Depends(get_db)):
    cat = db.query(CategoryDB).all()
    return cat


@router.post("/categories", summary="Добавление категории")
async def add_category(nte:CategoryNote, db:Session = Depends(get_db)):
    category_name = nte.category_name.strip().capitalize()
    category = db.query(CategoryDB).filter(CategoryDB.category_name==category_name).first()
    if category:
        raise HTTPException(status_code=400, detail=f"Category {category.category_name} already exist")
    db_note = CategoryDB(category_name=category_name)
    
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

