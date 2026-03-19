import re
from pydantic import BaseModel, Field, field_validator


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