import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SuccessNote(BaseModel):
    header: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    priority: int = Field(1, ge=1, le=10)
    category_id: int = Field(1, ge=1, le=99)

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)
