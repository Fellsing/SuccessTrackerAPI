import re
from pydantic import BaseModel, Field, field_validator


class SuccessNote(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int = Field(1, ge=1, le=10)
    category_id: int = Field(1, ge=1, le=99)

    class Config:
        from_attributes = (
            True  # Это позволит Pydantic легко дружить с объектами SQLAlchemy
        )


class CategoryNote(BaseModel):
    category_name: str = Field(min_length=2, max_length=50)

    class Config:
        from_attributes = True


class UserNote(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=30)

    @field_validator("password")
    @classmethod
    def validate_pass_strenght(cls, v:str) ->str:
        if not re.search(r"[A-Z]",v):
            raise ValueError("Нет заглавных букв")
        if not re.search(r"\d",v):
            raise ValueError("Нет цифр")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]",v):
            raise ValueError("Нет спец символов")
        return v



    class Config:
        from_attributes = True


class UpdateSNote(BaseModel):
    title: str | None = None
    description: str | None = Field(None, max_length=500)
    priority: int | None = Field(None, ge=1, le=10)
    category_id: int | None = Field(None, ge=1)
