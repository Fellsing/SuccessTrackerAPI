from fastapi import Query, HTTPException
from sqlalchemy.orm import Session

from models.models import CategoryDB, SuccessDB
from schemas.success import SuccessCreate, SuccessNote, UpdateSNote



def create_success_note(db:Session, note:SuccessCreate, user_id: int):
    category_name=note.category_name.strip().capitalize()
    category = db.query(CategoryDB).filter(category_name==CategoryDB.category_name).first()
    if not category:
        category = CategoryDB(category_name=category_name)
        db.add(category)
        db.commit()
        db.refresh(category)
    note_data = note.model_dump(exclude="category_name")
    new_success = SuccessDB(**note_data, category_id = category.id, owner_id = user_id)
    db.add(new_success)
    db.commit()
    db.refresh(new_success)
    return new_success


def delete_success(db:Session, success_id:int, user_id: int):
    db_note = db.query(SuccessDB).filter(SuccessDB.owner_id==user_id, SuccessDB.id==success_id).first()
    if not db_note:
        raise HTTPException(status_code=403, detail="Current user dont have this note")
    db.delete(db_note)
    db.commit()
    return {"status": "Deleted from DB", "id": db_note.id}



def update_success_note(db:Session, user_id:int, success_id:int, note_data:UpdateSNote):
    db_note = db.query(SuccessDB).filter(SuccessDB.id==success_id, user_id==SuccessDB.owner_id).first()
    if not db_note:
        raise HTTPException(status_code=403, detail="Current user dont have this note")
    new_data = note_data.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(db_note, key, value)
    db.commit()
    db.refresh(db_note)
    return db_note
