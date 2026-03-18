from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from database import Base, engine


class CategoryDB(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, unique=True)

    notes = relationship("SuccessDB", back_populates="category")


class SuccessDB(Base):
    __tablename__ = "success_notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)
    category_id = Column(Integer, ForeignKey("categories.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))

    category = relationship("CategoryDB", back_populates="notes")
    owner = relationship("UserDB", back_populates="notes")

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    hashed_pass = Column(String)

    notes = relationship("SuccessDB", back_populates="owner")


# Команда для создания таблицы
def create_tables():
    Base.metadata.create_all(bind=engine)
