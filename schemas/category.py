import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

class CategoryNote(BaseModel):
    category_name: str = Field(min_length=2, max_length=50)

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