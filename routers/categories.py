import json
from fastapi import APIRouter, Depends, HTTPException
import math
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from core.redis_config import get_redis
from database import get_db
from models.models import SuccessDB, CategoryDB, UserDB
from models.crud import get_category_by_name, create_category_note
from auth.auth_utils import get_current_user
from schemas import SuccessNote, UpdateSNote, SuccessCreate,CategoryStat,CategoryOut, CategoryNote
router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/categories_list",response_model=list[CategoryOut], summary="Вывести все категории")
async def get_categories(db:Session = Depends(get_db)):
    
    rd = get_redis()
    cache_key = "all_categories"
    cached_data = rd.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    cat = db.query(CategoryDB).all()
    res = [{"id":i.id, "category_name":i.category_name }for i in cat]
    rd.setex(cache_key, 300, json.dumps(res))
    return res


@router.post("/categories", summary="Добавление категории")
async def add_category(nte:CategoryNote, db:Session = Depends(get_db)):
    if get_category_by_name(db, nte.category_name):
        raise HTTPException(status_code=400, detail=f"Category {nte.category_name} already exist")
    return create_category_note(db, nte)

