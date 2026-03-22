from fastapi import APIRouter, Depends, HTTPException
import math
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from database import get_db
from models.models import SuccessDB, CategoryDB, UserDB
from auth.auth_utils import get_current_user
from schemas import SuccessNote, UpdateSNote, SuccessCreate,CategoryStat,CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/categories_list",response_model=list[CategoryOut])
async def get_categories(db:Session = Depends(get_db)):
    cat = db.query(CategoryDB).all()
    return cat