import re
from pydantic import BaseModel, Field, field_validator


class SuccessNote(BaseModel):
    header: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int = Field(1, ge=1, le=10)
    category_id: int = Field(1, ge=1, le=99)

    class Config:
        from_attributes = (
            True  # Позволяет Pydantic легко дружить с объектами SQLAlchemy
        )


class UpdateSNote(BaseModel):
    header: str | None = None
    description: str | None = Field(None, max_length=500)
    priority: int | None = Field(None, ge=1, le=10)
    category_id: int | None = Field(None, ge=1)


class SuccessCreate(BaseModel):
    header: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int = Field(1, ge=1, le=10)
    category_name: str = Field(min_length=3, max_length=50)

    class Config:
        from_attributes = (
            True  # Позволяет Pydantic легко дружить с объектами SQLAlchemy
        )
