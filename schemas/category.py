import re
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

class CategoryNote(BaseModel):
    category_name: str = Field(min_length=2, max_length=50, description="Название категории, например 'Спорт' или 'Учеба'",
        examples=["Здоровье"])
    
    @field_validator("category_name")
    @classmethod
    def validate_name(cls, cname:str)->str:
        cname=cname.strip().capitalize()
        if not re.match(r"^[a-zA-Zа-яА-Я\s\-]+$", cname):
            raise ValueError("Название категории может состоять только из латинских или русских букв, символа пробела, символа дефиса")
        if cname.isdigit():
            raise ValueError("Название категории не может состоять только из цифр")
        return cname

    model_config = ConfigDict(from_attributes=True) # Новый стандарт V2



class CategoryStat(BaseModel):
    category: str
    count: int

    model_config = ConfigDict(from_attributes=True)

class CategoryOut(BaseModel):
    id: int
    category_name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)