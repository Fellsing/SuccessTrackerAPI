import re
from pydantic import BaseModel, Field, field_validator

class CategoryNote(BaseModel):
    category_name: str = Field(min_length=2, max_length=50)

    class Config:
        from_attributes = True
