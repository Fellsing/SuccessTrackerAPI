from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.category import CategoryNote


class SuccessNote(BaseModel):
    header: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int = Field(1, ge=1, le=10)
    category_id: int = Field(1, ge=1, le=99)

    @field_validator("header")
    @classmethod
    def header_validation(cls, header:str|None)->str|None:
        if header is None:
            return header
        header = header.strip().capitalize()
        if not re.match(r"^[a-zA-Zа-яА-Я0-9\s\.\,\-\:]+$", header):
            raise ValueError("Заголовок должен содержать только буквенные символы, пробелы, знаки препинания")
        return header
    model_config = ConfigDict(from_attributes=True)


class UpdateSNote(SuccessNote):
    header: str | None = Field(None,min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int | None = Field(None, ge=1, le=10)
    category_id: int | None = Field(None, ge=1)


class SuccessCreate(BaseModel):
    header: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int = Field(1, ge=1, le=10)
    category_name: str = Field(min_length=3, max_length=50)

    model_config = ConfigDict(from_attributes=True)



class SuccessRead(BaseModel):
    id: int
    owner_id: int
    creation_date: datetime
    header: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int = Field( ge=1, le=10)
    category: CategoryNote |None = None

    model_config = ConfigDict(from_attributes=True)